# PlusPlus Slack Integration Setup

## Quick Start

### 1. Create Slack App

Go to https://api.slack.com/apps and click **"Create New App"** → **"From scratch"**

- App name: `PlusPlus`
- Workspace: select your Salesforce workspace
- Click **Create App**

### 2. Configure Slash Command

In your app settings:

1. Go to **Slash Commands** → **Create New Command**
2. Fill in:
   - **Command**: `/plusplus`
   - **Request URL**: `http://your-ip:8000/slack/slash` (or `https://your-domain.com/slack/slash` if deployed)
   - **Short Description**: Query PlusPlus training catalog
   - **Usage hint**: `courses | events | search <query>`

3. Click **Save**

### 3. Get Signing Secret

1. Go to **Basic Information**
2. Copy **Signing Secret**
3. Set as environment variable:
   ```bash
   export SLACK_SIGNING_SECRET="your-signing-secret-here"
   ```

### 4. Install App to Workspace

1. Go to **Install App** (left sidebar)
2. Click **Install to Workspace**
3. Authorize the app

### 5. Start Server

```bash
export PLUSPLUS_API_KEY="da207d190c238839ccb554a8b484fc00a3a74752c17c675926de38c07d636fa1"
export SLACK_SIGNING_SECRET="your-signing-secret"
python main.py
```

## Usage

In any Slack channel:

```
/plusplus courses          # List all courses
/plusplus events           # List all events
/plusplus search mulesoft  # Search for MuleSoft trainings
```

## Deployment Notes

### Local Testing (ngrok)

If running locally, use ngrok to expose your server:

```bash
ngrok http 8000
```

Then set Request URL to: `https://your-ngrok-url.ngrok.io/slack/slash`

### Production Deployment

Update Request URL to your production domain (AWS, Cloud Run, etc.)

## Troubleshooting

**"url_verification" failed?**
- Make sure server is running and accessible at the Request URL
- Check firewall/routing rules

**Slash command not responding?**
- Verify signing secret is set correctly
- Check server logs for errors
- Ensure Slack app has permission to post to channel

**Getting 401 Unauthorized?**
- Verify request timestamp (requests older than 5 min are rejected)
- Double-check signing secret matches Slack app

## Permissions

Your app automatically has these scopes:
- `commands` - Register slash commands
- `chat:write` - Post messages

No additional permissions needed.
