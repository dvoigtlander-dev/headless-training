from flask import Flask, request, jsonify
import os
import requests
import time

app = Flask(__name__)

FASTAPI_BASE = "http://localhost:8006"


@app.route('/search-training', methods=['POST'])
def search_training():
    """Proxy slash command to FastAPI"""
    try:
        start = time.time()

        # Forward to FastAPI slash endpoint with Slack headers
        headers = {}
        if 'X-Slack-Request-Timestamp' in request.headers:
            headers['X-Slack-Request-Timestamp'] = request.headers['X-Slack-Request-Timestamp']
        if 'X-Slack-Signature' in request.headers:
            headers['X-Slack-Signature'] = request.headers['X-Slack-Signature']

        print(f"DEBUG: [Flask] Proxying to FastAPI at {time.time()-start:.2f}s")

        resp = requests.post(
            f"{FASTAPI_BASE}/slack/slash",
            data=request.form,
            headers=headers,
            timeout=3
        )

        print(f"DEBUG: [Flask] Got response at {time.time()-start:.2f}s, status={resp.status_code}")

        return resp.json(), resp.status_code
    except Exception as e:
        import traceback
        print(f"ERROR: [Flask] {e}")
        print(traceback.format_exc())
        return {'error': str(e)}, 500


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'ok'})


@app.route('/slack/events', methods=['POST'])
def slack_events():
    """Proxy to FastAPI"""
    try:
        resp = requests.post(
            f"{FASTAPI_BASE}/slack/events",
            json=request.get_json(),
            timeout=5
        )
        return resp.json(), resp.status_code
    except Exception as e:
        return {'error': str(e)}, 500


if __name__ == '__main__':
    import sys
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 5001
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
