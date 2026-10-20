# Slack Training Search Backend Setup

## Step 1: Install Dependencies

```bash
cd C:\Users\dvoigtlander\claude\Headless_Training
pip install -r requirements.txt
```

## Step 2: Create `.env` (Optional)

Create a `.env` file in this directory if you need to set the port:

```
PORT=5000
```

## Step 3: Run the Backend Locally

```bash
python app.py
```

You should see:
```
 * Running on http://127.0.0.1:5000
```

## Step 4: Expose to the Internet with ngrok

In a **new terminal**, install and run ngrok:

```bash
# Install ngrok (one-time)
# Download from https://ngrok.com/download or: brew install ngrok (Mac) / choco install ngrok (Windows)

# Start the tunnel
ngrok http 5000
```

You'll see output like:
```
Forwarding    https://abc123def456.ngrok.io -> http://127.0.0.1:5000
```

**Copy the HTTPS URL** — you'll need it next.

## Step 5: Update Slack Slash Command

1. Go to your Slack app settings
2. Navigate to **Slash Commands**
3. Click **Edit** on `/search-training`
4. Set **Request URL** to: `https://your-ngrok-url.ngrok.io/search-training`
   - Replace `your-ngrok-url` with the URL from ngrok
   - **Example:** `https://abc123def456.ngrok.io/search-training`
5. Click **Save**

## Step 6: Test in Slack

In your Slack workspace, type:

```
/search-training machine learning
```

The bot will search across Pluralsight, PlusPlus, O'Reilly, and Trailhead, then post results to the channel.

---

## Troubleshooting

**"Command not found" error in Slack:**
- Make sure the **Request URL** is correct and includes the full path: `/search-training`
- ngrok tunnel might have timed out — restart it and update the URL

**"Search failed" in Slack:**
- Check your terminal where `python app.py` is running — look for error messages
- Verify the `slack-training-search` skill exists: `claude skill slack-training-search "test"`

**Backend crashes:**
- Make sure Flask is installed: `pip install Flask`
- Check that port 5000 is not already in use

---

## Keeping it Running

**For local testing:** Keep both `python app.py` and `ngrok http 5000` running in separate terminals.

**For production:** Deploy to a service like:
- Heroku (free tier available)
- AWS Lambda
- Google Cloud Run
- Replit

(Let me know if you need deployment instructions for any of these.)
