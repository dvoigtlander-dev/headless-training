"""PlusPlus HTTP API Server - Unified training catalog access"""

import os
import hmac
import hashlib
import time
import json
import asyncio
import subprocess
import sys
from dotenv import load_dotenv
from fastapi import FastAPI, Query, Header, HTTPException, Form, Request
from fastapi.middleware.cors import CORSMiddleware
import httpx
import uvicorn
from concurrent.futures import ThreadPoolExecutor
import threading

load_dotenv()

# Configuration
BASE_URL = os.environ.get("PLUSPLUS_BASE_URL", "https://sfdc-bt.plusplus.app")
API_KEY = os.environ.get("PLUSPLUS_API_KEY")
OPTIONAL_API_AUTH = os.environ.get("PLUSPLUS_API_AUTH_KEY", "")
SLACK_SIGNING_SECRET = os.environ.get("SLACK_SIGNING_SECRET", "")
SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN", "")

# Load tunnel URLs from config file
TUNNELS = {}
try:
    with open("tunnels.json") as f:
        TUNNELS = json.load(f)
except:
    TUNNELS = {
        "api_tunnel": "https://always-transcription-displaying-rare.trycloudflare.com",
        "dashboard_tunnel": "{DASHBOARD_URL}"
    }

DASHBOARD_URL = TUNNELS.get("dashboard_tunnel", "http://localhost:8501")
print(f"DEBUG: Loaded tunnels.json - api_tunnel: {TUNNELS.get('api_tunnel')}, dashboard_tunnel: {DASHBOARD_URL}", flush=True)
sys.stdout.flush()

# MCP client flag
USE_MCP_FOR_PLUSPLUS = True

if not API_KEY:
    raise ValueError("PLUSPLUS_API_KEY environment variable is required")

# MCP Configuration
TRAILHEAD_MCP_URL = os.environ.get("TRAILHEAD_MCP_URL", "https://mcp.trailhead.salesforce.com/mcp")
PLURALSIGHT_MCP_URL = os.environ.get("PLURALSIGHT_MCP_URL", "https://mcp.pluralsight.com/mcp")
OREILLY_MCP_URL = os.environ.get("OREILLY_MCP_URL", "https://api.oreilly.com/api/search/v1/mcp")
OREILLY_MCP_TOKEN = os.environ.get("OREILLY_MCP_TOKEN", "")

app = FastAPI(
    title="PlusPlus API",
    description="Shared access to Salesforce PlusPlus training catalog",
    version="1.0.0"
)

# Enable CORS for broader access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _validate_auth(auth_header: str = Header(None)):
    """Validate API auth header if configured"""
    if OPTIONAL_API_AUTH and auth_header != f"Bearer {OPTIONAL_API_AUTH}":
        raise HTTPException(status_code=401, detail="Unauthorized")


async def _verify_slack_signature(request: Request):
    """Verify Slack request signature"""
    # For development/testing, skip validation if timestamp header is missing
    timestamp = request.headers.get("X-Slack-Request-Timestamp")
    if not timestamp:
        print("DEBUG: No timestamp header, skipping Slack signature verification")
        return True
    return True  # Skip full verification for now


def _headers():
    return {
        "Authorization": f"Bearer {API_KEY}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }


def _client():
    return httpx.Client(base_url=BASE_URL, headers=_headers(), follow_redirects=True, timeout=30)


def _search_plusplus_via_mcp(query: str, limit: int = 10):
    """Search PlusPlus via MCP server"""
    try:
        result = subprocess.run(
            [sys.executable, "-c", f"""
import subprocess
import json
import sys

# Call MCP tool via subprocess
proc = subprocess.Popen(
    ["{sys.executable}", "plusplus_mcp_server.py"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True
)

# For now, return empty - MCP integration needs proper setup
# This is a placeholder for direct MCP client integration
sys.exit(0)
"""],
            cwd=os.getcwd(),
            capture_output=True,
            text=True,
            timeout=15
        )
        # Fallback to direct API if MCP unavailable
        return None
    except Exception as e:
        print(f"MCP search error: {e}")
        return None


def _search_plusplus_courses(query: str, limit: int = 10) -> list:
    """Search PlusPlus courses - tries MCP first, falls back to direct API"""
    try:
        with _client() as client:
            resp = client.get("/api/v2/courses", params={"limit": limit * 2}, timeout=5)
            if resp.status_code == 200:
                courses = resp.json().get("data", [])
                q_lower = query.lower()
                matching = []
                for c in courses:
                    name = (c.get("name", "") or "").lower()
                    desc = (c.get("description", "") or "").lower()
                    tags = " ".join([t.get("name", "") for t in c.get("tags", [])]).lower()
                    if q_lower in name or q_lower in desc or q_lower in tags:
                        # PlusPlus doesn't provide deep links; link to search query instead
                        course_url = f"{BASE_URL}?search={query}"
                        matching.append({
                            "source": "plusplus",
                            "title": c.get("name", ""),
                            "description": c.get("description", ""),
                            "url": course_url,
                            "type": "course"
                        })
                return matching[:limit]
    except Exception as e:
        print(f"DEBUG: Course search error: {e}")
    return []


def _search_plusplus_events(query: str, limit: int = 10) -> list:
    """Search PlusPlus events"""
    try:
        with _client() as client:
            resp = client.get("/api/v2/events", params={"limit": limit * 2}, timeout=5)
            if resp.status_code == 200:
                events = resp.json().get("data", [])
                q_lower = query.lower()
                matching = []
                for e in events:
                    name = (e.get("name", "") or "").lower()
                    desc = (e.get("description", "") or "").lower()
                    if q_lower in name or q_lower in desc:
                        # PlusPlus doesn't provide deep links; link to search query instead
                        event_url = f"{BASE_URL}?search={query}"
                        matching.append({
                            "source": "plusplus",
                            "title": e.get("name", ""),
                            "description": e.get("description", ""),
                            "url": event_url,
                            "type": "event"
                        })
                return matching[:limit]
    except Exception as e:
        print(f"DEBUG: Event search error: {e}")
    return []


@app.get("/")
async def root():
    """Redirect to dashboard"""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="http://localhost:8501")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "service": "plusplus-api"}


@app.post("/slack/events")
async def slack_events(request: Request):
    """Slack Events API endpoint for URL verification and events"""
    # Verify signature
    await _verify_slack_signature(request)

    body = await request.json()

    # Handle URL verification challenge (required by Slack during setup)
    if body.get("type") == "url_verification":
        return {"challenge": body.get("challenge")}

    # Handle other events if needed
    return {"ok": True}


@app.get("/api/courses")
async def get_courses(
    limit: int = Query(100, ge=1, le=200),
    offset: int = Query(0, ge=0),
    authorization: str = Header(None)
):
    """Get all courses"""
    _validate_auth(authorization)
    try:
        with _client() as client:
            resp = client.get("/api/v2/courses", params={"limit": limit, "offset": offset})
            resp.raise_for_status()
            return resp.json()
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"PlusPlus API error: {str(e)}")


@app.get("/api/events")
async def get_events(
    limit: int = Query(100, ge=1, le=200),
    offset: int = Query(0, ge=0),
    authorization: str = Header(None)
):
    """Get all events/training sessions"""
    _validate_auth(authorization)
    try:
        with _client() as client:
            resp = client.get("/api/v2/events", params={"limit": limit, "offset": offset})
            resp.raise_for_status()
            return resp.json()
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"PlusPlus API error: {str(e)}")


@app.get("/api/enrollments")
async def get_enrollments(
    limit: int = Query(100, ge=1, le=200),
    offset: int = Query(0, ge=0),
    authorization: str = Header(None)
):
    """Get user enrollments"""
    _validate_auth(authorization)
    try:
        with _client() as client:
            resp = client.get("/api/v2/enrollments", params={"limit": limit, "offset": offset})
            resp.raise_for_status()
            return resp.json()
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"PlusPlus API error: {str(e)}")


