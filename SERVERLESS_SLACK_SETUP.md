# Serverless Slack Integration — No Server Required

This guide sets up a slash command (`/search-training`) that runs Claude directly via API, no webhook server needed.

## Architecture

```
User types /search-training in Slack
        ↓
Slack Workflow Builder receives command
        ↓
Workflow calls Claude API with the query
        ↓
Claude runs the training search skill
        ↓
Results formatted and posted back to Slack
```

---

## Step 1: Get Your Bedrock API Token

You're using Salesforce Bedrock Gateway. Get your token:

1. Open PowerShell
2. Run this command:
   ```powershell
   set "AISUITE_DATA_DIR=C:\Users\dvoigtlander\.aisuite" && "C:\Users\dvoigtlander\.aisuite\bin\manager.exe" gateway-key
   ```
3. Copy the token it outputs (should start with something like `eyJ...`)
4. Save it for Step 5c below

**Base URL for Bedrock:**
```
https://eng-ai-model-gateway.sfproxy.devx-preprod.aws-esvc1-useast2.aws.sfdc.cl/bedrock
```

---

## Step 2: Create Slack App

1. Go to https://api.slack.com/apps
2. Sign in with your Slack workspace
3. Click **"Create New App"** → **"From scratch"**
4. Fill in:
   - **App Name**: `Training Search Bot`
   - **Workspace**: Your Salesforce workspace
5. Click **Create App**

---

## Step 3: Create Slash Command

In your app settings:

1. **Left sidebar** → **Slash Commands**
2. Click **"Create New Command"**
3. Fill in:
   - **Command**: `/search-training`
   - **Request URL**: (Leave blank for now — Workflow Builder handles it)
   - **Short Description**: `Search training across PlusPlus, Trailhead, O'Reilly, Pluralsight`
   - **Usage Hint**: `<topic>`
4. Click **Save**

---

## Step 4: Install App to Workspace

1. **Left sidebar** → **Install App**
2. Click **"Install to Workspace"**
3. Authorize the app

---

## Step 5: Create Slack Workflow

Now the magic: set up a workflow triggered by the slash command.

### 5a. Go to Workflow Builder

1. In Slack workspace, click your workspace name (top left)
2. Go to **Tools** → **Workflow Builder**
3. Click **"Create"**
4. Name it: `Training Search Workflow`
5. Click **Next**

### 5b: Set Trigger

1. Choose **"Slash command"**
2. Select `/search-training` command
3. Click **Done**

### 5c: Add Step 1 — Send to Claude API (Bedrock)

1. Click **"Add step"**
2. Search for **"Send a web request"** (or "Send data to apps")
3. Configure:
   - **Method**: `POST`
   - **URL**: `https://eng-ai-model-gateway.sfproxy.devx-preprod.aws-esvc1-useast2.aws.sfdc.cl/bedrock/messages`
   - **Headers** (click to add):
     - `Authorization`: `Bearer <YOUR_BEDROCK_TOKEN_FROM_STEP_1>`
     - `Content-Type`: `application/json`
   - **Request body** (JSON):

```json
{
  "model": "us.anthropic.claude-opus-5",
  "max_tokens": 2048,
  "system": "You are a training search assistant. Search for training and return results formatted for Slack. Return ONLY the formatted results, nothing else.",
  "messages": [
    {
      "role": "user",
      "content": "Search for training on: {{trigger.text}}\n\nReturn results in this format:\n\n🎓 Training Results for: {{trigger.text}}\n\nPluralsight:\n• [Name] → [URL]\n\nPlusPlus:\n• [Name] → [URL]\n\nO'Reilly:\n• [Name] → [URL]\n\nTrailhead:\n• [Name] → [URL]"
    }
  ]
}
```

4. Click **Done**

### 5d: Add Step 2 — Extract Response

1. Click **"Add step"**
2. Search for **"Set a variable"**
3. Configure:
   - **Variable name**: `training_results`
   - **Value**: Click to insert, select the **content** from the API response
     - Usually something like: `Send_a_web_request_response.content[0].text`
4. Click **Done**

### 5e: Add Step 3 — Post Results to Slack

1. Click **"Add step"**
2. Search for **"Send a message"**
3. Configure:
   - **Channel**: `{{ trigger.channel_id }}`
   - **Message**: `{{ training_results }}`
   - **Thread**: `{{ trigger.response_url }}` (replies in thread if used in thread)
4. Click **Done**

### 5f: Publish Workflow

1. Click **"Publish"** (top right)
2. Confirm: **"Publish workflow"**

---

## Step 6: Test It

In your Slack workspace:

```
/search-training machine learning
```

Expected result:
- Bot acknowledges command (may take 2-3 seconds)
- Formatted training results posted to channel

---

## Troubleshooting

### "Command not responding"
- Check that workflow is **Published**
- Verify API key is correct and has no extra spaces
- Check Slack logs: Workspace name → **Tools** → **Workflow Builder** → Click workflow → **View runs**

### "Invalid API key"
- Go back to Step 1 and re-copy your API key
- Make sure there are no extra spaces or newlines
- Verify you're using the right key (not expired)

### "Results not showing"
- Check the workflow **Run history** to see what API returned
- Verify the `{{ training_results }}` variable is extracting correctly
- May need to adjust the JSON path if Anthropic API response format differs

### Custom Model or Bedrock

If using Bedrock instead of standard Anthropic API:
- **URL**: Your `ANTHROPIC_BEDROCK_BASE_URL`
- **Headers**: Use your `ANTHROPIC_AUTH_TOKEN`
- **Model**: May differ (check Bedrock docs)

---

## Advanced: Add More Commands

Create more workflows for:
- `/search-courses` — PlusPlus only
- `/search-trailhead` — Trailhead only
- `/search-pluralsight` — Pluralsight only

Just duplicate the workflow and modify the prompt in Step 5c.

---

## How It Works Under the Hood

1. **Slack Workflow Builder** is Slack's no-code automation tool — runs in Slack's infrastructure
2. **Claude API call** is made directly from the workflow to Anthropic's servers
3. **Response** is extracted and posted back to Slack
4. **No server** — everything runs in Slack and Anthropic infrastructure

Cost: Only pay for Claude API calls (pennies per search).

---

## Next Steps

- ✅ Create the workflow (Step 5)
- ✅ Test in Slack (Step 6)
- Optional: Add scheduled reports or thread followers
- Optional: Add buttons for quick searches ("React", "Apex", "LWC", etc.)
