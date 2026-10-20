# PlusPlus API Setup Guide

## Overview

PlusPlus is Salesforce's unified training catalog platform. This guide covers how to set up and use the PlusPlus API for accessing courses, events, and training content.

## Prerequisites

- PlusPlus account access
- API key (contact your PlusPlus administrator)
- Base URL for your PlusPlus instance
- Python 3.8+ (if using the Python examples)

## Getting Started

### 1. Obtain API Credentials

Contact your PlusPlus administrator to get:
- **API Key**: Authentication token for API requests
- **Base URL**: Your PlusPlus instance URL (typically `https://sfdc-bt.plusplus.app` or your custom domain)

### 2. Environment Configuration

Create a `.env` file with your credentials:

```env
PLUSPLUS_API_KEY=your_api_key_here
PLUSPLUS_BASE_URL=https://sfdc-bt.plusplus.app
```

Load the environment variables in your application:

```python
import os
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.environ.get("PLUSPLUS_BASE_URL", "https://sfdc-bt.plusplus.app")
API_KEY = os.environ.get("PLUSPLUS_API_KEY")

if not API_KEY:
    raise ValueError("PLUSPLUS_API_KEY environment variable is required")
```

## API Authentication

PlusPlus uses Bearer token authentication. Include the API key in the Authorization header:

```
Authorization: Bearer {API_KEY}
```

### Python Example with httpx

```python
import httpx

BASE_URL = "https://sfdc-bt.plusplus.app"
API_KEY = "your_api_key"

def _client():
    return httpx.Client(
        base_url=BASE_URL,
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        },
        timeout=30
    )

with _client() as client:
    response = client.get("/api/v2/courses", params={"limit": 10})
    courses = response.json()
```

## API Endpoints

### Get All Courses

**Endpoint:** `GET /api/v2/courses`

**Parameters:**
- `limit` (int): Maximum results to return (default: 50, max: 100)
- `offset` (int): Pagination offset (default: 0)

**Response:**
```json
{
  "data": [
    {
      "public_id": "uuid",
      "name": "Course Name",
      "description": "Course description...",
      "content_type": "course",
      "tags": [
        {"name": "tag1"},
        {"name": "tag2"}
      ]
    }
  ]
}
```

**Example:**
```python
with _client() as client:
    resp = client.get("/api/v2/courses", params={"limit": 50})
    courses = resp.json().get("data", [])
    for course in courses:
        print(f"{course['name']} - {course['description'][:100]}")
```

### Get All Events

**Endpoint:** `GET /api/v2/events`

**Parameters:**
- `limit` (int): Maximum results to return (default: 50, max: 100)
- `offset` (int): Pagination offset (default: 0)

**Response:**
```json
{
  "data": [
    {
      "public_id": "uuid",
      "name": "Event Name",
      "description": "Event description...",
      "content_type": "event",
      "date": "2024-09-22",
      "time": "14:00"
    }
  ]
}
```

**Example:**
```python
with _client() as client:
    resp = client.get("/api/v2/events", params={"limit": 25})
    events = resp.json().get("data", [])
    for event in events:
        print(f"{event['name']} - {event['date']} at {event['time']}")
```

## Searching Content

PlusPlus doesn't provide a dedicated search endpoint. Instead, fetch all content and filter locally:

```python
def search_courses(query: str, limit: int = 10) -> list:
    """Search for courses by keyword"""
    try:
        with _client() as client:
            resp = client.get("/api/v2/courses", params={"limit": limit * 2})
            if resp.status_code == 200:
                courses = resp.json().get("data", [])
                q_lower = query.lower()
                matching = []
                
                for course in courses:
                    name = (course.get("name", "") or "").lower()
                    desc = (course.get("description", "") or "").lower()
                    tags = " ".join([t.get("name", "") for t in course.get("tags", [])]).lower()
                    
                    if q_lower in name or q_lower in desc or q_lower in tags:
                        matching.append({
                            "title": course.get("name"),
                            "description": course.get("description"),
                            "tags": [t.get("name") for t in course.get("tags", [])]
                        })
                
                return matching[:limit]
    except Exception as e:
        print(f"Search error: {e}")
    
    return []

# Usage
results = search_courses("python", limit=5)
for result in results:
    print(f"- {result['title']}")
```

## Response Field Reference

### Course Fields

| Field | Type | Description |
|-------|------|-------------|
| `public_id` | string | Unique identifier for the course |
| `name` | string | Course title |
| `description` | string | Course description (can be long) |
| `content_type` | string | Always "course" |
| `tags` | array | List of tags with `name` field |
| `duration` | string | Course length (e.g., "2 hours") |
| `level` | string | Skill level (e.g., "Beginner") |

### Event Fields

| Field | Type | Description |
|-------|------|-------------|
| `public_id` | string | Unique identifier for the event |
| `name` | string | Event title |
| `description` | string | Event description |
| `content_type` | string | Always "event" |
| `date` | string | Event date (YYYY-MM-DD format) |
| `time` | string | Event time (HH:MM format) |
| `location` | string | Event location |
| `capacity` | integer | Maximum attendees |

## Deep Linking

PlusPlus does not currently support deep linking to specific courses or events via public URLs. When displaying results, either:

1. **Link to search**: `https://your-plusplus.com?search={query}`
2. **Link to main catalog**: `https://your-plusplus.com`