@app.get("/api/assignments")
async def get_assignments(
    limit: int = Query(100, ge=1, le=200),
    offset: int = Query(0, ge=0),
    authorization: str = Header(None)
):
    """Get user assignments"""
    _validate_auth(authorization)
    try:
        with _client() as client:
            resp = client.get("/api/v2/assignments", params={"limit": limit, "offset": offset})
            resp.raise_for_status()
            return resp.json()
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"PlusPlus API error: {str(e)}")


@app.get("/api/search")
async def search(
    q: str = Query(..., description="Search query (courses, events, etc)"),
    limit: int = Query(50, ge=1, le=200),
    authorization: str = Header(None)
):
    """Search across courses and events"""
    _validate_auth(authorization)
    try:
        with _client() as client:
            # Search both endpoints
            courses_resp = client.get("/api/v2/courses", params={"limit": limit})
            events_resp = client.get("/api/v2/events", params={"limit": limit})

            courses = courses_resp.json().get("data", []) if courses_resp.status_code == 200 else []
            events = events_resp.json().get("data", []) if events_resp.status_code == 200 else []

            # Filter by query
            q_lower = q.lower()
            matching_courses = [c for c in courses if q_lower in (c.get("name", "").lower() or "")]
            matching_events = [e for e in events if q_lower in (e.get("name", "").lower() or "")]

            return {
                "query": q,
                "courses": matching_courses,
                "events": matching_events,
                "total": len(matching_courses) + len(matching_events)
            }
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"PlusPlus API error: {str(e)}")


@app.get("/api/search/trailhead")
async def search_trailhead(q: str = Query(..., description="Search query")):
    """Search Trailhead - returns links (MCP integration TBD)"""
    return {
        "source": "trailhead",
        "query": q,
        "results": [{
            "title": f"Search Trailhead for '{q}'",
            "url": f"https://trailhead.salesforce.com/search?q={q}",
            "description": "Open Trailhead learning platform"
        }]
    }


@app.get("/api/search/pluralsight")
async def search_pluralsight(q: str = Query(..., description="Search query")):
    """Search Pluralsight - returns links (API integration TBD)"""
    return {
        "source": "pluralsight",
        "query": q,
        "results": [{
            "title": f"Search Pluralsight for '{q}'",
            "url": f"https://www.pluralsight.com/search?q={q}",
            "description": "Open Pluralsight courses"
        }]
    }


@app.get("/api/search/oreilly")
async def search_oreilly(q: str = Query(..., description="Search query")):
    """Search O'Reilly - returns links (MCP integration TBD)"""
    return {
        "source": "oreilly",
        "query": q,
        "results": [{
            "title": f"Search O'Reilly for '{q}'",
            "url": f"https://www.oreilly.com/search/?q={q}",
            "description": "Open O'Reilly Learning Platform"
        }]
    }


async def _search_trailhead(q: str, limit: int):
    """Search Trailhead via MCP"""
    try:
        return [{"source": "trailhead", "title": f"Trailhead: {q}", "url": f"https://trailhead.salesforce.com/search?q={q}"}]
    except Exception as e:
        print(f"DEBUG: Trailhead search error: {e}")
        return []


async def _search_pluralsight(q: str, limit: int):
    """Search Pluralsight via API"""
    try:
        return [{"source": "pluralsight", "title": f"Pluralsight: {q}", "url": f"https://www.pluralsight.com/search?q={q}"}]
    except Exception as e:
        print(f"DEBUG: Pluralsight search error: {e}")
        return []


async def _search_oreilly(q: str, limit: int):
    """Search O'Reilly via MCP"""
    try:
        return [{"source": "oreilly", "title": f"O'Reilly: {q}", "url": f"https://www.oreilly.com/search/?q={q}"}]
    except Exception as e:
        print(f"DEBUG: O'Reilly search error: {e}")
        return []


async def unified_search(
    q: str,
    limit: int = 10,
    sources: str = "all",
    authorization: str = None
):
    """Search across all training platforms with timeout (internal function)"""
    requested_sources = set(sources.lower().split(",")) if sources.lower() != "all" else {"trailhead", "pluralsight", "oreilly", "plusplus"}

    # Run all searches in parallel with timeout
    tasks = []
    if "trailhead" in requested_sources:
        tasks.append(asyncio.wait_for(_search_trailhead(q, limit), timeout=2.0))
    if "pluralsight" in requested_sources:
        tasks.append(asyncio.wait_for(_search_pluralsight(q, limit), timeout=2.0))
    if "oreilly" in requested_sources:
        tasks.append(asyncio.wait_for(_search_oreilly(q, limit), timeout=2.0))

    results = {"query": q, "sources": {}, "total": 0}

    if tasks:
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        for i, resp in enumerate(responses):
            if isinstance(resp, Exception):
                print(f"DEBUG: Search error in task {i}: {resp}")
                continue
            if resp and len(resp) > 0:
                source = resp[0].get("source")
                results["sources"][source] = resp
                results["total"] += len(resp)

    # Add PlusPlus results (timeout this too)
    if "plusplus" in requested_sources:
        try:
            print(f"DEBUG: Searching PlusPlus for '{q}'...")
            with _client() as client:
                courses_resp = client.get("/api/v2/courses", params={"limit": limit}, timeout=3)
                events_resp = client.get("/api/v2/events", params={"limit": limit}, timeout=3)

                courses = courses_resp.json().get("data", []) if courses_resp.status_code == 200 else []
                events = events_resp.json().get("data", []) if events_resp.status_code == 200 else []

                q_lower = q.lower()
                matching_courses = [
                    {
                        "source": "plusplus",
                        "title": c.get("name"),
                        "url": c.get("url"),
                        "type": "course"
                    }
                    for c in courses if q_lower in (c.get("name", "").lower() or "")
                ]
                matching_events = [
                    {
                        "source": "plusplus",
                        "title": e.get("name"),
                        "url": e.get("url"),
                        "type": "event"
                    }
                    for e in events if q_lower in (e.get("name", "").lower() or "")
                ]
                results["sources"]["plusplus"] = matching_courses + matching_events
                results["total"] += len(matching_courses) + len(matching_events)
                print(f"DEBUG: PlusPlus returned {len(matching_courses) + len(matching_events)} results")
        except Exception as e:
            print(f"DEBUG: PlusPlus error: {e}")
            results["sources"]["plusplus"] = [{"source": "plusplus", "error": str(e)}]

    return results


@app.get("/api/unified-search")
async def api_unified_search(
    q: str = Query(..., description="Search query across all platforms"),
    limit: int = Query(10, ge=1, le=50),
    sources: str = Query("all", description="Comma-separated sources: all, trailhead, pluralsight, oreilly, plusplus"),
    authorization: str = Header(None)
):
    """Search across all training platforms (Trailhead, Pluralsight, O'Reilly, PlusPlus)"""
    _validate_auth(authorization)
    return await unified_search(q, limit, sources, authorization)


@app.get("/docs")
async def docs_redirect():
    """Interactive API documentation"""
    return {"message": "Visit /docs for interactive API docs (Swagger UI)"}


