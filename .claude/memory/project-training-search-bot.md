---
name: training-search-bot
description: Slack-based training content search agent across 4 platforms
metadata:
  type: project
---

## Status
Skill created and ready. Needs Slack invocation integration.

## What It Does
Monitors Slack DMs for training questions, searches across 4 platforms, returns bulleted results with enrollment links.

## Platforms Searched
- **Pluralsight** — skill learning paths, courses
- **PlusPlus** — Salesforce internal training (API: http://localhost:8000/api/search)
- **O'Reilly** — technical learning library (MCP: `mcp__oreilly__search_oreilly_content`)
- **Trailhead** — Salesforce certifications and modules (MCP: `trailhead.content_search`)

## Files & Locations
- **Skill:** `~/.claude/skills/slack-training-search/SKILL.md` and `agent.js`
- **Project folder:** `C:\Users\dvoigtlander\claude\Headless_Training`
- **Config:** Slack bot token (xoxb-...) required; documented in `SLACK_SETUP.md`

## Current Flow
`/slack-training-search` in Claude Code → polls DMs → searches 4 platforms in parallel → posts formatted results back to DM thread

## Next Steps: Choose Slack Invocation Method
1. **Slash command** — register `/training-search query` in Slack app settings
2. **Auto-trigger** — bot auto-runs when DM contains training keywords (search, course, learn, certification, skill, module)
3. **Webhook** — host simple endpoint that Slack calls to trigger agent

**Recommendation:** Slash command is easiest to set up and control.

## Created
2026-08-31