Example:
```python
def get_plusplus_url(query: str) -> str:
    """Generate PlusPlus search URL"""
    return f"{BASE_URL}?search={query}"
```

## Error Handling

### Common HTTP Status Codes

| Status | Meaning | Action |
|--------|---------|--------|
| 200 | Success | Process response normally |
| 400 | Bad Request | Check parameters |
| 401 | Unauthorized | Verify API key |
| 403 | Forbidden | Check permissions |
| 429 | Rate Limited | Retry with backoff |
| 500 | Server Error | Retry later |

### Example Error Handling

```python
def fetch_courses_safe(limit: int = 50) -> dict:
    """Fetch courses with error handling"""
    try:
        with _client() as client:
            resp = client.get(
                "/api/v2/courses",
                params={"limit": limit},
                timeout=5
            )
            resp.raise_for_status()  # Raise on HTTP errors
            return resp.json()
    except httpx.HTTPStatusError as e:
        print(f"HTTP Error {e.response.status_code}: {e}")
        return {"data": [], "error": str(e)}
    except httpx.TimeoutException:
        print("Request timeout")
        return {"data": [], "error": "timeout"}
    except Exception as e:
        print(f"Unexpected error: {e}")
        return {"data": [], "error": str(e)}
```

## Performance Tips

### 1. Pagination

Always use pagination for large datasets:

```python
def fetch_all_courses(page_size: int = 100):
    """Fetch all courses with pagination"""
    offset = 0
    all_courses = []
    
    while True:
        with _client() as client:
            resp = client.get(
                "/api/v2/courses",
                params={"limit": page_size, "offset": offset}
            )
            if resp.status_code != 200:
                break
            
            courses = resp.json().get("data", [])
            if not courses:
                break
            
            all_courses.extend(courses)
            offset += page_size
    
    return all_courses
```

### 2. Caching

Cache results locally to reduce API calls:

```python
import json
from datetime import datetime, timedelta

CACHE_FILE = "plusplus_cache.json"
CACHE_TTL = timedelta(hours=1)

def get_cached_courses():
    """Get courses from cache if fresh"""
    try:
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, "r") as f:
                cache = json.load(f)
            
            cache_time = datetime.fromisoformat(cache.get("timestamp"))
            if datetime.now() - cache_time < CACHE_TTL:
                return cache.get("courses", [])
    except Exception:
        pass
    
    # Fetch fresh data
    with _client() as client:
        resp = client.get("/api/v2/courses", params={"limit": 100})
        courses = resp.json().get("data", [])
    
    # Save to cache
    with open(CACHE_FILE, "w") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "courses": courses
        }, f)
    
    return courses
```

### 3. Timeouts

Always set reasonable timeouts:

```python
# Set timeout per request
client.get("/api/v2/courses", timeout=5)

# Or set default timeout for all requests
client = httpx.Client(timeout=30)
```

## Integration Examples

### Slack Bot Integration

```python
from slack_sdk import WebClient

def post_course_to_slack(course: dict, channel: str):
    """Post a course to Slack"""
    slack_client = WebClient(token=SLACK_BOT_TOKEN)
    
    slack_client.chat_postMessage(
        channel=channel,
        blocks=[
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*{course['name']}*\n{course['description'][:200]}"
                }
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "View on PlusPlus"},
                        "url": f"{BASE_URL}?search={course['name']}"
                    }
                ]
            }
        ]
    )
```

### FastAPI Endpoint

```python
from fastapi import FastAPI, Query

app = FastAPI()

@app.get("/api/training/search")
async def search_training(q: str = Query(...), limit: int = Query(10, le=50)):
    """Search PlusPlus courses and events"""
    courses = search_courses(q, limit=limit)
    events = search_events(q, limit=limit)
    
    return {
        "query": q,
        "courses": courses,
        "events": events,
        "total": len(courses) + len(events)
    }
```

## Troubleshooting

### 401 Unauthorized

**Issue:** API key is invalid or expired

**Solution:**
- Verify API key in `.env` file
- Contact PlusPlus administrator for new key
- Check that Authorization header is set correctly

### 429 Rate Limited

**Issue:** Too many requests

**Solution:**
- Implement exponential backoff
- Cache results locally
- Reduce request frequency
- Contact administrator about rate limits

### Empty Results

**Issue:** Search returns no results

**Solution:**
- Verify query keywords are in course/event name or description
- Check that description field contains the search term
- Try broader search terms
- Verify API key has search permission

### Timeout Errors

**Issue:** Requests take too long

**Solution:**
- Increase timeout value
- Reduce limit parameter
- Check network connectivity
- Contact PlusPlus administrator about performance

## Security Best Practices

1. **Never commit API keys** - Use `.env` files with `.gitignore`
2. **Rotate keys regularly** - Request new keys periodically
3. **Limit scope** - Use API keys with minimal required permissions
4. **Use HTTPS only** - Always use secure connections
5. **Validate input** - Sanitize user search queries
6. **Log carefully** - Don't log sensitive data like API keys
7. **Monitor usage** - Track API calls for suspicious activity

## Support

For API issues or questions:
- Contact your PlusPlus administrator
- Check PlusPlus documentation portal
- Review API response status codes and error messages

## Version History

- **v1.0** (Sept 2024) - Initial API setup guide