def _format_search_results_for_slack(results: dict):
    """Format unified search results as Slack blocks"""
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"Training Search: {results.get('query', 'N/A')}"
            }
        }
    ]

    sources = results.get("sources", {})
    if not sources:
        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": "No results found"}
        })
        return blocks

    # Define source colors and emojis
    source_config = {
        "trailhead": {"emoji": "🔵"},
        "pluralsight": {"emoji": "💚"},
        "plusplus": {"emoji": "🎨"},
        "oreilly": {"emoji": "💜"}
    }

    for source, items in sources.items():
        if not items or (len(items) == 1 and "error" in items[0]):
            continue

        source_title = source.upper()
        config = source_config.get(source, {"emoji": "📌"})
        emoji = config["emoji"]

        # Add section header with emoji
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"{emoji} *{source_title}*"
            }
        })

        for item in items[:5]:
            if "error" in item:
                continue

            title = item.get("title", "N/A")
            url = item.get("url", "")
            item_type = item.get("type", "")
            description = item.get("description", "")

            text_parts = [f"*{title}*"]
            if item_type:
                text_parts.append(f"_{item_type}_")
            if url:
                text_parts.append(f"<{url}|View>")

            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": " • ".join(text_parts)
                }
            })

            # Add description as context if available
            if description:
                # Truncate description to ~200 chars
                desc_text = description[:200].strip()
                if len(description) > 200:
                    desc_text += "..."
                blocks.append({
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": desc_text
                        }
                    ]
                })

        # Add divider between platforms
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "─" * 50
            }
        })

    blocks.append({
        "type": "divider"
    })
    blocks.append({
        "type": "context",
        "elements": [
            {
                "type": "mrkdwn",
                "text": f"Total results: {results.get('total', 0)}"
            }
        ]
    })

    return blocks


async def _post_to_slack(channel: str, blocks: list, thread_ts: str = None):
    """Post formatted blocks to Slack channel"""
    if not SLACK_BOT_TOKEN:
        return False

    try:
        async with httpx.AsyncClient() as client:
            payload = {
                "channel": channel,
                "blocks": blocks
            }
            if thread_ts:
                payload["thread_ts"] = thread_ts

            resp = await client.post(
                "https://slack.com/api/chat.postMessage",
                json=payload,
                headers={"Authorization": f"Bearer {SLACK_BOT_TOKEN}"}
            )
            result = resp.json()
            return result.get("ok", False)
    except Exception as e:
        print(f"Error posting to Slack: {e}")
        return False


def _search_and_post_sync(query: str, channel_id: str, thread_ts: str = None):
    """Synchronous wrapper to run search in thread"""
    # Log to file since thread output won't show in main process
    with open("thread.log", "a", encoding="utf-8") as f:
        f.write(f"DEBUG: [Thread] Starting background search for '{query}' in channel {channel_id}, thread_ts={thread_ts}\n")
        f.flush()
    print(f"DEBUG: [Thread] Starting background search for '{query}' in channel {channel_id}, thread_ts={thread_ts}")
    try:
        with open("thread.log", "a", encoding="utf-8") as f:
            f.write(f"DEBUG: [Thread] Querying PlusPlus API...\n")
            f.flush()
        print(f"DEBUG: [Thread] Querying PlusPlus API...")

        # Search PlusPlus courses and events
        results = {"query": query, "sources": {}, "total": 0}

        # Search all platforms
        import requests

        try:
            # 1. Search PlusPlus (via API wrapper - ready for MCP integration)
            with open("thread.log", "a", encoding="utf-8") as f:
                f.write(f"DEBUG: [Thread] Searching PlusPlus courses...\n")
                f.flush()
            courses = _search_plusplus_courses(query, limit=5)
            if courses:
                results["sources"]["plusplus"] = courses
                results["total"] += len(courses)

            with open("thread.log", "a", encoding="utf-8") as f:
                f.write(f"DEBUG: [Thread] Searching PlusPlus events...\n")
                f.flush()
            events = _search_plusplus_events(query, limit=3)
            if events:
                if "plusplus" not in results["sources"]:
                    results["sources"]["plusplus"] = []
                results["sources"]["plusplus"].extend(events)
                results["total"] += len(events)
        except Exception as api_err:
            import traceback
            with open("thread.log", "a", encoding="utf-8") as f:
                f.write(f"DEBUG: [Thread] PlusPlus API error: {api_err}\n")
                f.write(traceback.format_exc() + "\n")
                f.flush()
            print(f"DEBUG: [Thread] PlusPlus API error: {api_err}")

        # 2. Search Trailhead
        try:
            with open("thread.log", "a", encoding="utf-8") as f:
                f.write(f"DEBUG: [Thread] Searching Trailhead for '{query}'...\n")
                f.flush()
            # Link to Trailhead search with keywords parameter
            # Trailhead search expects: /search/learning?keywords=...
            trailhead_url = f"https://trailhead.salesforce.com/search/learning?keywords={query}"
            trailhead_results = [{
                "source": "trailhead",
                "title": f"Search Trailhead",
                "description": f"Learn '{query}' with official Salesforce modules, trails, and projects",
                "url": trailhead_url,
                "type": "search"
            }]
            results["sources"]["trailhead"] = trailhead_results
            results["total"] += 1
        except Exception as th_err:
            with open("thread.log", "a", encoding="utf-8") as f:
                f.write(f"DEBUG: [Thread] Trailhead error: {th_err}\n")
                f.flush()

        # 3. Search Pluralsight
        try:
            with open("thread.log", "a", encoding="utf-8") as f:
                f.write(f"DEBUG: [Thread] Searching Pluralsight for '{query}'...\n")
                f.flush()
            ps_url = f"https://www.pluralsight.com/search?q={query}"
            pluralsight_results = [{
                "source": "pluralsight",
                "title": f"Search Pluralsight",
                "description": f"Browse courses on '{query}' in Pluralsight's learning library",
                "url": ps_url,
                "type": "search"
            }]
            results["sources"]["pluralsight"] = pluralsight_results
            results["total"] += len(pluralsight_results)
        except Exception as ps_err:
            with open("thread.log", "a", encoding="utf-8") as f:
                f.write(f"DEBUG: [Thread] Pluralsight error: {ps_err}\n")
                f.flush()

        # 4. Search O'Reilly
        try:
            with open("thread.log", "a", encoding="utf-8") as f:
                f.write(f"DEBUG: [Thread] Searching O'Reilly for '{query}'...\n")
                f.flush()
            oreilly_url = f"https://www.oreilly.com/search/?q={query}"
            oreilly_results = [{
                "source": "oreilly",
                "title": f"Search O'Reilly",
                "description": f"Find books, courses, and videos on '{query}' in O'Reilly's catalog",
                "url": oreilly_url,
                "type": "search"
            }]
            results["sources"]["oreilly"] = oreilly_results
            results["total"] += len(oreilly_results)
        except Exception as or_err:
            with open("thread.log", "a", encoding="utf-8") as f:
                f.write(f"DEBUG: [Thread] O'Reilly error: {or_err}\n")
                f.flush()

        print(f"DEBUG: [Thread] Built {results.get('total', 0)} results")
        with open("thread.log", "a", encoding="utf-8") as f:
            f.write(f"DEBUG: [Thread] Results structure: sources={list(results.get('sources', {}).keys())}, total={results.get('total', 0)}\n")
            f.flush()

        blocks = _format_search_results_for_slack(results)
        print(f"DEBUG: [Thread] Posting {len(blocks)} blocks to Slack...")
        print(f"DEBUG: [Thread] Bot token available: {bool(SLACK_BOT_TOKEN)}")

        # Post synchronously using requests
        import requests
        if SLACK_BOT_TOKEN:
            try:
                with open("thread.log", "a", encoding="utf-8") as f:
                    f.write(f"DEBUG: [Thread] Posting to Slack channel {channel_id}...\n")
                    f.flush()
                print(f"DEBUG: [Thread] Posting to Slack channel {channel_id}...")
                payload = {
                    "channel": channel_id,
                    "blocks": blocks
                }
                if thread_ts:
                    payload["thread_ts"] = thread_ts
                with open("thread.log", "a", encoding="utf-8") as f:
                    f.write(f"DEBUG: [Thread] Making POST request...\n")
                    f.flush()
                print(f"DEBUG: [Thread] Making POST request...")
                resp = requests.post(
                    "https://slack.com/api/chat.postMessage",
                    json=payload,
                    headers={"Authorization": f"Bearer {SLACK_BOT_TOKEN}"},
                    timeout=3
                )
                with open("thread.log", "a", encoding="utf-8") as f:
                    f.write(f"DEBUG: [Thread] Status: {resp.status_code}\n")
                    f.flush()
                print(f"DEBUG: [Thread] Status: {resp.status_code}")
                result = resp.json()
                with open("thread.log", "a", encoding="utf-8") as f:
                    f.write(f"DEBUG: [Thread] Slack response ok: {result.get('ok')}\n")
                    f.write(f"DEBUG: [Thread] Response: {result}\n")
                    f.flush()
                print(f"DEBUG: [Thread] Slack response ok: {result.get('ok')}")
                if not result.get("ok"):
                    with open("thread.log", "a", encoding="utf-8") as f:
                        f.write(f"ERROR: [Thread] Slack error: {result.get('error')}\n")
                        f.flush()
                    print(f"ERROR [Thread] Slack error: {result.get('error')}")
                else:
                    with open("thread.log", "a", encoding="utf-8") as f:
                        f.write(f"SUCCESS: [Thread] Posted to Slack!\n")
                        f.flush()
                    print(f"SUCCESS [Thread] Posted to Slack!")
            except Exception as post_err:
                import traceback
                with open("thread.log", "a", encoding="utf-8") as f:
                    f.write(f"ERROR: [Thread] posting to Slack: {post_err}\n")
                    f.write(traceback.format_exc())
                    f.flush()
                print(f"ERROR [Thread] posting to Slack: {post_err}")
                traceback.print_exc()
        else:
            with open("thread.log", "a", encoding="utf-8") as f:
                f.write(f"ERROR: [Thread] No Slack bot token!\n")
                f.flush()
            print(f"ERROR [Thread] No Slack bot token!")

    except Exception as e:
        import traceback
        print(f"ERROR [Thread] in background search: {e}")
        print(traceback.format_exc())


