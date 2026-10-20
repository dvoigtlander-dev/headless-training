---
name: slack-training-bot
description: Slack polling bot for comprehensive training search across 4 platforms
metadata:
  type: project
---

## Goal
Create a Slack bot that listens for training questions and searches across 4 training platforms, then posts results back to Slack.

## Platforms Integrated
- Pluralsight (via plusplus-skill)
- PlusPlus (via plusplus-skill)
- O'Reilly (via mcp__oreilly__search_oreilly_content)
- Salesforce Trailhead (via trailhead MCP)

## Approach (Decided)
**Polling-based bot** — much simpler than webhooks/event subscriptions.

How it works:
1. Bot polls the Slack channel every N seconds for new messages
2. When a message is detected, extracts the question
3. Searches all 4 platforms in parallel
4. Posts formatted results back to the channel

**Why this approach:** Simpler setup, no webhook URL needed, no always-on server required (can run locally or as a cron job)

## Slack App Setup Steps

1. Go to https://api.slack.com/apps
2. Click "Create New App" → **"Blank app"**
3. Name: `Training Search Bot`
4. Select workspace
5. Left sidebar → **OAuth & Permissions**
   - Add bot scopes: `chat:write`, `channels:read`, `users:read`
6. **Install to Workspace** → Authorize
7. Copy **Bot User OAuth Token** (xoxb-...)
8. Get **Channel ID** (right-click channel in Slack → Copy channel ID)

## Implementation Plan
- Build Python bot script (runs locally or scheduled)
- Stores last-seen message timestamp to avoid duplicates
- Calls all 4 training platforms
- Formats results as Slack blocks/threads
- Posts back to channel

## Next Steps
1. Complete Slack app setup (get bot token + channel ID)
2. Build Python bot script
3. Test with sample queries
4. Deploy (local loop or cron/scheduled task)

## Related Skills
- `plusplus-skill` — Query PlusPlus catalog
- `trailhead` MCP — Salesforce Trailhead content
- `mcp__oreilly__search_oreilly_content` — O'Reilly search
- Pluralsight skill available in the system
