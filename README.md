# Instagram Gemini Bot

A FastAPI webhook that connects an Instagram group chat to Google Gemini. The bot listens for @mentions in a single target thread, enforces a cooldown between AI responses, blocks image-generation requests, and replies in Turkish.

---

## Quick Start

```bash
# 1. Clone and enter the project
cd FIproject

# 2. Create a virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS / Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Copy and fill in your environment variables
copy .env.example .env       # Windows
# cp .env.example .env       # macOS / Linux

# 5. Run the server
uvicorn main:app --host 0.0.0.0 --port 8000
```

---

## Environment Variables

| Variable | Description |
|---|---|
| `IG_ACCESS_TOKEN` | Instagram page access token with `instagram_manage_messages` permission |
| `VERIFY_TOKEN` | Arbitrary string you set in the Meta webhook configuration |
| `GEMINI_API_KEY` | API key from [Google AI Studio](https://aistudio.google.com/apikey) |
| `TARGET_THREAD_ID` | The group-chat thread ID the bot should respond in |
| `BOT_USERNAME` | The bot's Instagram username (without `@`) |
| `COOLDOWN_SECONDS` | Seconds between AI responses (default `300` = 5 min) |

---

## How to Find the Instagram Thread ID

There is no direct "copy thread ID" button in the Instagram UI. Use one of these approaches:

### Option A — Read it from the Webhook Payload (Recommended)

1. Deploy the bot with `TARGET_THREAD_ID` set to any placeholder value.
2. Send a message in the target group chat that mentions the bot.
3. Check your server logs — the incoming webhook payload contains `recipient.id`, which is the thread ID.
4. Copy that value, set it as `TARGET_THREAD_ID` in your `.env`, and restart the server.

### Option B — Instagram Graph API Explorer

1. Go to the [Meta Graph API Explorer](https://developers.facebook.com/tools/explorer/).
2. Select your app and use the page token that has `instagram_manage_messages`.
3. Call `GET /me/conversations?platform=instagram` to list recent threads.
4. Identify your group chat and copy its `id` field.

---

## Deploying

### Render (Recommended — Free Tier Available)

1. Push this repo to GitHub.
2. Create a new **Web Service** on [render.com](https://render.com).
3. Set the **Build Command** to `pip install -r requirements.txt`.
4. Set the **Start Command** to `uvicorn main:app --host 0.0.0.0 --port $PORT`.
5. Add all environment variables from `.env` in the Render dashboard.
6. Copy the generated URL (e.g. `https://your-app.onrender.com`) and set the webhook callback URL in Meta App Dashboard to `https://your-app.onrender.com/webhook`.

### Railway / Fly.io

Same general flow — push repo, set env vars, point Meta webhook to `https://<your-domain>/webhook`.

### Local Development with ngrok

```bash
# Terminal 1: run the server
uvicorn main:app --host 0.0.0.0 --port 8000

# Terminal 2: expose it
ngrok http 8000
```

Use the ngrok HTTPS URL as your webhook callback in the Meta App Dashboard.

---

## Meta App Dashboard Webhook Setup

1. Go to [Meta for Developers](https://developers.facebook.com/) → your app → **Webhooks**.
2. Subscribe to the **Instagram** product, event type **messages**.
3. Set **Callback URL** to `https://<your-domain>/webhook`.
4. Set **Verify Token** to the same value as `VERIFY_TOKEN` in your `.env`.
5. Click **Verify and Save**.

---

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/webhook` | Meta webhook verification (hub.challenge handshake) |
| `POST` | `/webhook` | Receives incoming Instagram messages |
| `GET` | `/health` | Health check + remaining cooldown |
