#!/bin/bash
# Headless Training Search - Daily Startup Script

set -e
cd "$(dirname "$0")"

echo "=== Headless Training Search Startup ==="
echo ""

# Kill any existing processes
echo "Cleaning up old processes..."
ps aux | grep "python.*main.py" | grep -v grep | awk '{print $2}' | xargs -r kill -9 2>/dev/null || true
ps aux | grep "streamlit" | grep -v grep | awk '{print $2}' | xargs -r kill -9 2>/dev/null || true
ps aux | grep "cloudflared" | grep -v grep | awk '{print $2}' | xargs -r kill -9 2>/dev/null || true
sleep 2

# Start FastAPI server
echo "Starting FastAPI server on port 8006..."
python main.py > main.log 2>&1 &
FASTAPI_PID=$!
echo "FastAPI PID: $FASTAPI_PID"

# Wait for FastAPI to be ready
echo "Waiting for FastAPI to be healthy..."
for i in {1..30}; do
  if curl -s http://localhost:8006/health > /dev/null 2>&1; then
    echo "✓ FastAPI is ready"
    break
  fi
  if [ $i -eq 30 ]; then
    echo "✗ FastAPI failed to start"
    exit 1
  fi
  sleep 1
done

# Start Streamlit dashboard
echo "Starting Streamlit dashboard on port 8501..."
streamlit run dashboard.py --server.port=8501 --logger.level=error > dashboard.log 2>&1 &
STREAMLIT_PID=$!
echo "Streamlit PID: $STREAMLIT_PID"

# Wait for dashboard to be ready
echo "Waiting for dashboard to be healthy..."
for i in {1..30}; do
  if curl -s http://localhost:8501 > /dev/null 2>&1; then
    echo "✓ Dashboard is ready"
    break
  fi
  sleep 1
done

# Start cloudflared tunnel for FastAPI
echo "Starting cloudflared tunnel for FastAPI..."
./cloudflared.exe tunnel --url http://localhost:9006 > cloudflared-api.log 2>&1 &
CLOUDFLARED_API_PID=$!
echo "Cloudflared API PID: $CLOUDFLARED_API_PID"

# Start cloudflared tunnel for Dashboard
echo "Starting cloudflared tunnel for Dashboard..."
./cloudflared.exe tunnel --url http://localhost:8501 > cloudflared-dashboard.log 2>&1 &
CLOUDFLARED_DASH_PID=$!
echo "Cloudflared Dashboard PID: $CLOUDFLARED_DASH_PID"

# Wait for tunnels to be ready and get URLs
echo "Waiting for tunnels to be ready..."
sleep 5
API_URL=$(grep "https://" cloudflared-api.log | head -1 | grep -o "https://[^ ]*" || echo "UNKNOWN")
DASH_URL=$(grep "https://" cloudflared-dashboard.log | head -1 | grep -o "https://[^ ]*" || echo "UNKNOWN")

echo ""
echo "=== ✓ Systems Ready ==="
echo ""
echo "Slack Request URL:"
echo "  $API_URL/slack/slash"
echo ""
echo "Dashboard:"
echo "  Local: http://localhost:8501"
echo "  Public: $DASH_URL"
echo ""
echo "FastAPI:"
echo "  Local: http://localhost:9006"
echo "  Public: $API_URL"
echo ""
echo "Use /training-search in Slack to search across all platforms"
echo ""
echo "Logs:"
echo "  - FastAPI: main.log"
echo "  - Dashboard: dashboard.log"
echo "  - Cloudflared API: cloudflared-api.log"
echo "  - Cloudflared Dashboard: cloudflared-dashboard.log"
echo "  - Background searches: thread.log"
echo ""
