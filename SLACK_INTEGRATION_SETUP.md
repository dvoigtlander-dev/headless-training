# Slack Integration Setup — Step by Step

## Prerequisites
- Python 3.8+
- Slack workspace admin access
- PlusPlus API key
- For local testing: ngrok (https://ngrok.com)

## Step 1: Create Slack App

1. Go to https://api.slack.com/apps
2. Click **"Create New App"** → **"From scratch"**
3. Fill in:
   - **App name**: `PlusPlus Training Bot`
   - **Workspace**: Select your Salesforce workspace
4. Click **Create App**

## Step 2: Configure Slash Commands

In your app settings, go to **Slash Commands** (left sidebar):

1. Click **Create New Command**
2. Fill in:
   - **Command**: `/training-search`
   - **Request URL**: `http://localhost:8000/slack/slash` (for local testing, use ngrok URL)
   - **Short Description**: Search training across PlusPlus, Trailhead, O'Reilly, Pluralsight
   - **Usage hint**: `<topic>`
3. Click **Save**

Repeat for `/plusplus` command (legacy):
- Same setup but usage hint is: `courses | events | search <query>`

## Step 3: Get Signing Secret

1. Go to **Basic Information** (left sidebar)
2. Scroll to **App Credentials**
3. Copy **Signing Secret**
4. Save this — you'll need it to start the server

## Step 4: Add Bot Permissions

Go to **OAuth & Permissions** (left sidebar):

1. Under **Scopes** → **Bot Token Scopes**, add:
   - `commands` — Register slash commands
   - `chat:write` — Post messages to channels
   - `chat:write.public` — Post to public channels

2. Click **Install to Workspace** (if not already installed)
3. Authorize the app

## Step 5: Local Testing (ngrok)

If running on `localhost`, expose to Slack with ngrok:

```bash
ngrok http 8000
```

This gives you a public URL like `https://abc-123-def.ngrok.io`. Use this for the Request URL in Step 2.

## Step 6: Start the Server

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export PLUSPLUS_API_KEY="your-api-key-here"
export SLACK_SIGNING_SECRET="your-signing-secret-from-step-3"

# Start server
python main.py
```

Server runs on `http://localhost:8000`

## Step 7: Test in Slack

In your Slack workspace, try:

```
/training-search machine learning
/training-search salesforce
/plusplus courses
/plusplus search mulesoft
```

## Troubleshooting

**"The slash command didn't work"**
- Verify ngrok is running and the URL matches your Request URL
- Check server logs for errors
- Ensure `SLACK_SIGNING_SECRET` is set correctly

**"Unauthorized" error**
- Double-check signing secret matches exactly (copy from Slack app settings)
- Check that ngrok/server is running at the URL you configured

**"url_verification failed"**
- Make sure Request URL is accessible and server is running
- Slash commands expect a response within 3 seconds; server must be responsive

**Environment variables not loading**
- Verify they're exported: `echo $PLUSPLUS_API_KEY`
- On Windows, use `set` instead of `export`: `set PLUSPLUS_API_KEY=...`

## Production Deployment

When deploying (AWS, Cloud Run, etc.):

1. Update Request URL to your production domain
2. Set environment variables in your deployment config:
   - `PLUSPLUS_API_KEY`
   - `SLACK_SIGNING_SECRET`
3. Use HTTPS for all URLs (Slack requires it)

## Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/slack/slash` | POST | Slash command handler |
| `/slack/events` | POST | Event verification (for future use) |
| `/api/courses` | GET | Get all courses |
| `/api/events` | GET | Get all events |
| `/api/search` | GET | Search PlusPlus catalog |
| `/api/unified-search` | GET | Search all platforms |
| `/health` | GET | Health check |
| `/docs` | GET | Interactive API docs (Swagger) |
