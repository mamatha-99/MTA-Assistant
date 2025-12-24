# 🚇 Green Line Chatbot - Quick Deployment

## FASTEST Way to Share (5 minutes!)

### Using Render (Free - No Credit Card Required)

**Step 1:** Make sure your server is working locally
```bash
# Test it first
python3 backend/api/main.py
# Visit http://localhost:8000 - should see "healthy!"
```

**Step 2:** Create GitHub Repository
1. Go to https://github.com/new
2. Create repository named `green-line-chatbot`
3. Run these commands:

```bash
cd "/Users/sj/Desktop/Capstone/Green Line"

git init
git add .
git commit -m "Initial commit - Green Line NYC Subway Chatbot"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/green-line-chatbot.git
git push -u origin main
```

**Step 3:** Deploy on Render
1. Go to https://render.com (Sign up with GitHub - FREE)
2. Click "New +" → "Web Service"
3. Connect your `green-line-chatbot` repository
4. Fill in:
   - **Name**: `green-line-chatbot` (or whatever you want)
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python3 backend/api/main.py`
   - **Plan**: Free

5. Click **Advanced** → Add Environment Variable:
   - **Key**: `OPENAI_API_KEY`
   - **Value**: `sk-...` (your OpenAI API key)

6. Click "Create Web Service"

**Step 4:** Wait ~5-10 minutes

Your app will be live at: `https://green-line-chatbot-XXXX.onrender.com`

**Step 5:** Update Frontend (Optional)
If you want to host the frontend too:
1. Edit `frontend/index.html`
2. Change line with `API_URL` to your Render URL
3. Upload to GitHub Pages or keep local

---

## Alternative: Quick Demo with LocalTunnel (Even Faster!)

If you just need a quick share RIGHT NOW:

```bash
# Install localtunnel
npm install -g localtunnel

# Start your server (in one terminal)
python3 backend/api/main.py

# In another terminal, expose it
lt --port 8000 --subdomain greenline

# You'll get: https://greenline.loca.lt
```

Share this URL with your teammates! They might need to click through a warning page first.

---

## Share These Test Queries with Teammates

Once deployed, tell your teammates to try:

1. **"How do I get from Grand Central to Wall Street?"**
   - Should show: Take 4/5 train Downtown, ~11 minutes

2. **"When is the next train at Union Square?"**
   - Shows real-time arrivals for 4, 5, 6 trains

3. **"Take me from Yankee Stadium to Brooklyn Bridge"**
   - Shows: 4 train Downtown, ~25 minutes

4. **"Are there any delays on the 6 train?"**
   - Shows current service alerts
   
5. **"How do I get to Times Square?"** (Should reject)
   - Response: "I currently provide navigation assistance for the 4, 5, and 6 trains..."

---

## Your Project is Ready! ✅

All files configured:
- ✅ requirements.txt
- ✅ Environment variables support
- ✅ CORS enabled
- ✅ Database included
- ✅ Green Line data loaded
- ✅ GPT-4o-mini for cost savings

Choose your deployment method and go! 🚀