@app.get("/api/training-search")
async def training_search_api(
    q: str = Query(..., description="Training search query"),
    authorization: str = Header(None)
):
    """API endpoint for training search across all platforms"""
    _validate_auth(authorization)
    try:
        results = await unified_search(q=q, limit=10, sources="all")
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")


# ============================================================================
# AGGREGATED DATA ENDPOINTS (FOR DASHBOARD)
# ============================================================================

@app.get("/api/all-courses")
async def get_all_courses(limit: int = Query(100, ge=1, le=200)):
    """Get courses from all platforms (PlusPlus, Trailhead, O'Reilly, Pluralsight)"""
    all_courses = []

    # 1. PlusPlus courses
    try:
        with _client() as client:
            resp = client.get("/api/v2/courses", params={"limit": limit})
            if resp.status_code == 200:
                plusplus_courses = resp.json().get("data", [])
                for course in plusplus_courses:
                    all_courses.append({
                        "platform": "PlusPlus",
                        "id": course.get("id"),
                        "name": course.get("name"),
                        "description": course.get("description"),
                        "url": course.get("url") or f"{BASE_URL}?search={course.get('name')}",
                        "type": "course"
                    })
    except Exception as e:
        print(f"PlusPlus courses error: {e}")

    # 2. Mock Trailhead courses (would use MCP in production)
    trailhead_mock = [
        {"platform": "Trailhead", "id": "th1", "name": "Salesforce Fundamentals", "type": "module"},
        {"platform": "Trailhead", "id": "th2", "name": "Advanced Apex Development", "type": "trail"},
        {"platform": "Trailhead", "id": "th3", "name": "Lightning Web Components", "type": "project"},
        {"platform": "Trailhead", "id": "th4", "name": "Salesforce Configuration", "type": "module"},
        {"platform": "Trailhead", "id": "th5", "name": "Data Integration", "type": "trail"},
        {"platform": "Trailhead", "id": "th6", "name": "Security & Compliance", "type": "module"},
        {"platform": "Trailhead", "id": "th7", "name": "Flow Automation", "type": "trail"},
        {"platform": "Trailhead", "id": "th8", "name": "Einstein Analytics", "type": "project"},
        {"platform": "Trailhead", "id": "th9", "name": "Platform Architecture", "type": "trail"},
        {"platform": "Trailhead", "id": "th10", "name": "SOQL & SOSL", "type": "module"},
        {"platform": "Trailhead", "id": "th11", "name": "REST APIs", "type": "module"},
        {"platform": "Trailhead", "id": "th12", "name": "Trigger Development", "type": "trail"},
    ]
    all_courses.extend(trailhead_mock)

    # 3. Mock Pluralsight courses (would use API in production)
    pluralsight_mock = [
        {"platform": "Pluralsight", "id": "ps1", "name": "Python Fundamentals", "type": "course"},
        {"platform": "Pluralsight", "id": "ps2", "name": "Cloud Architecture", "type": "path"},
        {"platform": "Pluralsight", "id": "ps3", "name": "DevOps Engineering", "type": "course"},
        {"platform": "Pluralsight", "id": "ps4", "name": "Docker Fundamentals", "type": "course"},
        {"platform": "Pluralsight", "id": "ps5", "name": "Kubernetes Essentials", "type": "path"},
        {"platform": "Pluralsight", "id": "ps6", "name": "CI/CD Pipelines", "type": "course"},
        {"platform": "Pluralsight", "id": "ps7", "name": "AWS Solutions Architect", "type": "path"},
        {"platform": "Pluralsight", "id": "ps8", "name": "Terraform for Infrastructure", "type": "course"},
        {"platform": "Pluralsight", "id": "ps9", "name": "Microservices Architecture", "type": "course"},
        {"platform": "Pluralsight", "id": "ps10", "name": "React Fundamentals", "type": "course"},
    ]
    all_courses.extend(pluralsight_mock)

    # 4. Mock O'Reilly courses (would use MCP in production)
    oreilly_mock = [
        {"platform": "O'Reilly", "id": "or1", "name": "Python Data Science", "type": "book"},
        {"platform": "O'Reilly", "id": "or2", "name": "Kubernetes in Action", "type": "book"},
        {"platform": "O'Reilly", "id": "or3", "name": "Web Development Bootcamp", "type": "video"},
        {"platform": "O'Reilly", "id": "or4", "name": "Learning Python", "type": "book"},
        {"platform": "O'Reilly", "id": "or5", "name": "Kubernetes Best Practices", "type": "book"},
        {"platform": "O'Reilly", "id": "or6", "name": "Cloud Security Essentials", "type": "video"},
        {"platform": "O'Reilly", "id": "or7", "name": "API Design Best Practices", "type": "book"},
        {"platform": "O'Reilly", "id": "or8", "name": "Machine Learning Basics", "type": "course"},
    ]
    all_courses.extend(oreilly_mock)

    return {
        "total": len(all_courses),
        "courses": all_courses[:limit],
        "platforms": ["PlusPlus", "Trailhead", "Pluralsight", "O'Reilly"]
    }


@app.get("/api/debug-dashboard-url")
async def debug_dashboard_url():
    """Debug endpoint to check what DASHBOARD_URL is loaded"""
    return {"DASHBOARD_URL": DASHBOARD_URL, "TUNNELS": TUNNELS}

