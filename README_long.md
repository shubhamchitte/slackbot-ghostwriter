# Digital Ghostwriter Slack Bot 🤖

AI-powered Slack bot that listens to your conversations and suggests polished content for X and LinkedIn.

---

## What It Does

- Listens to your Slack conversations passively
- Filters noise (scheduling talk, "ok cool", etc.)
- Identifies valuable insights worth sharing
- Suggests ready-to-post content for X and LinkedIn
- You approve/edit before posting

**30-minute conversation window** - Bot groups messages in 30-min windows. If silence > 30 min, it processes the conversation. [Configure this in `.env` if needed](#configuration)

---

## Quick Setup (15 Minutes)

### 1. Get Slack Tokens

1. Go to [api.slack.com/apps](https://api.slack.com/apps) → **Create New App** → **From scratch**
2. Name it (e.g., "Ghostwriter Bot"), select your workspace
3. **Enable Socket Mode** (Settings → Socket Mode → toggle ON)
   - Copy the **App-Level Token** (starts with `xapp-`)
4. Go to **OAuth & Permissions** → **Scopes** → Add:
   - `channels:history`, `channels:read`, `chat:write`, `commands`
5. **Install App to Workspace** → Copy **Bot Token** (starts with `xoxb-`)

### 2. Get Gemini API Key

- Visit [aistudio.google.com/apikey](https://aistudio.google.com/app/apikey)
- Click **Create API Key** → Copy it

### 3. Install & Run

```bash
# Clone/navigate to project
cd slackbot-ghostwriter

# Install dependencies
pip install -r requirements.txt

# Configure tokens
cp .env.example .env
nano .env  # Paste your 3 tokens

# Run the bot
python main.py
```

### 4. Invite Bot to Channel

In your Slack channel: `/invite @Ghostwriter Bot`

---

## Demo

> **[ADD YOUR VIDEO DEMO LINK HERE]**

---

## Configuration

Edit `.env` to customize behavior:

```bash
# 30-minute conversation window (default)
BUFFER_TIME_WINDOW_MINUTES=30

# Minimum messages needed before processing
BUFFER_MIN_MESSAGES=3

# Quality threshold (0.0-1.0)
MIN_SIGNAL_SCORE=0.6
```

---

## Usage

Just chat naturally in Slack. The bot will:
- ✅ Process conversations after 30 minutes of silence
- ✅ Send interactive cards with suggested content
- ✅ Let you **Edit**, **Approve**, or **Dismiss** suggestions

**Force processing now:** `/ghostwrite now`

---

## What Gets Filtered (Won't Generate Content)

- ❌ Scheduling talk ("let's meet at 3pm")
- ❌ Short replies ("ok", "cool", "👍")
- ❌ Code blocks without context
- ❌ Messages under 10 words

---

## Troubleshooting

**Bot not responding?**
- Invite it to channel: `/invite @Ghostwriter Bot`
- Check logs for errors

**"Missing environment variables" error?**
- Verify `.env` file exists (copy from `.env.example`)
- Check all 3 tokens are filled in

**Messages being ignored?**
- Check conversation quality (needs real insights, not chit-chat)
- Review logs for filtering reasons

---

## Tech Stack

- **Python 3.8+**
- **Slack SDK** (Socket Mode - runs locally, no server)
- **Google Gemini Flash** (free AI API)
- **SQLite** (local storage)

---

## License

MIT
