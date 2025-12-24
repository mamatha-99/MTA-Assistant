# 🚇 Deploy NYC Subway Assistant on Streamlit Cloud

This guide will help you deploy the NYC Subway Assistant chatbot on Streamlit Cloud.

## Prerequisites

1. A GitHub account
2. A Streamlit Cloud account (free at [streamlit.io/cloud](https://streamlit.io/cloud))
3. Your Google AI Studio API key

## Step-by-Step Deployment

### 1. Push Your Code to GitHub

If you haven't already, push your code to a GitHub repository:

```bash
git init
git add .
git commit -m "Initial commit - NYC Subway Assistant"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
git push -u origin main
```

### 2. Create Streamlit Cloud Account

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Sign in with your GitHub account
3. Authorize Streamlit Cloud to access your repositories

### 3. Deploy Your App

1. Click **"New app"** button
2. Select your repository
3. Set the following:
   - **Main file path**: `app.py`
   - **Python version**: 3.9 or higher
4. Click **"Advanced settings"** and add environment variable:
   - **Key**: `GOOGLE_AI_API_KEY`
   - **Value**: `Your API Key`
5. Click **"Deploy"**

### 4. Wait for Deployment

Streamlit Cloud will:
- Install dependencies from `requirements.txt`
- Start your app
- Provide you with a public URL (e.g., `https://your-app-name.streamlit.app`)

## Environment Variables

The app uses the following environment variable:
- `GOOGLE_AI_API_KEY`: Your Google AI Studio API key

You can set this in Streamlit Cloud's app settings under "Secrets" or as an environment variable.

## Local Testing

Before deploying, test locally:

```bash
# Install dependencies
pip install -r requirements.txt

# Set API key (optional if hardcoded)
export GOOGLE_AI_API_KEY="Your API Key"

# Run Streamlit app
streamlit run app.py
```

The app will be available at `http://localhost:8501`

## Troubleshooting

### App fails to start
- Check that `app.py` is in the root directory
- Verify all dependencies are in `requirements.txt`
- Check Streamlit Cloud logs for error messages

### API errors
- Verify your Google AI API key is correct
- Check that the API key has proper permissions
- Ensure the API key is set as an environment variable

### Import errors
- Make sure all backend modules are accessible
- Check that `backend/` directory structure is correct
- Verify all Python dependencies are listed in `requirements.txt`

## Features

The Streamlit app includes:
- ✅ Chat interface with message history
- ✅ Integration with Gemini API
- ✅ Function calling for subway routing
- ✅ Real-time train information
- ✅ Service alerts
- ✅ MTA-themed UI

## Support

For issues or questions:
- Check Streamlit Cloud logs
- Review the [Streamlit documentation](https://docs.streamlit.io)
- Check GitHub issues

---

**Happy Deploying! 🚇**