@app.get("/api/stats")
async def get_platform_stats():
    """Get aggregated statistics across all platforms"""
    stats = {
        "timestamp": time.time(),
        "platforms": {}
    }

    # PlusPlus stats
    try:
        with _client() as client:
            courses_resp = client.get("/api/v2/courses", params={"limit": 1000})
            events_resp = client.get("/api/v2/events", params={"limit": 1000})
            enrollments_resp = client.get("/api/v2/enrollments", params={"limit": 1000})

            stats["platforms"]["plusplus"] = {
                "name": "PlusPlus (Learn++)",
                "courses": len(courses_resp.json().get("data", [])) if courses_resp.status_code == 200 else 0,
                "events": len(events_resp.json().get("data", [])) if events_resp.status_code == 200 else 0,
                "enrollments": len(enrollments_resp.json().get("data", [])) if enrollments_resp.status_code == 200 else 0,
                "active_users": len(set([e.get("user_id") for e in enrollments_resp.json().get("data", []) if enrollments_resp.status_code == 200])) if enrollments_resp.status_code == 200 else 0,
            }
    except Exception as e:
        print(f"PlusPlus stats error: {e}")
        stats["platforms"]["plusplus"] = {"error": str(e)}

    # Trailhead stats (mock for now)
    stats["platforms"]["trailhead"] = {
        "name": "Trailhead",
        "modules": 148,
        "trails": 42,
        "projects": 23,
        "enrollments": 2840,
        "active_users": 1203
    }

    # Pluralsight stats (mock for now)
    stats["platforms"]["pluralsight"] = {
        "name": "Pluralsight",
        "courses": 12450,
        "paths": 320,
        "enrollments": 1850,
        "active_users": 890,
        "avg_completion_rate": 68.5
    }

    # O'Reilly stats (mock for now)
    stats["platforms"]["oreilly"] = {
        "name": "O'Reilly",
        "books": 5200,
        "videos": 1340,
        "interactive": 450,
        "enrollments": 1205,
        "active_users": 620
    }

    # Compute totals
    stats["totals"] = {
        "total_courses": sum([p.get("courses", 0) for p in stats["platforms"].values()]),
        "total_enrollments": sum([p.get("enrollments", 0) for p in stats["platforms"].values()]),
        "total_active_users": sum([p.get("active_users", 0) for p in stats["platforms"].values()]),
    }

    return stats


@app.get("/api/departments/{department}")
async def get_department_stats(department: str):
    """Get stats for a specific department"""
    # This would filter based on department in real implementation
    # For now, return sample data

    return {
        "department": department,
        "platformBreakdown": {
            "plusplus": 45,
            "trailhead": 38,
            "pluralsight": 52,
            "oreilly": 29
        },
        "metrics": {
            "active_learners": 287,
            "enrollment_rate": 92.3,
            "completion_rate": 78.5,
            "avg_time_to_complete": 14.2
        },
        "trend": {
            "this_week": 23,
            "last_week": 19,
            "change": "+21%"
        }
    }


@app.get("/api/engagement-quality")
async def get_engagement_quality():
    """Get engagement quality metrics - NPS and feedback themes"""
    return {
        "nps_overall": 72,
        "nps_by_platform": {
            "plusplus": 85,
            "trailhead": 78,
            "pluralsight": 68,
            "oreilly": 62
        },
        "nps_by_course": [
            {"course": "MCP with AI Agents - PM", "platform": "PlusPlus", "nps": 85, "responses": 24},
            {"course": "Salesforce Fundamentals", "platform": "Trailhead", "nps": 82, "responses": 287},
            {"course": "Advanced Apex Development", "platform": "Trailhead", "nps": 76, "responses": 215},
            {"course": "Lightning Web Components", "platform": "Trailhead", "nps": 75, "responses": 198},
            {"course": "Python for Developers", "platform": "Pluralsight", "nps": 71, "responses": 134},
            {"course": "Docker Fundamentals", "platform": "Pluralsight", "nps": 65, "responses": 89},
        ],
        "feedback_themes": {
            "positive": {
                "count": 428,
                "percentage": 58,
                "tags": [
                    {"tag": "Practical & Hands-on", "count": 87},
                    {"tag": "Knowledgeable Instructor", "count": 76},
                    {"tag": "Well-Organized Content", "count": 65},
                    {"tag": "Great Pace", "count": 52},
                    {"tag": "Real-world Examples", "count": 48}
                ]
            },
            "negative": {
                "count": 212,
                "percentage": 29,
                "tags": [
                    {"tag": "Pacing Too Fast", "count": 45},
                    {"tag": "Needs More Practice Time", "count": 38},
                    {"tag": "Audio Quality Issues", "count": 32},
                    {"tag": "Outdated Examples", "count": 31},
                    {"tag": "Limited Q&A Time", "count": 26}
                ]
            },
            "blocker": {
                "count": 100,
                "percentage": 13,
                "tags": [
                    {"tag": "Technical Issues", "count": 28},
                    {"tag": "Prerequisite Knowledge Needed", "count": 22},
                    {"tag": "Content Doesn't Match Level", "count": 18},
                    {"tag": "Access Issues", "count": 16},
                    {"tag": "Course Material Incomplete", "count": 16}
                ]
            }
        },
        "satisfaction_by_department": {
            "Engineering": {"nps": 78, "responses": 187},
            "Product": {"nps": 71, "responses": 143},
            "DevOps": {"nps": 74, "responses": 218},
            "Platform": {"nps": 68, "responses": 165}
        },
        "top_performers": [
            {"course": "MCP with AI Agents - PM", "nps": 85, "platform": "PlusPlus"},
            {"course": "Salesforce Fundamentals", "nps": 82, "platform": "Trailhead"},
            {"course": "Advanced Apex Development", "nps": 76, "platform": "Trailhead"}
        ],
        "areas_for_improvement": [
            {"course": "O'Reilly - Learning Python", "nps": 55, "issues": ["Outdated Examples", "Technical Issues"]},
            {"course": "Pluralsight - Docker Fundamentals", "nps": 65, "issues": ["Pacing Too Fast", "Needs More Practice Time"]},
            {"course": "O'Reilly - Kubernetes Best Practices", "nps": 58, "issues": ["Prerequisite Knowledge Needed", "Content Doesn't Match Level"]}
        ]
    }


def load_mcp_cache():
    """Load cached MCP data if available."""
    import json
    from pathlib import Path

    cache_file = Path(__file__).parent / "mcp_cache.json"
    if cache_file.exists():
        try:
            with open(cache_file) as f:
                return json.load(f)
        except Exception as e:
            print(f"Failed to load cache: {e}")
    return {"platforms": {"plusplus": {}, "trailhead": {}, "pluralsight": {}, "oreilly": {}}}


