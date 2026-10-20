# PlusPlus API Usage Guide

A comprehensive HTTP API for accessing the Salesforce PlusPlus training catalog, integrated with Trailhead, Pluralsight, and O'Reilly content sources.

## Overview

The PlusPlus API is a FastAPI server that:
- Proxies requests to the Salesforce PlusPlus training platform
- Searches across multiple training sources (PlusPlus, Trailhead, Pluralsight, O'Reilly)
- Provides Slack integration via `/plusplus` slash commands
- Handles authentication and request validation

---

## Getting Started

### Prerequisites
- Python 3.7+
- pip
- Valid PlusPlus API key

### Installation

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set environment variables**
   ```bash
   export PLUSPLUS_API_KEY="your-api-key-here"
   export PORT=8000
   ```

3. **Start the server**
   ```bash
   python main.py
   ```

   The server runs on `http://localhost:8000` by default.

### Interactive Documentation

Once running, access:
- **Swagger UI (OpenAPI docs)**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

---

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `PLUSPLUS_API_KEY` | ✅ Yes | - | API key for PlusPlus platform |
| `PLUSPLUS_BASE_URL` | No | `https://sfdc-bt.plusplus.app` | PlusPlus API endpoint |
| `PLUSPLUS_API_AUTH_KEY` | No | - | Optional Bearer token for request authentication |
| `SLACK_SIGNING_SECRET` | No | - | Slack signing secret for validating slash commands |
| `TRAILHEAD_MCP_URL` | No | `https://mcp.trailhead.salesforce.com/mcp` | Trailhead MCP endpoint |
| `PLURALSIGHT_MCP_URL` | No | `https://mcp.pluralsight.com/mcp` | Pluralsight MCP endpoint |
| `OREILLY_MCP_URL` | No | `https://api.oreilly.com/api/search/v1/mcp` | O'Reilly MCP endpoint |
| `OREILLY_MCP_TOKEN` | No | - | Bearer token for O'Reilly API |
| `PORT` | No | `8000` | Server port |

---

## API Endpoints

### 1. Health Check

**GET** `/health`

Check if the API is running.

**Response:**
```json
{
  "status": "ok",
  "service": "plusplus-api"
}
```

**Example:**
```bash
curl http://localhost:8000/health
```

---

### 2. Get All Courses

**GET** `/api/courses`

Retrieve all available courses from the PlusPlus catalog.

**Query Parameters:**
- `limit` (integer, 1-200, default: 100) - Number of results
- `offset` (integer, default: 0) - Pagination offset

**Headers:**
- `Authorization` (optional) - `Bearer {PLUSPLUS_API_AUTH_KEY}` if authentication is enabled

**Response:**
```json
{
  "data": [
    {
      "id": "course-123",
      "name": "MuleSoft Fundamentals",
      "description": "Learn the basics of MuleSoft integration",
      "status": "active",
      "url": "https://..."
    }
  ]
}
```

**Example:**
```bash
# Get first 50 courses
curl "http://localhost:8000/api/courses?limit=50&offset=0"

# With authentication
curl -H "Authorization: Bearer your-auth-key" http://localhost:8000/api/courses
```

**Python:**
```python
import requests

response = requests.get("http://localhost:8000/api/courses", params={"limit": 50})
courses = response.json()["data"]
for course in courses:
    print(f"{course['name']} - {course['status']}")
```

---

### 3. Get All Events

**GET** `/api/events`

Retrieve all upcoming training events and sessions.

**Query Parameters:**
- `limit` (integer, 1-200, default: 100)
- `offset` (integer, default: 0)

**Headers:**
- `Authorization` (optional) - Bearer token if enabled

**Response:**
```json
{
  "data": [
    {
      "id": "event-456",
      "name": "MuleSoft Training - Chicago",
      "description": "In-person MuleSoft training",
      "status": "active",
      "date": "2026-09-15",
      "url": "https://..."
    }
  ]
}
```

**Example:**
```bash
curl "http://localhost:8000/api/events?limit=25"
```

---

### 4. Get User Enrollments

**GET** `/api/enrollments`

Retrieve courses the current user is enrolled in.

**Query Parameters:**
- `limit` (integer, 1-200, default: 100)
- `offset` (integer, default: 0)

**Headers:**
- `Authorization` (optional)

**Response:**
```json
{
  "data": [
    {
      "id": "enrollment-789",
      "course_id": "course-123",
      "course_name": "MuleSoft Fundamentals",
      "status": "in-progress",
      "progress": 65,
      "enrolled_date": "2026-08-01"
    }
  ]
}
```

**Example:**
```bash
curl http://localhost:8000/api/enrollments
```

---

### 5. Get User Assignments

**GET** `/api/assignments`

Retrieve training assignments for the current user.

**Query Parameters:**
- `limit` (integer, 1-200, default: 100)
- `offset` (integer, default: 0)

**Headers:**
- `Authorization` (optional)

**Response:**
```json
{
  "data": [
    {
      "id": "assign-101",
      "course_name": "Sales Cloud Advanced",
      "assigned_by": "manager@salesforce.com",
      "due_date": "2026-09-30",
      "status": "pending"
    }
  ]
}
```

**Example:**
```bash
curl http://localhost:8000/api/assignments
```

---

### 6. Search Courses & Events

**GET** `/api/search`

Search for courses and events by keyword within the PlusPlus catalog.

**Query Parameters:**
- `q` (string, required) - Search query
- `limit` (integer, 1-200, default: 50) - Max results per category
- `Authorization` (optional) - Bearer token

**Response:**
```json
{
  "query": "mulesoft",
  "courses": [
    {
      "id": "course-123",
      "name": "MuleSoft Fundamentals",
      "description": "...",
      "status": "active"
    }
  ],
  "events": [
    {
      "id": "event-456",
      "name": "MuleSoft Training - Chicago",
      "date": "2026-09-15"
    }
  ],
  "total": 5
}
```

**Example:**
```bash
# Search for MuleSoft trainings
curl "http://localhost:8000/api/search?q=mulesoft"

# Search with custom limit
curl "http://localhost:8000/api/search?q=agentcore&limit=100"
```

**Python:**
```python
import requests

response = requests.get("http://localhost:8000/api/search", params={"q": "mulesoft"})
results = response.json()
print(f"Found {results['total']} results")
print(f"Courses: {len(results['courses'])}")
print(f"Events: {len(results['events'])}")
```

**JavaScript:**
```javascript
const response = await fetch("http://localhost:8000/api/search?q=mulesoft");
const data = await response.json();
console.log(`Total results: ${data.total}`);
```

---

### 7. Unified Search (Multi-Platform)

**GET** `/api/unified-search`

Search across **all training platforms** (PlusPlus, Trailhead, Pluralsight, O'Reilly) simultaneously.

**Query Parameters:**
- `q` (string, required) - Search query
- `limit` (integer, 1-50, default: 10) - Results per source
- `sources` (string, default: "all") - Comma-separated sources to search:
  - `all` - Search all platforms
  - `trailhead` - Salesforce Trailhead only
  - `pluralsight` - Pluralsight only
  - `oreilly` - O'Reilly only
  - `plusplus` - PlusPlus only
- `Authorization` (optional) - Bearer token

**Response:**
```json
{
  "query": "mulesoft",
  "sources": {
    "trailhead": [
      {
        "source": "trailhead",
        "title": "MuleSoft Trail",
        "url": "https://trailhead.salesforce.com/...",
        "type": "trail",
        "points": 1200,
        "minutes": 480
      }
    ],
    "pluralsight": [
      {
        "source": "pluralsight",
        "title": "MuleSoft Fundamentals",
        "url": "https://pluralsight.com/...",
        "type": "course",
        "duration": "4 hours"
      }
    ],
    "oreilly": [
      {
        "source": "oreilly",
        "title": "MuleSoft Handbook",
        "url": "https://oreilly.com/...",
        "type": "book",
        "authors": ["John Doe"],
        "publisher": "O'Reilly Media"
      }
    ],
    "plusplus": [
      {
        "source": "plusplus",
        "title": "MuleSoft Training - Chicago",
        "url": "https://plusplus.app/...",
        "type": "event"
      }
    ]
  },
  "total": 12
}
```

**Examples:**

```bash
# Search all platforms
curl "http://localhost:8000/api/unified-search?q=mulesoft"

# Search specific platforms
curl "http://localhost:8000/api/unified-search?q=mulesoft&sources=trailhead,pluralsight"

# Increase results limit
curl "http://localhost:8000/api/unified-search?q=agentcore&limit=25&sources=all"
```

**Python:**
```python
import requests

response = requests.get(
    "http://localhost:8000/api/unified-search",
    params={
        "q": "mulesoft",
        "sources": "trailhead,pluralsight",
        "limit": 15
    }
)

data = response.json()
for source, items in data["sources"].items():
    print(f"\n{source.upper()}:")
    for item in items:
        print(f"  - {item['title']}")
```

---

## Authentication

### Optional Authentication

To require Bearer token authentication on requests:

1. **Set the auth key:**
   ```bash
   export PLUSPLUS_API_AUTH_KEY="your-secret-key-here"
   ```

2. **Include header in requests:**
   ```bash
   curl -H "Authorization: Bearer your-secret-key-here" \
     http://localhost:8000/api/courses
   ```

3. **Python:**
   ```python
   import requests

   headers = {"Authorization": "Bearer your-secret-key-here"}
   response = requests.get("http://localhost:8000/api/courses", headers=headers)
   ```

If `PLUSPLUS_API_AUTH_KEY` is not set, authentication is disabled and all requests are public.

---

## Slack Integration

### Setup

See `SLACK_SETUP.md` for complete Slack app configuration instructions.

**Quick setup:**
1. Create a Slack app at https://api.slack.com/apps
2. Add slash command `/plusplus` pointing to `http://your-server:8000/slack/slash`
3. Copy the signing secret to `SLACK_SIGNING_SECRET` env var
4. Install app to workspace
5. Start the API server

### Slash Commands

Once installed, use `/plusplus` in any Slack channel:

```
/plusplus courses              # List all courses
/plusplus events               # List all upcoming events
/plusplus search mulesoft      # Search for "mulesoft" courses/events
```

**Examples:**
```
/plusplus search agentcore     # Search for AgentCore trainings
/plusplus search salescloud    # Search for Sales Cloud courses
/plusplus courses              # View full course catalog
```

---

## Deployment

### Docker

**Build image:**
```bash
docker build -t plusplus-api .
```

**Run container:**
```bash
docker run -e PLUSPLUS_API_KEY=your_key \
  -e SLACK_SIGNING_SECRET=your_secret \
  -p 8000:8000 \
  plusplus-api
```

### Google Cloud Run

```bash
gcloud run deploy plusplus-api \
  --source . \
  --set-env-vars PLUSPLUS_API_KEY=your_key,SLACK_SIGNING_SECRET=your_secret \
  --platform managed \
  --region us-central1
```

### Kubernetes

1. Create secret:
   ```bash
   kubectl create secret generic plusplus-secrets \
     --from-literal=PLUSPLUS_API_KEY=your_key \
     --from-literal=SLACK_SIGNING_SECRET=your_secret
   ```

2. Deploy using `k8s-deployment.yaml`:
   ```bash
   kubectl apply -f k8s-deployment.yaml
   ```

---

## Common Use Cases

### 1. List All MuleSoft Trainings

```python
import requests

response = requests.get("http://localhost:8000/api/search?q=mulesoft")
data = response.json()

print(f"Found {data['total']} results")
for course in data['courses']:
    print(f"Course: {course['name']}")
for event in data['events']:
    print(f"Event: {event['name']}")
```

### 2. Find Training Across All Platforms

```bash
curl "http://localhost:8000/api/unified-search?q=salescloud"
```

### 3. Get User's Current Enrollments

```python
response = requests.get("http://localhost:8000/api/enrollments")
enrollments = response.json()["data"]

for enrollment in enrollments:
    print(f"{enrollment['course_name']}: {enrollment['progress']}% complete")
```

### 4. Check Pending Assignments

```bash
curl http://localhost:8000/api/assignments | jq '.data[] | select(.status=="pending")'
```

### 5. Paginate Through Courses

```python
import requests

all_courses = []
limit = 100
offset = 0

while True:
    response = requests.get(
        "http://localhost:8000/api/courses",
        params={"limit": limit, "offset": offset}
    )
    data = response.json()
    all_courses.extend(data["data"])
    
    if len(data["data"]) < limit:
        break
    
    offset += limit

print(f"Total courses: {len(all_courses)}")
```

---

## Error Handling

### Common HTTP Status Codes

| Status | Meaning | Example |
|--------|---------|---------|
| 200 | Success | Request completed |
| 401 | Unauthorized | Invalid/missing Bearer token |
| 400 | Bad Request | Invalid query parameters |
| 502 | Bad Gateway | PlusPlus API unreachable |
| 500 | Server Error | Internal API error |

### Handling Errors in Python

```python
import requests

try:
    response = requests.get("http://localhost:8000/api/courses")
    response.raise_for_status()  # Raise exception for HTTP errors
    data = response.json()
except requests.exceptions.HTTPError as e:
    print(f"HTTP Error: {e.response.status_code} - {e.response.text}")
except requests.exceptions.ConnectionError:
    print("Failed to connect to API")
```

---

## Performance Tips

1. **Use pagination** - Don't request all courses at once; use `limit` and `offset`
   ```bash
   curl "http://localhost:8000/api/courses?limit=50&offset=0"
   ```

2. **Specific searches** - Use `/api/search` instead of fetching all courses
   ```bash
   curl "http://localhost:8000/api/search?q=mulesoft"
   ```

3. **Cache results** - Store frequently accessed data to reduce API calls

4. **Parallel requests** - Use async for multiple requests
   ```python
   import asyncio
   import aiohttp
   
   async def fetch_all():
       async with aiohttp.ClientSession() as session:
           # Make multiple requests concurrently
           pass
   ```

---

## Troubleshooting

### Server Won't Start

**Error:** `ModuleNotFoundError: No module named 'fastapi'`

**Solution:**
```bash
pip install -r requirements.txt
```

### 502 Bad Gateway

**Problem:** The PlusPlus API is unreachable

**Solutions:**
- Check `PLUSPLUS_BASE_URL` is correct
- Verify `PLUSPLUS_API_KEY` is valid
- Ensure network connectivity to PlusPlus

### 401 Unauthorized

**Problem:** Bearer token authentication failed

**Solutions:**
- Verify header format: `Authorization: Bearer <token>`
- Check `PLUSPLUS_API_AUTH_KEY` matches exactly
- Ensure token is set and not empty

### Slack Command Doesn't Respond

**Problem:** `/plusplus` command fails silently

**Solutions:**
- Check server is running: `curl http://localhost:8000/health`
- Verify `SLACK_SIGNING_SECRET` is set correctly
- Ensure Request URL in Slack app matches your server
- Check firewall/networking allows Slack requests

---

## Support

For issues, check:
1. Server logs for error messages
2. Status at `/health` endpoint
3. Interactive docs at `/docs` for API schema
4. `SLACK_SETUP.md` for Slack-specific issues
