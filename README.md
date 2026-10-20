# PlusPlus API

Shared HTTP API for accessing Salesforce PlusPlus training catalog.

## Quick Start

### Local Development
```bash
pip install -r requirements.txt
PLUSPLUS_API_KEY=your_key python main.py
```

Runs on `http://localhost:8000`

### Interactive Docs
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## Endpoints

### `/api/courses`
Get all courses
```bash
curl http://localhost:8000/api/courses
```

### `/api/events`
Get all events/training sessions
```bash
curl http://localhost:8000/api/events
```

### `/api/enrollments`
Get user enrollments
```bash
curl http://localhost:8000/api/enrollments
```

### `/api/assignments`
Get user assignments
```bash
curl http://localhost:8000/api/assignments
```

### `/api/search`
Search across courses and events
```bash
curl "http://localhost:8000/api/search?q=mulesoft"
curl "http://localhost:8000/api/search?q=agentcore"
```

## Authentication (Optional)

Set `PLUSPLUS_API_AUTH_KEY` to require Bearer token auth:
```bash
export PLUSPLUS_API_AUTH_KEY=secret-key-here
python main.py
```

Then clients must include header:
```bash
curl -H "Authorization: Bearer secret-key-here" http://localhost:8000/api/courses
```

## Environment Variables

- `PLUSPLUS_BASE_URL` - PlusPlus API base URL (default: `https://sfdc-bt.plusplus.app`)
- `PLUSPLUS_API_KEY` - PlusPlus API key (required)
- `PLUSPLUS_API_AUTH_KEY` - Optional auth key to require on requests
- `PORT` - Server port (default: 8000)

## Deployment

### Docker
```bash
docker build -t plusplus-api .
docker run -e PLUSPLUS_API_KEY=your_key -p 8000:8000 plusplus-api
```

### Kubernetes
```bash
kubectl create secret generic plusplus-secrets \
  --from-literal=PLUSPLUS_API_KEY=your_key
kubectl apply -f k8s-deployment.yaml
```

### Cloud Run (Google Cloud)
```bash
gcloud run deploy plusplus-api \
  --source . \
  --set-env-vars PLUSPLUS_API_KEY=your_key \
  --platform managed
```

## Usage Examples

### Python
```python
import requests

base_url = "http://localhost:8000"
response = requests.get(f"{base_url}/api/search?q=mulesoft")
print(response.json())
```

### JavaScript/Node.js
```javascript
const response = await fetch("http://localhost:8000/api/events");
const data = await response.json();
console.log(data);
```

### Bash/curl
```bash
# Get all MuleSoft events
curl "http://localhost:8000/api/search?q=mulesoft"

# Get all AgentCore events
curl "http://localhost:8000/api/search?q=agentcore"

# Paginate courses
curl "http://localhost:8000/api/courses?limit=50&offset=0"
```

## Response Format

All endpoints return JSON. Courses and events follow PlusPlus API format:

```json
{
  "data": [
    {
      "id": "...",
      "name": "Course/Event Name",
      "description": "...",
      "status": "active",
      ...
    }
  ]
}
```

Search endpoint returns:
```json
{
  "query": "mulesoft",
  "courses": [...],
  "events": [...],
  "total": 5
}
```