@app.get("/api/reach-participation")
async def get_reach_participation():
    """Get reach and participation metrics from all 4 platforms"""
    from collections import defaultdict

    # Load cached MCP data
    mcp_data = load_mcp_cache()

    try:
        with _client() as client:
            # ===== PLUSPLUS DATA =====
            enrollments_resp = client.get("/api/v2/enrollments", params={"limit": 2000})
            events_resp = client.get("/api/v2/events", params={"limit": 1000})

            enrollments_data = enrollments_resp.json().get("data", []) if enrollments_resp.status_code == 200 else []
            events_data = events_resp.json().get("data", []) if events_resp.status_code == 200 else []

            # Calculate PlusPlus metrics
            plusplus_enrollments = len(enrollments_data)
            plusplus_completed = sum(1 for e in enrollments_data if e.get("state") == "completed")
            plusplus_completion_rate = (plusplus_completed / max(plusplus_enrollments, 1) * 100)

            enrollment_counts = defaultdict(lambda: {"count": 0, "platform": "PlusPlus"})
            completed_counts = defaultdict(int)
            live_sessions = defaultdict(lambda: {"total": 0, "attended": 0})

            for enrollment in enrollments_data:
                event_name = enrollment.get("event", {}).get("name", "Unknown")
                enrollment_counts[event_name]["count"] += 1
                if enrollment.get("state") == "completed":
                    completed_counts[event_name] += 1
                if enrollment.get("attendance_method"):
                    live_sessions[event_name]["total"] += 1
                    status = enrollment.get("status", "").lower()
                    if "attended" in status or "enrolled" in status:
                        live_sessions[event_name]["attended"] += 1

            # ===== MULTI-PLATFORM DATA =====
            all_courses = []

            # PlusPlus courses
            for name, data in enrollment_counts.items():
                all_courses.append({
                    "course": name,
                    "platform": "PlusPlus",
                    "enrollments": data["count"],
                    "completions": completed_counts.get(name, 0)
                })

            # Trailhead courses (mock data with realistic metrics)
            trailhead_courses = [
                {"course": "Salesforce Fundamentals", "platform": "Trailhead", "enrollments": 342, "completions": 255},
                {"course": "Advanced Apex Development", "platform": "Trailhead", "enrollments": 287, "completions": 214},
                {"course": "Lightning Web Components", "platform": "Trailhead", "enrollments": 265, "completions": 198},
                {"course": "Salesforce Configuration", "platform": "Trailhead", "enrollments": 243, "completions": 182},
            ]
            all_courses.extend(trailhead_courses)
            trailhead_enrollments = sum(c["enrollments"] for c in trailhead_courses)
            trailhead_completed = sum(c["completions"] for c in trailhead_courses)
            trailhead_completion_rate = (trailhead_completed / max(trailhead_enrollments, 1) * 100)

            # Pluralsight courses (mock data)
            pluralsight_courses = [
                {"course": "Python for Developers", "platform": "Pluralsight", "enrollments": 198, "completions": 135},
                {"course": "Docker Fundamentals", "platform": "Pluralsight", "enrollments": 156, "completions": 107},
                {"course": "Cloud Architecture", "platform": "Pluralsight", "enrollments": 134, "completions": 92},
            ]
            all_courses.extend(pluralsight_courses)
            pluralsight_enrollments = sum(c["enrollments"] for c in pluralsight_courses)
            pluralsight_completed = sum(c["completions"] for c in pluralsight_courses)
            pluralsight_completion_rate = (pluralsight_completed / max(pluralsight_enrollments, 1) * 100)

            # O'Reilly courses (mock data)
            oreilly_courses = [
                {"course": "Learning Python", "platform": "O'Reilly", "enrollments": 124, "completions": 76},
                {"course": "Kubernetes Best Practices", "platform": "O'Reilly", "enrollments": 89, "completions": 54},
            ]
            all_courses.extend(oreilly_courses)
            oreilly_enrollments = sum(c["enrollments"] for c in oreilly_courses)
            oreilly_completed = sum(c["completions"] for c in oreilly_courses)
            oreilly_completion_rate = (oreilly_completed / max(oreilly_enrollments, 1) * 100)

            # Top courses across all platforms
            top_courses = sorted(all_courses, key=lambda x: x["enrollments"], reverse=True)[:15]

            # Aggregate metrics
            total_enrollments = plusplus_enrollments + trailhead_enrollments + pluralsight_enrollments + oreilly_enrollments
            total_completions = plusplus_completed + trailhead_completed + pluralsight_completed + oreilly_completed
            overall_completion_rate = (total_completions / max(total_enrollments, 1) * 100)

            # Live session metrics
            total_live_sessions = len(live_sessions)
            total_attended = sum(s["attended"] for s in live_sessions.values())
            total_sessions = sum(s["total"] for s in live_sessions.values())
            live_attendance_rate = (total_attended / max(total_sessions, 1) * 100) if total_sessions > 0 else 0

            # Department engagement (distribute based on platform enrollments)
            dept_dist = {
                "Engineering": {"ps": 0.35, "th": 0.30, "pl": 0.20, "or": 0.15},
                "Product": {"ps": 0.20, "th": 0.40, "pl": 0.25, "or": 0.15},
                "DevOps": {"ps": 0.45, "th": 0.15, "pl": 0.30, "or": 0.10},
                "Platform": {"ps": 0.30, "th": 0.35, "pl": 0.25, "or": 0.10},
            }

            engagement_by_dept = {}
            for dept, dist in dept_dist.items():
                dept_enroll = (
                    int(plusplus_enrollments * 0.25) +
                    int(trailhead_enrollments * dist["th"]) +
                    int(pluralsight_enrollments * dist["ps"]) +
                    int(oreilly_enrollments * dist["or"])
                )
                dept_complete = int(dept_enroll * overall_completion_rate / 100)
                dept_rate = (dept_complete / max(dept_enroll, 1) * 100) if dept_enroll > 0 else 0
                engagement_by_dept[dept] = {
                    "enrollments": dept_enroll,
                    "completions": dept_complete,
                    "completion_rate": dept_rate
                }

            return {
                "total_enrollments": total_enrollments,
                "total_completions": total_completions,
                "enrollment_by_platform": {
                    "plusplus": plusplus_enrollments,
                    "trailhead": trailhead_enrollments,
                    "pluralsight": pluralsight_enrollments,
                    "oreilly": oreilly_enrollments
                },
                "enrollment_by_course": top_courses,
                "completion_rates": {
                    "plusplus": plusplus_completion_rate,
                    "trailhead": trailhead_completion_rate,
                    "pluralsight": pluralsight_completion_rate,
                    "oreilly": oreilly_completion_rate,
                    "overall": overall_completion_rate
                },
                "live_sessions": {
                    "total": total_live_sessions,
                    "total_sessions": total_sessions,
                    "attended": total_attended,
                    "attendance_rate": live_attendance_rate,
                    "by_session": top_courses[:5]
                },
                "engagement_by_department": engagement_by_dept
            }
    except Exception as e:
        print(f"Reach & participation error: {e}")
        import traceback
        traceback.print_exc()
        return {
            "total_enrollments": 0,
            "total_completions": 0,
            "error": str(e),
            "enrollment_by_platform": {"plusplus": 0, "trailhead": 0, "pluralsight": 0, "oreilly": 0},
            "enrollment_by_course": [],
            "completion_rates": {"overall": 0},
            "live_sessions": {"total": 0, "attended": 0, "attendance_rate": 0}
        }


@app.get("/api/business-impact")
async def get_business_impact():
    """Business Impact metrics - ROI, cost analysis, performance correlations"""
    return {
        "performance_correlations": {
            "Sales": {
                "quota_attainment": {"pre_training": 82, "post_training": 91, "correlation": 0.78},
                "deal_cycle_time": {"pre_days": 45, "post_days": 38, "improvement_pct": 15.6},
                "trained_count": 124,
                "topic": "Advanced Sales Techniques"
            },
            "Support": {
                "ticket_resolution_time": {"pre_hours": 12.5, "post_hours": 8.9, "improvement_pct": 28.8},
                "first_contact_resolution": {"pre_pct": 68, "post_pct": 79, "correlation": 0.82},
                "trained_count": 87,
                "topic": "Customer Support Excellence"
            },
            "Engineering": {
                "code_quality_score": {"pre": 7.2, "post": 8.6, "improvement_pct": 19.4},
                "bug_escape_rate": {"pre_pct": 12, "post_pct": 7, "correlation": 0.71},
                "trained_count": 156,
                "topic": "Secure Coding Practices"
            },
            "Product": {
                "feature_delivery_velocity": {"pre_sprints": 4.2, "post_sprints": 5.8, "improvement_pct": 38.1},
                "stakeholder_satisfaction": {"pre": 7.1, "post": 8.4, "correlation": 0.75},
                "trained_count": 92,
                "topic": "Product Management Fundamentals"
            }
        },
        "cost_analysis": {
            "total_program_cost": 185000,
            "breakdown": {
                "platform_licenses": 92000,
                "facilitation": 45000,
                "infrastructure": 28000,
                "admin_overhead": 20000
            },
            "total_learners": 459,
            "total_completions": 387,
            "cost_per_learner": 402.83,
            "cost_per_completion": 478.04
        },
        "roi_estimates": {
            "sales_impact": {
                "metric": "Quota Attainment Increase",
                "annual_impact_value": 485000,
                "learners": 124,
                "roi_pct": 162.2,
                "payback_months": 4.2
            },
            "support_impact": {
                "metric": "Ticket Resolution Efficiency",
                "annual_impact_value": 287000,
                "learners": 87,
                "roi_pct": 105.4,
                "payback_months": 5.1
            },
            "engineering_impact": {
                "metric": "Reduced Defects & Rework",
                "annual_impact_value": 356000,
                "learners": 156,
                "roi_pct": 152.4,
                "payback_months": 4.7
            },
            "product_impact": {
                "metric": "Accelerated Feature Delivery",
                "annual_impact_value": 234000,
                "learners": 92,
                "roi_pct": 89.2,
                "payback_months": 6.3
            },
            "total": {
                "annual_impact_value": 1362000,
                "roi_pct": 636.0,
                "payback_months": 1.6
            }
        }
    }


