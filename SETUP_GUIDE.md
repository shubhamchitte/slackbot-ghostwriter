# Digital Ghostwriter Slack Bot - Quick Setup Guide

Follow these steps to get your bot running in ~30 minutes!

## 📋 Prerequisites

- Python 3.8 or higher
- A Slack workspace where you have admin permissions
- Google account (for Gemini API key)

---

## Step 1: Create Slack App (5 minutes)

### 1.1 Create the App
1. Go to [api.slack.com/apps](https://api.slack.com/apps)
2. Click **"Create New App"**
3. Choose **"From scratch"**
4. Name it: `Ghostwriter Bot`
5. Select your workspace
6. Click **"Create App"**

### 1.2 Enable Socket Mode
1. In the left sidebar, click **"Socket Mode"**
2. Toggle **"Enable Socket Mode"** to ON
3. You'll be prompted to create an App-Level Token:
   - Token Name: `ghostwriter-socket`
   - Scope: `connections:write`
   - Click **"Generate"**
4. **Copy the token** (starts with `xapp-`) - you'll need this for `.env`

### 1.3 Add Bot Scopes
1. In the left sidebar, click **"OAuth & Permissions"**
2. Scroll to **"Scopes"** → **"Bot Token Scopes"**
3. Click **"Add an OAuth Scope"** and add these:
   - `channels:history` - Read message history
   - `channels:read` - View channel info
   - `chat:write` - Post messages
   - `commands` - Use slash commands

### 1.4 Install to Workspace
1. Scroll to top of **"OAuth & Permissions"** page
2. Click **"Install to Workspace"**
3. Click **"Allow"**
4. **Copy the "Bot User OAuth Token"** (starts with `xoxb-`) - you'll need this for `.env`

### 1.5 Add Slash Command
1. In the left sidebar, click **"Slash Commands"**
2. Click **"Create New Command"**
3. Fill in:
   - Command: `/ghostwrite`
   - Request URL: `https://example.com` (Socket Mode doesn't use this, but it's required)
   - Short Description: `Control the Ghostwriter bot`
   - Usage Hint: `now | stats`
4. Click **"Save"**

### 1.6 Subscribe to Events
1. In the left sidebar, click **"Event Subscriptions"**
2. Toggle **"Enable Events"** to ON
3. Under **"Subscribe to bot events"**, add:
   - `message.channels` - Listen to messages in channels
4. Click **"Save Changes"**

---

## Step 2: Get Google Gemini API Key (2 minutes)

1. Go to [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Sign in with your Google account
3. Click **"Get API Key"** or **"Create API Key"**
4. Select a Google Cloud project (or create a new one)
5. Click **"Create API key in existing project"**
6. **Copy the API key** - you'll need this for `.env`

> **Note**: Gemini Flash has a generous free tier (15 requests/min, 1M tokens/day)

---

## Step 3: Clone & Install (3 minutes)

### 3.1 Navigate to Project
```bash
cd /Users/shubh/Antigravity_apps/slackbot-ghostwriter
```

### 3.2 Install Dependencies
```bash
pip install -r requirements.txt
```

You should see:
```
Successfully installed slack-bolt-1.18.0 slack-sdk-3.23.0 python-dotenv-1.0.0 google-generativeai-0.3.0
```

---

## Step 4: Configure Environment (3 minutes)

### 4.1 Create .env File
```bash
cp .env.example .env
```

### 4.2 Edit .env
Open `.env` in your text editor and fill in the three tokens you copied:

```bash
# Slack Credentials (from Step 1)
SLACK_BOT_TOKEN=xoxb-your-bot-token-here
SLACK_APP_TOKEN=xapp-your-app-token-here

# Google Gemini API (from Step 2)
GEMINI_API_KEY=your-gemini-api-key-here

# Optional: Leave these as defaults for now
BUFFER_TIME_WINDOW_MINUTES=30
BUFFER_MIN_MESSAGES=3
MIN_SIGNAL_SCORE=0.6
MIN_MESSAGE_LENGTH=10
DB_PATH=data/ghostwriter.db
```

**Important**: Replace the placeholder values with your actual tokens!

---

## Step 5: Invite Bot to Channel (1 minute)

1. Open Slack
2. Go to your private channel (or create one for testing)
3. Type: `/invite @Ghostwriter Bot`
4. Press Enter

You should see: "added Ghostwriter Bot to this channel"

---

## Step 6: Run the Bot! (1 minute)

```bash
python main.py
```

You should see:
```
============================================================
🤖 Digital Ghostwriter Slack Bot
============================================================
2026-01-30 23:17:57 - __main__ - INFO - ✅ Configuration validated
2026-01-30 23:17:57 - __main__ - INFO - ✅ Database initialized
2026-01-30 23:17:57 - __main__ - INFO - ✅ Ghostwriter LLM initialized
2026-01-30 23:17:57 - __main__ - INFO - ✅ Buffer Engine initialized
2026-01-30 23:17:57 - __main__ - INFO - ✅ Slack listener initialized
2026-01-30 23:17:57 - __main__ - INFO - ✅ Interaction handler initialized

✅ All modules initialized successfully!

📋 Configuration:
  • Buffer window: 30 minutes
  • Min messages: 3
  • Min signal score: 0.6
  • Database: data/ghostwriter.db
  • Listening to: All channels (invite bot to your channel)

🚀 Digital Ghostwriter bot is running!
💬 Start chatting in your Slack channel...
⏰ Suggestions will appear after 30 min of silence (or use /ghostwrite now)

⌨️  Press Ctrl+C to stop

============================================================
⚡️ Bolt app is running!
```

---

## Step 7: Test It! (5-10 minutes)

### Option A: Quick Test with Manual Trigger

1. Go to your Slack channel
2. Have a conversation (10+ messages about a real topic):
   ```
   You: Should we go freemium or paid-only?
   Co-founder: I think freemium could work
   You: But 60% of free users never convert
   Co-founder: True, but they drive word-of-mouth
   You: Good point. Let's add usage caps to freemium
   ... (keep going for 10+ messages)
   ```

3. Type: `/ghostwrite now`

4. Wait ~10-30 seconds

5. You should see a suggestion card appear! 🎉

### Option B: Natural Test (Wait 30 Minutes)

1. Have a natural conversation with your co-founder
2. Stop chatting
3. Wait 30 minutes
4. The bot will automatically process and post a suggestion

---

## 🎉 Success!

If you see a suggestion card with:
- ✅ A draft for X (Twitter)
- ✅ A draft for LinkedIn
- ✅ Edit/Approve/Dismiss buttons

**You're all set!** The bot is working correctly.

---

## 🔧 Troubleshooting

### Bot not receiving messages?

**Check 1**: Is the bot invited to the channel?
```
/invite @Ghostwriter Bot
```

**Check 2**: Are the scopes correct?
- Go to api.slack.com/apps → Your App → OAuth & Permissions
- Verify `channels:history`, `channels:read`, `chat:write` are added

**Check 3**: Check the logs
- Look for "Received message from user..." in the terminal
- If you don't see this, the bot isn't receiving events

### "Missing required environment variables" error?

**Fix**: Check your `.env` file
```bash
cat .env
```

Make sure all three tokens are set (no placeholder text):
- `SLACK_BOT_TOKEN=xoxb-...`
- `SLACK_APP_TOKEN=xapp-...`
- `GEMINI_API_KEY=...`

### "Failed to initialize Gemini" error?

**Fix**: Check your Gemini API key
1. Go to [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Verify your API key is active
3. Copy it again and update `.env`

### Messages being filtered as noise?

**Check the logs**: You'll see why messages are filtered
```
DEBUG - Noise detected: contains keyword 'meeting'
DEBUG - Noise detected: too short (5 words)
```

**Adjust settings** in `.env`:
```bash
MIN_MESSAGE_LENGTH=5  # Lower threshold
MIN_SIGNAL_SCORE=0.4  # Lower threshold
```

### No suggestions appearing?

**Possible reasons**:

1. **Signal score too low**: Check logs for "signal too low"
   - Solution: Lower `MIN_SIGNAL_SCORE` in `.env`

2. **Not enough messages**: Need at least 3 messages
   - Solution: Lower `BUFFER_MIN_MESSAGES` in `.env`

3. **LLM confidence too low**: Check logs for "Confidence too low"
   - This means the conversation wasn't insightful enough
   - Try having a more substantive discussion

4. **Content failed validation**: Check logs for "failed quality validation"
   - The LLM generated promotional or generic content
   - Try again with a different conversation

---

## 📊 Useful Commands

### Check Statistics
```
/ghostwrite stats
```

Shows:
- Total conversations processed
- Total suggestions generated
- Approval rate
- Average signal score

### Force Process Now
```
/ghostwrite now
```

Immediately processes the current conversation (doesn't wait 30 min)

### Show Help
```
/ghostwrite
```

Shows available commands

---

## 🎯 Tips for Best Results

### What Makes a Good Conversation?

✅ **Good** (High Signal):
- Product debates and decisions
- Technical insights and learnings
- Market observations
- "Aha moments" and realizations
- First-person insights ("I learned...", "We decided...")
- Questions and back-and-forth discussion

❌ **Bad** (Low Signal / Filtered):
- Scheduling talk ("let's meet at 3pm")
- Short acknowledgments ("ok", "cool", "👍")
- Pure code without explanation
- Generic chit-chat

### Example High-Signal Conversation

```
Founder 1: I've been analyzing our churn data. 40% leave after the first week.

Founder 2: That's brutal. What's the common pattern?

Founder 1: They all hit the same wall - our onboarding is too complex.

Founder 2: Should we simplify it or add more hand-holding?

Founder 1: I think we need to do both. Simplify the UI AND add tooltips.

Founder 2: Agreed. Let's A/B test it next sprint.

Founder 1: The key insight here is: we optimized for power users, not new users.

Founder 2: Classic mistake. We need to optimize for the first 5 minutes, not the first 5 months.
```

This would generate a great suggestion! 🎯

---

## 🚀 Next Steps

1. **Use it daily**: Have natural conversations with your co-founder
2. **Review suggestions**: Click Edit to refine the drafts
3. **Track approval rate**: Use `/ghostwrite stats` to see what's working
4. **Adjust settings**: Tune `MIN_SIGNAL_SCORE` based on your needs
5. **Share feedback**: Note which suggestions are good vs bad to improve prompts

---

## 🛑 Stopping the Bot

Press `Ctrl+C` in the terminal:

```
^C
🛑 Shutting down gracefully...
✅ Goodbye!
```

---

## 📝 Files Created

After running the bot, you'll see:
```
slackbot-ghostwriter/
├── data/
│   └── ghostwriter.db  # SQLite database (auto-created)
├── .env                # Your tokens (keep secret!)
└── ... (other files)
```

**Important**: Never commit `.env` to git! It contains your secrets.

---

## 🎊 You're Done!

Enjoy your Digital Ghostwriter bot! 🤖✍️

For questions or issues, check the logs in the terminal - they're very detailed and will help you debug.
