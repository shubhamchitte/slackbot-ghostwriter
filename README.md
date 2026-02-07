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

1. **Create Slack App**
   - Go to [api.slack.com/apps](https://api.slack.com/apps) → **Create New App** → **From scratch**
   - Name it (e.g., "Ghostwriter Bot"), select your workspace

2. **Enable Socket Mode** (so bot runs locally without a server)
   - Go to **Settings** → **Socket Mode** → Toggle **ON**
   - Click **Generate Token** → Name it "socket_token" → Generate
   - **Copy the App-Level Token** (starts with `xapp-`) ← You'll need this

3. **Add Permissions**
   - Go to **OAuth & Permissions** → Scroll to **Bot Token Scopes**
   - Click **Add an OAuth Scope** and add these 4 scopes:
     - `channels:history` (read messages)
     - `channels:read` (see channel names)
     - `chat:write` (send messages)
     - `commands` (slash commands)

4. **Install to Workspace**
   - At top of **OAuth & Permissions** page → **Install to Workspace** → Allow
   - **Copy the Bot User OAuth Token** (starts with `xoxb-`) ← You'll need this

5. **Enable Events**
   - Go to **Event Subscriptions** → Toggle **ON**
   - Under **Subscribe to bot events**, add: `message.channels`
   - **Save Changes**

### 2. Get Gemini API Key

- Visit [aistudio.google.com/apikey](https://aistudio.google.com/app/apikey)
- Click **Create API Key** → Copy it

### 3. Install Dependencies

```bash
# Navigate to project
cd slackbot-ghostwriter

# Install Python packages
pip install -r requirements.txt
```

### 4. Configure Environment Variables

**IMPORTANT: Do this before running the bot!**

```bash
# Copy the template
cp .env.example .env

# Edit the file
nano .env  # or use any text editor
```

**Paste your 3 tokens in `.env`:**

```bash
SLACK_BOT_TOKEN=xoxb-YOUR-BOT-TOKEN-HERE
SLACK_APP_TOKEN=xapp-YOUR-APP-TOKEN-HERE
GEMINI_API_KEY=YOUR-GEMINI-KEY-HERE

# Keep defaults for testing (or customize)
BUFFER_TIME_WINDOW_MINUTES=30
BUFFER_MIN_MESSAGES=3
MIN_SIGNAL_SCORE=0.6
```

Save and close the file.

### 5. Run the Bot

```bash
python main.py
```

You should see: `⚡️ Bolt app is running!`

### 6. Invite Bot to Channel

In your Slack channel: `/invite @Ghostwriter Bot`

---

## Demo

> [**Demo Link**](https://drive.google.com/file/d/12wPJ4K7SdCzxrhJRKh5KIICIO3jRbqtR/view?usp=sharing)

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