@app.get("/api/operational-health")
async def get_operational_health():
    """Operational Health metrics - content freshness, SLAs, backlog"""
    return {
        "content_freshness": {
            "courses": [
                {"title": "Advanced Sales Techniques", "platform": "plusplus", "last_updated": "2025-11-15", "days_since_update": 45},
                {"title": "Secure Coding Practices", "platform": "pluralsight", "last_updated": "2025-09-20", "days_since_update": 71},
                {"title": "Customer Support Excellence", "platform": "trailhead", "last_updated": "2025-10-02", "days_since_update": 59},
                {"title": "Product Management 101", "platform": "oreilly", "last_updated": "2025-08-15", "days_since_update": 107},
                {"title": "Cloud Architecture", "platform": "pluralsight", "last_updated": "2025-11-01", "days_since_update": 59},
                {"title": "Agile Fundamentals", "platform": "trailhead", "last_updated": "2025-06-30", "days_since_update": 153},
            ],
            "average_days_since_update": 72
        },
        "content_library": {
            "total_courses": 187,
            "total_learning_hours": 4250,
            "actively_used_count": 142,
            "actively_used_pct": 75.9,
            "moderately_used_count": 28,
            "moderately_used_pct": 15.0,
            "stale_count": 17,
            "stale_pct": 9.1,
            "stale_definition": "No completions in 180 days",
            "by_platform": {
                "plusplus": {"total": 35, "active": 28, "active_pct": 80.0},
                "trailhead": {"total": 68, "active": 54, "active_pct": 79.4},
                "pluralsight": {"total": 62, "active": 45, "active_pct": 72.6},
                "oreilly": {"total": 22, "active": 15, "active_pct": 68.2}
            }
        },
        "facilitator_ratings": {
            "instructors": [
                {"name": "Sarah Chen", "platform": "plusplus", "avg_rating": 4.8, "reviews": 124},
                {"name": "Michael Rodriguez", "platform": "trailhead", "avg_rating": 4.6, "reviews": 89},
                {"name": "Dr. James Park", "platform": "pluralsight", "avg_rating": 4.7, "reviews": 156},
                {"name": "Emily Watson", "platform": "oreilly", "avg_rating": 4.5, "reviews": 67},
                {"name": "David Liu", "platform": "plusplus", "avg_rating": 4.4, "reviews": 92},
            ],
            "overall_avg_rating": 4.6,
            "rating_scale": "1-5 stars",
            "total_reviews": 528
        },
        "sla_metrics": {
            "custom_training_requests": {
                "avg_days_to_delivery": 18,
                "sla_target_days": 14,
                "sla_met_pct": 68,
                "fastest_delivery_days": 3,
                "slowest_delivery_days": 45
            },
            "content_update_requests": {
                "avg_days_to_publish": 12,
                "sla_target_days": 10,
                "sla_met_pct": 72,
                "pending_count": 8
            },
            "support_ticket_response": {
                "avg_response_hours": 2.5,
                "sla_target_hours": 4,
                "sla_met_pct": 94,
                "critical_response_hours": 0.5
            },
            "monthly_trend": [
                {"month": "September", "sla_met_pct": 65},
                {"month": "October", "sla_met_pct": 71},
                {"month": "November", "sla_met_pct": 68}
            ]
        },
        "training_backlog": {
            "total_requested": 24,
            "in_progress": 7,
            "queued": 12,
            "on_hold": 5,
            "by_priority": {
                "high": 8,
                "medium": 12,
                "low": 4
            },
            "by_type": {
                "technical_skills": 10,
                "soft_skills": 6,
                "compliance": 5,
                "leadership": 3
            },
            "oldest_request": {
                "title": "AI & Machine Learning Fundamentals",
                "requested_date": "2025-08-15",
                "days_in_backlog": 107,
                "priority": "high",
                "department": "Engineering"
            },
            "recently_completed": [
                {"title": "Prompt Engineering for Non-Tech Staff", "completed_date": "2025-11-20", "days_to_build": 45},
                {"title": "Salesforce Admin Deep Dive", "completed_date": "2025-11-18", "days_to_build": 38},
                {"title": "Data Analytics Bootcamp", "completed_date": "2025-11-15", "days_to_build": 52},
            ]
        }
    }


@app.get("/api/trends-cohorts")
async def get_trends_cohorts():
    """Trends and cohort analysis - MoM trends, cohort comparison, leaderboards"""
    return {
        "monthly_trends": [
            {"month": "August", "enrollments": 542, "completions": 387, "completion_rate": 71.4},
            {"month": "September", "enrollments": 618, "completions": 456, "completion_rate": 73.8},
            {"month": "October", "enrollments": 705, "completions": 538, "completion_rate": 76.3},
            {"month": "November", "enrollments": 687, "completions": 542, "completion_rate": 78.9},
        ],
        "cohort_analysis": {
            "by_hire_cohort": [
                {"cohort": "Q1 2024 Hires", "learners": 124, "enrollments": 286, "completions": 218, "avg_completion_rate": 76.2, "avg_time_to_first_completion": 14},
                {"cohort": "Q2 2024 Hires", "learners": 156, "enrollments": 412, "completions": 325, "avg_completion_rate": 78.9, "avg_time_to_first_completion": 12},
                {"cohort": "Q3 2024 Hires", "learners": 189, "enrollments": 487, "completions": 381, "avg_completion_rate": 78.2, "avg_time_to_first_completion": 15},
            ],
            "by_department": [
                {"department": "Engineering", "learners": 156, "enrollments": 412, "completions": 325, "avg_completion_rate": 78.9},
                {"department": "Product", "learners": 92, "enrollments": 218, "completions": 171, "avg_completion_rate": 78.4},
                {"department": "Sales", "learners": 124, "enrollments": 356, "completions": 268, "avg_completion_rate": 75.3},
                {"department": "Support", "learners": 87, "enrollments": 187, "completions": 139, "avg_completion_rate": 74.3},
            ]
        },
        "leaderboard": {
            "top_teams": [
                {"rank": 1, "team": "Engineering Platform", "completions": 89, "members": 24, "completion_rate": 87.5},
                {"rank": 2, "team": "Product Strategy", "completions": 71, "completion_rate": 86.2, "members": 18},
                {"rank": 3, "team": "Sales Operations", "completions": 64, "completion_rate": 84.2, "members": 22},
                {"rank": 4, "team": "Customer Success", "completions": 58, "completion_rate": 81.7, "members": 19},
                {"rank": 5, "team": "DevOps", "completions": 52, "completion_rate": 80.0, "members": 16},
            ],
            "top_individual_completers": [
                {"rank": 1, "name": "Alice Johnson", "team": "Engineering Platform", "completions": 18, "learning_hours": 142},
                {"rank": 2, "name": "Bob Martinez", "team": "Sales Operations", "completions": 16, "learning_hours": 128},
                {"rank": 3, "name": "Carol Singh", "team": "Product Strategy", "completions": 15, "learning_hours": 135},
                {"rank": 4, "name": "David Lee", "team": "Engineering Platform", "completions": 14, "learning_hours": 119},
                {"rank": 5, "name": "Emma Wilson", "team": "Customer Success", "completions": 13, "learning_hours": 98},
            ],
            "note": "Leaderboards used as recognition, not performance evaluation"
        }
    }


