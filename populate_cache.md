# Populate MCP Cache

To populate `mcp_cache.json` with real enrollment data from your 4 platforms, you need to call the MCP tools from Claude Code.

## Connected MCP Servers

- ✔ PlusPlus - `plusplus`
- ✔ Trailhead - `trailhead`
- ✔ O'Reilly - `oreilly`
- ! Pluralsight - needs authentication

## Tool Names to Call

Based on your platform configurations, try these tool names:

### PlusPlus
- `get_adoption_metrics()` - org-wide adoption metrics (confirmed working)

### Trailhead  
- Try: `get_enrollment_analytics()` or `get_learner_metrics()`

### O'Reilly
- Try: `get_enrollment_analytics()` or `get_learner_metrics()`

### Pluralsight
- Needs OAuth authentication first
- Try: `get_enrollment_analytics()` or `get_learner_metrics()`

## How to Populate Cache

1. Ask Claude Code to call each tool and fetch the results
2. The results will be cached to `mcp_cache.json`
3. FastAPI will read from this cache

Example prompt to Claude Code:
```
Call the MCP tools to fetch real enrollment data:
- plusplus: get_adoption_metrics(time_period='30d')
- trailhead: get_enrollment_analytics()
- oreilly: get_enrollment_analytics()

Save the results to mcp_cache.json in the Headless_Training directory.
Format: {timestamp: ISO string, platforms: {plusplus: {...}, trailhead: {...}, oreilly: {...}}}
```
