from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import sys
import google.generativeai as genai
import json

from dotenv import load_dotenv

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from backend.llm.tools import tool_plan_trip, tool_get_next_trains, tool_get_alerts

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure Gemini API
api_key = os.getenv("GOOGLE_AI_API_KEY", "AIzaSyBdEBYQQc0vvnqLoVSH-ZJ1dlIri5-Ei9M")
genai.configure(api_key=api_key)


# In-memory history for prototype simplicity
# In production, use Redis or Postgres
history_db = {} 

class ChatRequest(BaseModel):
    message: str
    session_id: str = "default" # New field

@app.post("/chat")
def chat_endpoint(req: ChatRequest):
    user_text = req.message
    
    # Retrieve History
    history = history_db.get(req.session_id, [])
    
    # Add User Message to History
    history.append({"role": "user", "content": user_text})
    
    # Enhanced System Prompt with better context management
    system_prompt = """You are the NYC Subway Assistant, specialized in the Lexington Avenue Line (Green Line).
    You have access to real-time subway data through specialized tools.
    
    ═══════════════════════════════════════════════════════════════
    ⚠️  CRITICAL: ALWAYS USE TOOLS - DO NOT GUESS ⚠️
    ═══════════════════════════════════════════════════════════════
    
    **MANDATORY RULE: When a user asks about routing, trains, or stations, you MUST call the appropriate tool.**
    
    - If user asks "How do I get from X to Y?" → ALWAYS call plan_trip(X, Y)
    - If user asks "When is the next train at X?" → ALWAYS call get_next_trains(X)  
    - If user asks about delays/alerts → ALWAYS call get_alerts()
    
    DO NOT make assumptions about whether a station is on the Green Line.
    DO NOT say "X is not on the Green Line" without calling plan_trip first.
    LET THE TOOL DECIDE - if the station is not found, the tool will return an error message.
    
    ═══════════════════════════════════════════════════════════════
    🚇 SERVICE SCOPE - IMPORTANT 🚇
    ═══════════════════════════════════════════════════════════════
    
    **YOU ONLY PROVIDE SERVICE FOR THE 4, 5, AND 6 TRAINS (LEXINGTON AVENUE LINE - GREEN LINE).**
    
    If a user asks about ANY other subway line or station not served by the 4, 5, or 6 trains:
    - Politely inform them: "I currently provide navigation assistance for the 4, 5, and 6 trains (Lexington Avenue Line - Green Line) only. We're working on expanding to cover the entire NYC subway system soon! Is there anything I can help you with regarding the 4, 5, or 6 trains?"
    - Do NOT attempt to plan trips or provide information for other lines.
    - Do NOT hallucinate or guess information about lines you don't support.
    
    Green Line Stations Include (but not limited to):
    - Manhattan: Grand Central-42 St, Union Square, Brooklyn Bridge-City Hall, Fulton St, Wall St, etc.
    - Bronx: Yankee Stadium, various stops along the Lexington Avenue corridor
    - Brooklyn: Atlantic Av-Barclays Ctr, Crown Heights-Utica Av, New Lots Av, Flatbush Av-Brooklyn College
    
    ═══════════════════════════════════════════════════════════════
    CRITICAL CONTEXT MANAGEMENT RULES:
    ═══════════════════════════════════════════════════════════════
    
    1. **REMEMBER THE CONVERSATION**: If the user previously mentioned a location and now provides 
       additional details, COMBINE them. Don't ask the same question twice.
    
    2. **RECOGNIZE FOLLOW-UP RESPONSES**: When a user says things like:
       - "The one on Lexington" or "Lexington Avenue"
       - "The main one" or "42nd Street one"  
       - "Number 1" or "Option A"
       They are answering your PREVIOUS disambiguation question.
    
    3. **CHAIN INFORMATION ACROSS TURNS**: If user says:
       Turn 1: "I'm at Grand Central"
       Turn 2: "I want to go to Brooklyn"
       Turn 3: "Atlantic Avenue"
       → You should understand: origin=Grand Central, destination=Atlantic Avenue
    
    4. **USE COMMON SENSE DEFAULTS**: For very popular Green Line stations, assume the main complex:
       - "Grand Central" → Grand Central-42 St (main complex)
       - "Union Square" → 14 St-Union Sq
       - "Brooklyn Bridge" → Brooklyn Bridge-City Hall
       Only ask for clarification if the station name is truly ambiguous (like "86th St" 
       which exists on multiple lines).
    
    5. **DON'T OVER-CLARIFY**: If a tool successfully returns data without ambiguity, 
       don't second-guess it. Present the information to the user.
    
    ═══════════════════════════════════════════════════════════════
    FUNCTION CAPABILITIES:
    ═══════════════════════════════════════════════════════════════
    
    - **plan_trip(origin, dest)**: Plan a route between two GREEN LINE stations
      - Call this when user asks "How do I get from X to Y?" (if both are on Green Line)
      - If tool returns "Ambiguous" error, it will list options - ask user to choose
      - Will only work for stations served by the 4, 5, or 6 trains
      
    - **get_next_trains(station)**: Get upcoming train arrivals at a GREEN LINE station
      - Call this when user asks "When is the next train at X?" (if X is on Green Line)
      - Only returns 4, 5, and 6 train arrivals
      
    - **get_alerts()**: Get current service alerts for the 4, 5, and 6 trains
      - Call this when user asks about delays, service changes, alerts
      - Only returns alerts relevant to Green Line routes
    
    ═══════════════════════════════════════════════════════════════
    CONVERSATION PATTERNS TO HANDLE:
    ═══════════════════════════════════════════════════════════════
    
    Pattern 1 - Out of Scope Query:
      User: "How do I get to Times Square?"
      You: "I currently provide navigation assistance for the 4, 5, and 6 trains (Lexington Avenue Line - Green Line) only. Times Square is served by other lines. We're working on expanding to cover the entire NYC subway system soon! Is there anything I can help you with regarding the 4, 5, or 6 trains?"
    
    Pattern 2 - In Scope Query:
      User: "How do I get from Grand Central to Wall Street?"
      You: [Call plan_trip("Grand Central", "Wall Street")]
    
    Pattern 3 - Progressive clarification:
      User: "How do I get from 86th St to Union Square?"
      Tool: Returns "Ambiguous origin '86th St'. Options: 86th St (Lexington - 4/5/6), 86th St (Broadway - 1)..."
      You: "I found multiple 86th St stations. Did you mean 86th St on Lexington Ave (4/5/6) or 86th St on Broadway (1)? Note: I can only help with the Lexington Ave station (4/5/6 trains)."
      User: "Lexington"
      You: [Call plan_trip("86th St Lexington", "Union Square")]
    
    ═══════════════════════════════════════════════════════════════
    IMPORTANT REMINDERS:
    ═══════════════════════════════════════════════════════════════
    
    - Always assume current time ("now") unless user specifies otherwise
    - When tools return ambiguity errors, extract the options and present them clearly
    - Be conversational and helpful, not robotic
    - If you're unsure about the user's intent, ask a specific question
    - After providing a route, offer to help with anything else (within Green Line scope)
    - NEVER provide information about lines other than 4, 5, and 6
    
    ═══════════════════════════════════════════════════════════════
    NYC SUBWAY TERMINOLOGY - USE AUTHENTIC LANGUAGE:
    ═══════════════════════════════════════════════════════════════
    
    - Say "4 train", "5 train", "6 train" NOT "route 4", "line 5", "4 line"
    - The tools will provide proper NYC directions (Uptown/Downtown, to Brooklyn/Bronx)
    - When presenting routes, use the exact direction terminology from the tools
    
    Examples of CORRECT phrasing:
    ✓ "Take the 6 train Uptown"
    ✓ "Board the 4 train Downtown to Brooklyn"
    ✓ "The 5 train heading Uptown to the Bronx"
    
    Examples of INCORRECT phrasing:
    ✗ "Take route 6 Northbound"
    ✗ "Board the 4 line Southbound"
    ✗ "The 5 train line heading North"
    
    ═══════════════════════════════════════════════════════════════
    CRITICAL: PRESERVE TOOL OUTPUT FORMATTING
    ═══════════════════════════════════════════════════════════════
    
    When presenting route information from plan_trip:
    - Present the STEPS section with minimal rephrasing
    - Keep terminal destinations (e.g., "Downtown to Brooklyn Bridge-City Hall")
    - Keep "6 express" formatting (already formatted by tools)
    - Preserve alert formatting and details
    - You may add friendly context but don't remove technical details
    """
    
    # Define tools for Gemini using FunctionDeclaration format
    plan_trip_func = genai.protos.FunctionDeclaration(
        name="plan_trip",
        description="Plan a route between two stations",
        parameters=genai.protos.Schema(
            type=genai.protos.Type.OBJECT,
            properties={
                "origin": genai.protos.Schema(type=genai.protos.Type.STRING, description="Origin station name"),
                "dest": genai.protos.Schema(type=genai.protos.Type.STRING, description="Destination station name")
            },
            required=["origin", "dest"]
        )
    )
    
    get_next_trains_func = genai.protos.FunctionDeclaration(
        name="get_next_trains",
        description="Get next train arrival times",
        parameters=genai.protos.Schema(
            type=genai.protos.Type.OBJECT,
            properties={
                "station": genai.protos.Schema(type=genai.protos.Type.STRING, description="Station name or ID")
            },
            required=["station"]
        )
    )
    
    get_alerts_func = genai.protos.FunctionDeclaration(
        name="get_alerts",
        description="Get current service alerts",
        parameters=genai.protos.Schema(type=genai.protos.Type.OBJECT)
    )
    
    # Create tool with function declarations
    tools = genai.protos.Tool(
        function_declarations=[plan_trip_func, get_next_trains_func, get_alerts_func]
    )
    
    # Initialize Gemini model with tools and system instruction
    model = genai.GenerativeModel(
        model_name="gemini-2.5-flash",
        system_instruction=system_prompt,
        tools=[tools]
    )
    
    # Convert history to Gemini format
    gemini_history = []
    for msg in history:
        if msg["role"] == "system":
            continue  # Skip, handled by system_instruction
        elif msg["role"] == "user":
            gemini_history.append({"role": "user", "parts": [msg["content"]]})
        elif msg["role"] == "assistant":
            # Check if it's a function call or regular response
            if "function_call" in str(msg.get("content", "")):
                # This was a function call, skip it as we'll handle it differently
                continue
            gemini_history.append({"role": "model", "parts": [msg["content"]]})
        elif msg["role"] == "tool":
            # Convert tool response to function response format
            gemini_history.append({
                "role": "function",
                "parts": [genai.protos.Part(
                    function_response=genai.protos.FunctionResponse(
                        name=msg.get("name", ""),
                        response={"result": msg["content"]}
                    )
                )]
            })
    
    # Start chat with history
    chat = model.start_chat(history=gemini_history if gemini_history else None)
    
    # Send user message
    response = chat.send_message(user_text)
    
    # Check if function call was made
    function_calls = []
    text_response = None
    
    for part in response.candidates[0].content.parts:
        if hasattr(part, 'function_call') and part.function_call:
            function_calls.append(part.function_call)
        elif hasattr(part, 'text') and part.text:
            text_response = part.text
    
    if function_calls:
        # Function call detected - execute all function calls
        function_responses = []
        
        for function_call in function_calls:
            fn_name = function_call.name
            args = {}
            for key, value in function_call.args.items():
                args[key] = value
            
            # Execute tool
            result_text = ""
            if fn_name == "plan_trip":
                result_text = tool_plan_trip(args.get("origin", ""), args.get("dest", ""))
            elif fn_name == "get_next_trains":
                result_text = tool_get_next_trains(args.get("station", ""))
            elif fn_name == "get_alerts":
                result_text = tool_get_alerts()
            
            # Create function response
            function_responses.append(
                genai.protos.Part(
                    function_response=genai.protos.FunctionResponse(
                        name=fn_name,
                        response={"result": result_text}
                    )
                )
            )
            
            # Add to history
            history.append({
                "role": "tool",
                "name": fn_name,
                "content": result_text
            })
        
        # Send function responses back to model
        final_response = chat.send_message(function_responses)
        final_resp = final_response.text
        
        # Append to history
        history.append({"role": "assistant", "content": final_resp})
        history_db[req.session_id] = history
        
        return {"response": final_resp}
    else:
        # Regular chat response
        resp_text = text_response if text_response else response.text
        history.append({"role": "assistant", "content": resp_text})
        history_db[req.session_id] = history
        return {"response": resp_text}

if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