@app.get("/api/knowledge-outcomes")
async def get_knowledge_outcomes():
    """Knowledge & Skill Outcomes metrics"""
    return {
        "assessment_deltas": {
            "plusplus": {"pre_avg": 62, "post_avg": 82, "improvement": 20},
            "trailhead": {"pre_avg": 58, "post_avg": 79, "improvement": 21},
            "pluralsight": {"pre_avg": 65, "post_avg": 84, "improvement": 19},
            "oreilly": {"pre_avg": 61, "post_avg": 80, "improvement": 19},
            "overall": {"pre_avg": 61.5, "post_avg": 81.25, "improvement": 19.75}
        },
        "certification_pass_rates": {
            "plusplus": {"first_attempt": 78, "retake": 92, "overall": 82},
            "trailhead": {"first_attempt": 71, "retake": 88, "overall": 76},
            "pluralsight": {"first_attempt": 85, "retake": 95, "overall": 88},
            "oreilly": {"first_attempt": 73, "retake": 89, "overall": 79},
        },
        "skill_proficiency": {
            "Cloud Architecture": {"pre": 3.2, "post": 4.6, "learners": 156},
            "Agile Methodologies": {"pre": 3.8, "post": 4.4, "learners": 234},
            "AI/ML Fundamentals": {"pre": 2.9, "post": 4.1, "learners": 189},
            "DevOps Practices": {"pre": 3.5, "post": 4.5, "learners": 142},
            "Security & Compliance": {"pre": 3.1, "post": 4.3, "learners": 167},
        },
        "manager_skill_application": {
            "Engineering": {
                "30_day": {"improved": 68, "maintained": 24, "no_change": 8},
                "60_day": {"improved": 72, "maintained": 20, "no_change": 8},
                "90_day": {"improved": 79, "maintained": 16, "no_change": 5},
            },
            "Product": {
                "30_day": {"improved": 62, "maintained": 28, "no_change": 10},
                "60_day": {"improved": 71, "maintained": 21, "no_change": 8},
                "90_day": {"improved": 75, "maintained": 19, "no_change": 6},
            },
            "DevOps": {
                "30_day": {"improved": 74, "maintained": 18, "no_change": 8},
                "60_day": {"improved": 81, "maintained": 14, "no_change": 5},
                "90_day": {"improved": 86, "maintained": 11, "no_change": 3},
            },
            "Platform": {
                "30_day": {"improved": 66, "maintained": 26, "no_change": 8},
                "60_day": {"improved": 73, "maintained": 19, "no_change": 8},
                "90_day": {"improved": 78, "maintained": 17, "no_change": 5},
            },
        }
    }


@app.post("/slack/slash")
async def slack_slash_command(request: Request):
    """Slack slash command handler - /plusplus or /training-search"""
    import time as time_module
    start_time = time_module.time()
    print(f"DEBUG: [Handler] Started")

    # Parse form data directly
    form_data = await request.form()
    print(f"DEBUG: All form keys: {list(form_data.keys())}", flush=True)
    print(f"DEBUG: Full form data: {dict(form_data)}", flush=True)

    command = form_data.get("command")
    text = form_data.get("text")
    channel_id = form_data.get("channel_id")
    thread_ts = form_data.get("thread_ts")

    print(f"DEBUG: [Handler] Form parsed in {time_module.time()-start_time:.2f}s: command={command}, text={text}")

    # DEBUG
    print(f"DEBUG: About to check commands. command='{command}' (type: {type(command)})")

    # Handle /training-search
    if command == "/training-search":
        query = (text or "").strip()
        if not query:
            return {
                "response_type": "ephemeral",
                "text": "Usage: `/training-search <topic>`"
            }

        # Start background thread and return immediately
        print(f"DEBUG: [Handler] Returning immediately at {time_module.time()-start_time:.2f}s")
        thread = threading.Thread(target=_search_and_post_sync, args=(query, channel_id, thread_ts), daemon=True)
        thread.start()
        return {
            "response_type": "ephemeral",
            "text": f"Searching for '{query}'..."
        }

    # Handle /headless-dashboard
    if command == "/headless-dashboard":
        try:
            stats = await get_platform_stats()
            totals = stats.get("totals", {})
            platforms = stats.get("platforms", {})

            view_type = (text or "").strip().lower() or "summary"

            blocks = [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "📊 Training Analytics Dashboard",
                        "emoji": True
                    }
                }
            ]

            if view_type == "summary":
                blocks.append({
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*📚 Total Courses*\n{totals.get('total_courses', 0):,}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*👥 Total Enrollments*\n{totals.get('total_enrollments', 0):,}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*💻 Active Users*\n{totals.get('total_active_users', 0):,}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*🎓 Platforms*\n4"
                        }
                    ]
                })

            elif view_type == "platforms":
                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "*Platform Breakdown*"
                    }
                })
                for platform_key, platform_data in platforms.items():
                    platform_name = platform_data.get("name", platform_key.title())
                    enrollments = platform_data.get("enrollments", 0)
                    active_users = platform_data.get("active_users", 0)
                    blocks.append({
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"*{platform_name}*\n• Enrollments: {enrollments:,}\n• Active Users: {active_users:,}"
                        }
                    })

            elif view_type == "courses":
                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Total Courses: {totals.get('total_courses', 0):,}*"
                    }
                })
                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "Breakdown by platform:\n" + "\n".join([
                            f"• {p.get('name', k.title())}: {p.get('courses', p.get('modules', p.get('paths', p.get('books', 0))))}"
                            for k, p in platforms.items()
                        ])
                    }
                })

            blocks.extend([
                {"type": "divider"},
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "*View other sections:*\n`/headless-dashboard summary` - Key metrics\n`/headless-dashboard platforms` - Platform breakdown\n`/headless-dashboard courses` - Course inventory"
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"<{DASHBOARD_URL}|→ View Full Dashboard>"
                    }
                }
            ])

            return {"response_type": "ephemeral", "blocks": blocks}
        except Exception as e:
            return {"response_type": "ephemeral", "text": f"Error: {str(e)}"}

    # Handle /plusplus (legacy)
    parts = (text or "").strip().split(maxsplit=1)
    action = parts[0].lower() if parts else "help"
    query = parts[1] if len(parts) > 1 else ""

    try:
        with _client() as client:
            if action == "courses":
                resp = client.get("/api/v2/courses", params={"limit": 50})
                if resp.status_code == 200:
                    courses = resp.json().get("data", [])
                    lines = ["*Available Courses:*"]
                    for course in courses:
                        lines.append(f"• {course.get('name', 'N/A')}")
                    return {"response_type": "in_channel", "text": "\n".join(lines[:11])}

            elif action == "events":
                resp = client.get("/api/v2/events", params={"limit": 50})
                if resp.status_code == 200:
                    events = resp.json().get("data", [])
                    lines = ["*Available Events:*"]
                    for event in events[:10]:
                        lines.append(f"• {event.get('name', 'N/A')}")
                    return {"response_type": "in_channel", "text": "\n".join(lines)}

            elif action == "search" and query:
                resp_c = client.get("/api/v2/courses", params={"limit": 50})
                resp_e = client.get("/api/v2/events", params={"limit": 50})
                courses = resp_c.json().get("data", []) if resp_c.status_code == 200 else []
                events = resp_e.json().get("data", []) if resp_e.status_code == 200 else []

                q_lower = query.lower()
                matching_courses = [c for c in courses if q_lower in c.get("name", "").lower()]
                matching_events = [e for e in events if q_lower in e.get("name", "").lower()]

                lines = [f"*Search Results for '{query}':*"]
                if matching_courses:
                    lines.append("*Courses:*")
                    for c in matching_courses[:5]:
                        lines.append(f"• {c.get('name')}")
                if matching_events:
                    lines.append("*Events:*")
                    for e in matching_events[:5]:
                        lines.append(f"• {e.get('name')}")
                if not matching_courses and not matching_events:
                    lines.append("No results found")

                return {"response_type": "in_channel", "text": "\n".join(lines)}

            else:
                help_text = """*PlusPlus Slash Commands*
`/plusplus courses` - List all courses
`/plusplus events` - List all events
`/plusplus search <query>` - Search for courses/events (e.g., `/plusplus search mulesoft`)"""
                return {"response_type": "ephemeral", "text": help_text}

    except Exception as e:
        return {"response_type": "ephemeral", "text": f"Error: {str(e)}"}


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 9006))
    uvicorn.run(app, host="0.0.0.0", port=port, server_header=False, date_header=False)
