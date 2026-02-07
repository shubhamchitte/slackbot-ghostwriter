# Digital Ghostwriter Slack Bot - Complete Roadmap & Blueprint

## 📋 Table of Contents
1. [Use Case & Vision](#use-case--vision)
2. [What's Been Completed](#whats-been-completed)
3. [Remaining Implementation Steps](#remaining-implementation-steps)
4. [Testing Strategy](#testing-strategy)
5. [Deployment Guide](#deployment-guide)

---

## 🎯 Use Case & Vision

### The Problem
As a technical founder, you have valuable conversations with your co-founder every day:
- Product debates and decisions
- Technical insights and learnings
- Market observations and strategy discussions
- "Aha moments" that would make great social media content

**But**: These insights get lost in Slack threads and never make it to X (Twitter) or LinkedIn.

### The Solution
A "Digital Ghostwriter" bot that:
1. **Passively listens** to your private Slack channel conversations
2. **Intelligently filters** out admin talk ("let's schedule a call") and focuses on insights
3. **Understands context** by buffering entire conversations, not just isolated messages
4. **Generates suggestions** for X (short/punchy) and LinkedIn (contextual/detailed)
5. **Presents options** via interactive Slack cards with Edit/Approve/Dismiss buttons
6. **Never auto-posts** - you stay in complete control

### Key Differentiators vs Reference Repo
- ✅ **Contextual Awareness**: Buffers 30-minute conversation windows instead of single messages
- ✅ **Noise Filtering**: Sophisticated algorithm to ignore scheduling talk and banter
- ✅ **Signal Scoring**: Rates conversations 0.0-1.0 based on insight value
- ✅ **100% Local**: Uses Socket Mode (no server, no ngrok, completely free)
- ✅ **Interactive UI**: Slack Block Kit cards with buttons (no external website)

### Target Workflow
```
You + Co-founder chat about pricing strategy (10 messages over 20 min)
    ↓
Bot silently buffers the conversation
    ↓
30 minutes later (or manual trigger via /ghostwrite now)
    ↓
Bot analyzes: "High signal! This is about a key decision"
    ↓
LLM generates 2 drafts (X + LinkedIn)
    ↓
Suggestion card appears in Slack with Edit/Approve/Dismiss buttons
    ↓
You click Edit, refine the LinkedIn post, click Approve
    ↓
Bot saves your feedback to improve future suggestions
```

---

## ✅ What's Been Completed

### Phase 1: Core Infrastructure ✅

#### 1. Project Setup
**Files Created**:
- `requirements.txt` - Dependencies (slack-bolt, google-generativeai, python-dotenv)
- `config.py` - Centralized configuration management
- `.env.example` - Environment variable template
- `.gitignore` - Excludes sensitive files
- `README.md` - Setup instructions and documentation

**Configuration System**:
```python
# config.py provides:
- SLACK_BOT_TOKEN, SLACK_APP_TOKEN (from .env)
- GEMINI_API_KEY (Google Gemini Flash)
- BUFFER_TIME_WINDOW_MINUTES (default: 30)
- BUFFER_MIN_MESSAGES (default: 3)
- MIN_SIGNAL_SCORE (default: 0.6)
- NOISE_KEYWORDS (scheduling terms to filter)
- MIN_MESSAGE_LENGTH (default: 10 words)
- DB_PATH (data/ghostwriter.db)
```

**Validation**: `Config.validate()` checks for missing required env vars on startup.

---

#### 2. Module 1: Slack Socket Listener ✅
**File**: `slack_listener.py`

**What It Does**:
- Establishes persistent connection to Slack using Socket Mode
- Listens for `message` events in channels the bot is invited to
- Filters out noise at the Slack level (bots, edits, threads)
- Passes clean message data to Buffer Engine

**Key Features**:
1. **Socket Mode Handler**: No public URL needed, runs on localhost
2. **Automatic Reconnection**: Built into slack-bolt library
3. **Message Filtering**:
   - Ignores messages with `subtype` (edits, deletes, bot messages)
   - Ignores messages without `user_id` (system messages)
   - Ignores threaded replies (prevents duplicate processing)
   - Optional channel filtering via `TARGET_CHANNEL_ID`

**Message Data Structure Passed to Buffer**:
```python
{
    "channel_id": "C1234567890",
    "user_id": "U9876543210",
    "text": "I think we should go freemium...",
    "timestamp": "1738251857.123456",
    "thread_ts": None,  # or timestamp if threaded
    "is_threaded": False
}
```

**Helper Methods**:
- `post_message(channel_id, blocks, text)` - For posting suggestion cards later

**Integration Point**: Calls `buffer_engine.add_message(message_data)` for each valid message.

---

#### 3. Module 2: Buffer Engine ✅
**File**: `buffer_engine.py`

**What It Does**:
This is the **most critical module** - the "intelligence layer" that distinguishes valuable insights from banter.

**Architecture**:
```
BufferEngine
    ├── ConversationBuffer (data class)
    │   ├── buffer_id: "C123_1738251857"
    │   ├── messages: List[Dict]
    │   ├── start_time, last_message_time
    │   ├── topic_keywords: ["Pricing", "Freemium"]
    │   └── signal_score: 0.85
    │
    ├── active_buffers: Dict[channel_id -> ConversationBuffer]
    ├── monitor_thread: Background daemon
    └── on_buffer_ready: Callback to LLM module
```

**Noise Filtering Algorithm** (`_is_noise()`):

1. **Scheduling Keywords** (HIGHEST PRIORITY)
   - Filters: "call", "meeting", "calendar", "zoom", "schedule", "sync", "standup"
   - Example: "Let's jump on a call at 3pm" → FILTERED ❌
   - Example: "We should call this feature 'Autopilot'" → KEPT ✅ (different context)

2. **Short Messages** (< 10 words)
   - Filters brief acknowledgments
   - Example: "ok cool" → FILTERED ❌
   - Example: "👍" → FILTERED ❌

3. **Pure Acknowledgments** (Regex Patterns)
   - Patterns: `^(ok|okay|sure|yep|yeah|sounds good|cool|lol)$`
   - Example: "sounds good 👍" → FILTERED ❌

4. **Code Without Context** (>80% code, <20 words)
   - Example: "```python\ndef foo(): pass```" → FILTERED ❌
   - Example: "Here's the fix for the race condition: ```code```" → KEPT ✅

**Signal Scoring Algorithm** (`calculate_signal_score()`):

Rates conversations 0.0 to 1.0 based on:

| Factor | Points | Criteria |
|--------|--------|----------|
| **Message Length** | 0.3 | 20-150 words/msg (sweet spot) |
| | 0.15 | 10-20 words/msg (acceptable) |
| **Questions** | 0.25 | 2+ questions (debates!) |
| | 0.1 | 1 question |
| **Technical Terms** | 0.25 | 5+ terms (API, product, growth, etc.) |
| | 0.15 | 2-4 terms |
| **First-Person Insights** | 0.3 | 2+ insights ("I learned", "We decided") |
| | 0.15 | 1 insight |
| **Conversation Length** | 0.1 | 5+ messages (more context) |

**Example High-Signal Conversation** (Score: 0.85):
```
User: I've been thinking about our pricing model. Should we go freemium?
User: The data shows 60% of users never upgrade from free tier.
User: But freemium drives all our word-of-mouth growth.
User: I think we should keep freemium but add usage caps. Thoughts?
```
- ✅ 4 messages (0.1)
- ✅ 1 question (0.1)
- ✅ Technical terms: pricing, freemium, users, upgrade (0.25)
- ✅ First-person: "I think we should" (0.15)
- ✅ Good length (0.25)
- **Total: 0.85** → Triggers LLM ✨

**Example Low-Signal Conversation** (Score: 0.0):
```
User: hey
User: can we sync tomorrow?
User: cool
```
- ❌ Scheduling keyword "sync" → FILTERED before scoring
- **Total: 0.0** → Discarded

**Buffering Strategy**:

1. **Time-Based Windows**: 30-minute default (`BUFFER_TIME_WINDOW_MINUTES`)
2. **Automatic Closure**: Buffer closes after 30 min of silence
3. **Minimum Messages**: Requires 3+ messages (`BUFFER_MIN_MESSAGES`)
4. **Background Monitoring**: Daemon thread checks every 60 seconds
5. **Manual Trigger**: `force_close_buffer(channel_id)` for `/ghostwrite now`

**Topic Keyword Extraction**:
- Extracts capitalized words: "Pricing", "Freemium", "API"
- Tracks technical acronyms: API, UI, UX, MVP, SaaS, AI, ML, LLM
- Keeps last 10 unique keywords per buffer
- Used for LLM context (future)

**Callback Mechanism**:
When buffer closes with `signal_score >= 0.6`:
```python
if self.on_buffer_ready:
    self.on_buffer_ready(buffer)  # Triggers Module 3 (LLM)
```

**Thread Safety**:
- Uses `threading.Lock()` to prevent race conditions
- All buffer operations are atomic

---

## 🚧 Remaining Implementation Steps

### Phase 2: LLM Integration (Module 3)

#### File to Create: `ghostwriter.py`

**Purpose**: Transform buffered conversations into platform-specific content suggestions using Google Gemini Flash.

**Implementation Steps**:

1. **Initialize Gemini Client**
```python
import google.generativeai as genai
from config import Config

genai.configure(api_key=Config.GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')
```

2. **Create Prompt Templates**

**For X (Twitter)**:
```
Role: You are a ghostwriter for a technical CEO.

Context: Below is a conversation between two founders:
{conversation_text}

Task: Extract ONE high-signal insight and write a punchy tweet (240 chars max).

Style Guidelines:
- Start with a hook (contrarian take, surprising stat, or question)
- Use simple words, avoid jargon
- Be specific, not generic
- End with a zinger or call-to-action

Good Examples:
- "Most founders optimize for valuation. The best optimize for learning rate."
- "We just spent 3 hours debugging. The bug? A missing comma. The lesson? Priceless."

Bad Examples:
- "Excited to announce..." (promotional)
- "Hustle harder!" (generic motivation)

Output Format (JSON):
{
  "x_draft": "your tweet here",
  "confidence": 0.85,
  "topic": "Pricing Strategy"
}
```

**For LinkedIn**:
```
Role: You are a ghostwriter for a technical CEO sharing founder lessons.

Context: Below is a conversation between two founders:
{conversation_text}

Task: Write a 150-250 word LinkedIn post about the key decision/insight.

Structure:
1. Hook: Start with the problem or debate (1-2 sentences)
2. Body: Explain the decision and why it matters (3-4 sentences)
3. Lesson: Generalize the takeaway for other founders (2-3 sentences)
4. CTA: Ask a question to drive engagement (1 sentence)

Tone: Authentic, humble, tactical (not motivational fluff)

Good Example:
"We debated for weeks: freemium or paid-only?

The data was clear—60% of free users never upgrade. But here's what the data didn't show: 100% of our word-of-mouth growth came from free users.

We decided to keep freemium but add usage caps. The result? 2x signups, same conversion rate, but now we're not subsidizing power users.

Lesson: Don't just look at conversion funnels. Look at acquisition loops.

What's your take on freemium? 👇"

Output Format (JSON):
{
  "linkedin_draft": "your post here",
  "confidence": 0.90,
  "topic": "Pricing Strategy"
}
```

3. **Implement Content Generation**
```python
class Ghostwriter:
    def __init__(self):
        genai.configure(api_key=Config.GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
    
    def generate_suggestions(self, buffer: ConversationBuffer) -> Dict:
        """
        Generate X and LinkedIn drafts from conversation buffer.
        
        Returns:
        {
            "x_draft": str,
            "linkedin_draft": str,
            "confidence": float,
            "topic": str,
            "buffer_id": str
        }
        """
        conversation_text = buffer.get_conversation_text()
        
        # Generate X draft
        x_prompt = self._build_x_prompt(conversation_text)
        x_response = self.model.generate_content(x_prompt)
        x_data = json.loads(x_response.text)
        
        # Generate LinkedIn draft
        linkedin_prompt = self._build_linkedin_prompt(conversation_text)
        linkedin_response = self.model.generate_content(linkedin_prompt)
        linkedin_data = json.loads(linkedin_response.text)
        
        # Combine results
        return {
            "x_draft": x_data["x_draft"],
            "linkedin_draft": linkedin_data["linkedin_draft"],
            "confidence": (x_data["confidence"] + linkedin_data["confidence"]) / 2,
            "topic": x_data["topic"],
            "buffer_id": buffer.buffer_id,
            "channel_id": buffer.channel_id
        }
```

4. **Content Quality Validation**
```python
def _validate_content(self, draft: str, platform: str) -> bool:
    """Ensure content meets quality standards."""
    
    # Check length
    if platform == "x" and len(draft) > 280:
        return False
    if platform == "linkedin" and not (150 <= len(draft) <= 300):
        return False
    
    # Check for promotional content
    promo_keywords = ["hiring", "we're excited to announce", "check out our"]
    if any(keyword in draft.lower() for keyword in promo_keywords):
        return False
    
    # Check for generic advice
    generic_phrases = ["hustle harder", "stay focused", "never give up"]
    if any(phrase in draft.lower() for phrase in generic_phrases):
        return False
    
    return True
```

5. **Error Handling**
```python
try:
    suggestion = self.generate_suggestions(buffer)
    
    # Validate confidence threshold
    if suggestion["confidence"] < 0.7:
        logger.info(f"Low confidence ({suggestion['confidence']}) - skipping")
        return None
    
    return suggestion
    
except Exception as e:
    logger.error(f"LLM generation failed: {e}")
    return None
```

**Integration**: Buffer Engine calls `ghostwriter.generate_suggestions(buffer)` when buffer closes.

---

### Phase 3: Interactive UI (Module 4)

#### File to Create: `interaction_handler.py`

**Purpose**: Present suggestions as interactive Slack cards using Block Kit.

**Implementation Steps**:

1. **Design Suggestion Card (Block Kit JSON)**
```python
def build_suggestion_card(suggestion: Dict) -> List[Dict]:
    """Build Block Kit blocks for suggestion card."""
    
    return [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": "💡 Content Suggestion",
                "emoji": True
            }
        },
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"*Topic:* {suggestion['topic']} | *Confidence:* {suggestion['confidence']:.0%}"
                }
            ]
        },
        {
            "type": "divider"
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*🐦 For X (Twitter):*\n{suggestion['x_draft']}"
            }
        },
        {
            "type": "divider"
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*💼 For LinkedIn:*\n{suggestion['linkedin_draft']}"
            }
        },
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"Based on your conversation from {format_time_range(suggestion)}"
                }
            ]
        },
        {
            "type": "actions",
            "block_id": f"suggestion_{suggestion['buffer_id']}",
            "elements": [
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "✏️ Edit"},
                    "style": "primary",
                    "action_id": "edit_suggestion",
                    "value": suggestion['buffer_id']
                },
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "👍 Approve"},
                    "style": "primary",
                    "action_id": "approve_suggestion",
                    "value": suggestion['buffer_id']
                },
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "🗑️ Dismiss"},
                    "style": "danger",
                    "action_id": "dismiss_suggestion",
                    "value": suggestion['buffer_id']
                }
            ]
        }
    ]
```

2. **Post Suggestion Card**
```python
class InteractionHandler:
    def __init__(self, slack_listener, storage):
        self.slack = slack_listener
        self.storage = storage
        self._register_button_handlers()
    
    def post_suggestion(self, suggestion: Dict):
        """Post suggestion card to Slack."""
        blocks = build_suggestion_card(suggestion)
        
        response = self.slack.post_message(
            channel_id=suggestion['channel_id'],
            blocks=blocks,
            text=f"Content suggestion: {suggestion['topic']}"
        )
        
        # Store message timestamp for later updates
        suggestion['message_ts'] = response['ts']
        self.storage.save_suggestion(suggestion)
```

3. **Handle Button Clicks**
```python
def _register_button_handlers(self):
    """Register handlers for button interactions."""
    
    @self.slack.app.action("edit_suggestion")
    def handle_edit(ack, body, client):
        ack()
        buffer_id = body['actions'][0]['value']
        suggestion = self.storage.get_suggestion(buffer_id)
        
        # Open modal with text inputs
        client.views_open(
            trigger_id=body['trigger_id'],
            view=self._build_edit_modal(suggestion)
        )
    
    @self.slack.app.action("approve_suggestion")
    def handle_approve(ack, body, client):
        ack()
        buffer_id = body['actions'][0]['value']
        
        # Update database
        self.storage.record_user_action(buffer_id, "approved")
        
        # Update message
        client.chat_update(
            channel=body['channel']['id'],
            ts=body['message']['ts'],
            text="✅ Suggestion approved!",
            blocks=[
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": "✅ *Suggestion approved!*"}
                }
            ]
        )
    
    @self.slack.app.action("dismiss_suggestion")
    def handle_dismiss(ack, body, client):
        ack()
        buffer_id = body['actions'][0]['value']
        
        # Update database
        self.storage.record_user_action(buffer_id, "dismissed")
        
        # Delete message
        client.chat_delete(
            channel=body['channel']['id'],
            ts=body['message']['ts']
        )
```

4. **Build Edit Modal**
```python
def _build_edit_modal(self, suggestion: Dict) -> Dict:
    """Build modal for editing drafts."""
    return {
        "type": "modal",
        "callback_id": "edit_modal_submit",
        "private_metadata": suggestion['buffer_id'],
        "title": {"type": "plain_text", "text": "Edit Suggestion"},
        "submit": {"type": "plain_text", "text": "Save"},
        "blocks": [
            {
                "type": "input",
                "block_id": "x_draft_input",
                "label": {"type": "plain_text", "text": "X (Twitter) Draft"},
                "element": {
                    "type": "plain_text_input",
                    "action_id": "x_draft",
                    "multiline": True,
                    "initial_value": suggestion['x_draft'],
                    "max_length": 280
                }
            },
            {
                "type": "input",
                "block_id": "linkedin_draft_input",
                "label": {"type": "plain_text", "text": "LinkedIn Draft"},
                "element": {
                    "type": "plain_text_input",
                    "action_id": "linkedin_draft",
                    "multiline": True,
                    "initial_value": suggestion['linkedin_draft']
                }
            }
        ]
    }
```

5. **Handle Modal Submission**
```python
@self.slack.app.view("edit_modal_submit")
def handle_modal_submit(ack, body, client, view):
    ack()
    
    buffer_id = view['private_metadata']
    values = view['state']['values']
    
    # Extract edited drafts
    x_draft = values['x_draft_input']['x_draft']['value']
    linkedin_draft = values['linkedin_draft_input']['linkedin_draft']['value']
    
    # Update database
    self.storage.update_suggestion(buffer_id, {
        'x_draft': x_draft,
        'linkedin_draft': linkedin_draft
    })
    self.storage.record_user_action(buffer_id, "edited")
```

---

### Phase 4: Local Storage (Module 5)

#### File to Create: `storage.py`

**Purpose**: Track conversations, suggestions, and user feedback in SQLite.

**Implementation Steps**:

1. **Database Schema**
```python
import sqlite3
from datetime import datetime
import json

class Storage:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Create tables if they don't exist."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Conversation buffers table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversation_buffers (
                buffer_id TEXT PRIMARY KEY,
                channel_id TEXT NOT NULL,
                start_time TIMESTAMP NOT NULL,
                end_time TIMESTAMP NOT NULL,
                message_count INTEGER NOT NULL,
                signal_score REAL NOT NULL,
                topic_keywords TEXT,
                raw_messages TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Suggestions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS suggestions (
                suggestion_id TEXT PRIMARY KEY,
                buffer_id TEXT NOT NULL,
                x_draft TEXT NOT NULL,
                linkedin_draft TEXT NOT NULL,
                confidence REAL NOT NULL,
                topic TEXT,
                message_ts TEXT,
                user_action TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (buffer_id) REFERENCES conversation_buffers(buffer_id)
            )
        """)
        
        # Used topics table (prevent repetition)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS used_topics (
                topic TEXT PRIMARY KEY,
                last_used TIMESTAMP NOT NULL,
                usage_count INTEGER DEFAULT 1
            )
        """)
        
        conn.commit()
        conn.close()
```

2. **Storage Methods**
```python
def save_buffer(self, buffer: ConversationBuffer):
    """Save conversation buffer."""
    conn = sqlite3.connect(self.db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO conversation_buffers 
        (buffer_id, channel_id, start_time, end_time, message_count, 
         signal_score, topic_keywords, raw_messages)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        buffer.buffer_id,
        buffer.channel_id,
        buffer.start_time.isoformat(),
        buffer.last_message_time.isoformat(),
        len(buffer.messages),
        buffer.signal_score,
        json.dumps(buffer.topic_keywords),
        json.dumps(buffer.messages)
    ))
    
    conn.commit()
    conn.close()

def save_suggestion(self, suggestion: Dict):
    """Save LLM-generated suggestion."""
    conn = sqlite3.connect(self.db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO suggestions 
        (suggestion_id, buffer_id, x_draft, linkedin_draft, confidence, topic, message_ts)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        suggestion['buffer_id'],  # Use buffer_id as suggestion_id
        suggestion['buffer_id'],
        suggestion['x_draft'],
        suggestion['linkedin_draft'],
        suggestion['confidence'],
        suggestion['topic'],
        suggestion.get('message_ts')
    ))
    
    # Track topic usage
    cursor.execute("""
        INSERT INTO used_topics (topic, last_used)
        VALUES (?, ?)
        ON CONFLICT(topic) DO UPDATE SET
            last_used = ?,
            usage_count = usage_count + 1
    """, (
        suggestion['topic'],
        datetime.now().isoformat(),
        datetime.now().isoformat()
    ))
    
    conn.commit()
    conn.close()

def record_user_action(self, buffer_id: str, action: str):
    """Record user action (approve/dismiss/edit)."""
    conn = sqlite3.connect(self.db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
        UPDATE suggestions
        SET user_action = ?, updated_at = ?
        WHERE suggestion_id = ?
    """, (action, datetime.now().isoformat(), buffer_id))
    
    conn.commit()
    conn.close()

def get_recent_topics(self, days: int = 30) -> List[str]:
    """Get topics used in last N days (avoid repetition)."""
    conn = sqlite3.connect(self.db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT topic FROM used_topics
        WHERE last_used >= datetime('now', '-' || ? || ' days')
    """, (days,))
    
    topics = [row[0] for row in cursor.fetchall()]
    conn.close()
    return topics

def get_approval_rate(self) -> float:
    """Calculate approval rate for analytics."""
    conn = sqlite3.connect(self.db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            COUNT(CASE WHEN user_action = 'approved' THEN 1 END) * 1.0 / COUNT(*) 
        FROM suggestions
        WHERE user_action IS NOT NULL
    """)
    
    rate = cursor.fetchone()[0] or 0.0
    conn.close()
    return rate
```

---

### Phase 5: Main Entry Point

#### File to Create: `main.py`

**Purpose**: Wire all modules together and start the bot.

**Implementation Steps**:

1. **Initialize All Modules**
```python
import logging
import signal
import sys
from config import Config
from storage import Storage
from buffer_engine import BufferEngine
from ghostwriter import Ghostwriter
from interaction_handler import InteractionHandler
from slack_listener import SlackListener

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Main entry point for Digital Ghostwriter bot."""
    
    # Validate configuration
    try:
        Config.validate()
        logger.info("✅ Configuration validated")
    except ValueError as e:
        logger.error(f"❌ Configuration error: {e}")
        sys.exit(1)
    
    # Initialize storage
    storage = Storage(Config.DB_PATH)
    logger.info("✅ Database initialized")
    
    # Initialize LLM
    ghostwriter = Ghostwriter()
    logger.info("✅ Ghostwriter LLM initialized")
    
    # Initialize buffer engine with callback
    def on_buffer_ready(buffer):
        """Callback when buffer is ready for processing."""
        logger.info(f"Processing buffer {buffer.buffer_id}")
        
        # Save buffer to database
        storage.save_buffer(buffer)
        
        # Generate suggestions
        suggestion = ghostwriter.generate_suggestions(buffer)
        
        if suggestion:
            # Post to Slack
            interaction_handler.post_suggestion(suggestion)
        else:
            logger.info("No suggestion generated (low confidence or error)")
    
    buffer_engine = BufferEngine(on_buffer_ready_callback=on_buffer_ready)
    logger.info("✅ Buffer Engine initialized")
    
    # Initialize Slack listener
    slack_listener = SlackListener(buffer_engine)
    logger.info("✅ Slack listener initialized")
    
    # Initialize interaction handler
    interaction_handler = InteractionHandler(slack_listener, storage)
    logger.info("✅ Interaction handler initialized")
    
    # Register slash command
    @slack_listener.app.command("/ghostwrite")
    def handle_ghostwrite_command(ack, command):
        ack()
        channel_id = command['channel_id']
        
        if command['text'] == 'now':
            buffer_engine.force_close_buffer(channel_id)
            logger.info(f"Manual trigger: force closed buffer for {channel_id}")
        else:
            # Show help
            slack_listener.post_message(
                channel_id=channel_id,
                text="Usage: `/ghostwrite now` to force process current conversation"
            )
    
    # Handle graceful shutdown
    def signal_handler(sig, frame):
        logger.info("Shutting down gracefully...")
        buffer_engine.stop()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start the bot
    logger.info("🚀 Digital Ghostwriter bot starting...")
    logger.info("Press Ctrl+C to stop")
    
    try:
        slack_listener.start()  # This blocks
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        buffer_engine.stop()
        sys.exit(1)

if __name__ == "__main__":
    main()
```

2. **Create Data Directory**
```python
import os

# Ensure data directory exists
os.makedirs('data', exist_ok=True)
```

---

## 🧪 Testing Strategy

### Unit Tests

Create `tests/` directory with:

1. **test_buffer_engine.py**
```python
def test_noise_filtering():
    """Test that admin talk is filtered."""
    engine = BufferEngine()
    
    # Should filter
    assert engine._is_noise("let's schedule a call") == True
    assert engine._is_noise("ok cool") == True
    assert engine._is_noise("👍") == True
    
    # Should keep
    assert engine._is_noise("I think we should pivot to freemium") == False

def test_signal_scoring():
    """Test signal score calculation."""
    buffer = ConversationBuffer("test_1", "C123")
    
    # Add high-signal messages
    buffer.add_message({"text": "Should we go freemium or paid-only?"})
    buffer.add_message({"text": "I learned that 60% of free users never convert."})
    
    score = buffer.calculate_signal_score()
    assert score > 0.6  # Should trigger LLM
```

2. **test_ghostwriter.py**
```python
def test_prompt_formatting():
    """Test that prompts are correctly formatted."""
    ghostwriter = Ghostwriter()
    
    buffer = create_test_buffer()
    prompt = ghostwriter._build_x_prompt(buffer.get_conversation_text())
    
    assert "Role: You are a ghostwriter" in prompt
    assert buffer.get_conversation_text() in prompt
```

3. **test_storage.py**
```python
def test_save_and_retrieve():
    """Test database operations."""
    storage = Storage(":memory:")  # In-memory DB for testing
    
    buffer = create_test_buffer()
    storage.save_buffer(buffer)
    
    # Verify saved
    conn = sqlite3.connect(":memory:")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM conversation_buffers WHERE buffer_id = ?", (buffer.buffer_id,))
    assert cursor.fetchone() is not None
```

### Integration Tests

1. **End-to-End Flow**
```python
def test_full_flow():
    """Test complete flow from message to suggestion."""
    
    # 1. Send messages to Slack listener
    # 2. Verify buffer created
    # 3. Verify noise filtered
    # 4. Force close buffer
    # 5. Verify LLM called
    # 6. Verify suggestion posted
    # 7. Verify database updated
```

### Manual Testing Checklist

- [ ] Bot connects to Slack via Socket Mode
- [ ] Bot receives messages in target channel
- [ ] Noise messages are filtered (check logs)
- [ ] High-signal conversation creates buffer
- [ ] Buffer closes after 30 min silence
- [ ] `/ghostwrite now` forces processing
- [ ] Suggestion card appears with both drafts
- [ ] Edit button opens modal
- [ ] Approve button updates message
- [ ] Dismiss button deletes message
- [ ] Database stores all actions
- [ ] Approval rate calculates correctly

---

## 🚀 Deployment Guide

### Local Development (Current)
```bash
# 1. Set up environment
cp .env.example .env
# Edit .env with your tokens

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run bot
python main.py
```

### Production Deployment Options

#### Option 1: Always-On Laptop
- Run `python main.py` in a tmux/screen session
- Pros: Free, simple
- Cons: Laptop must stay on

#### Option 2: Cloud VM (Free Tier)
- Google Cloud Free Tier (e2-micro)
- AWS Free Tier (t2.micro)
- Deploy with systemd service

```bash
# /etc/systemd/system/ghostwriter.service
[Unit]
Description=Digital Ghostwriter Slack Bot
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/slackbot-ghostwriter
ExecStart=/usr/bin/python3 main.py
Restart=always

[Install]
WantedBy=multi-user.target
```

#### Option 3: Docker Container
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "main.py"]
```

---

## 📊 Success Metrics

Track these to improve the bot:

1. **Approval Rate**: `storage.get_approval_rate()`
   - Target: >50% approval rate
   - If low: Adjust prompts or signal score threshold

2. **Noise Filter Accuracy**
   - Manually review filtered messages
   - Adjust `NOISE_KEYWORDS` and `MIN_MESSAGE_LENGTH`

3. **Signal Score Distribution**
   - Log all signal scores
   - Adjust `MIN_SIGNAL_SCORE` threshold

4. **Topic Diversity**
   - Check `used_topics` table
   - Ensure no repetition within 30 days

---

## 🎯 Next Immediate Steps

1. **Implement Module 3** (Ghostwriter LLM)
   - Create `ghostwriter.py`
   - Test with sample conversations
   - Validate output quality

2. **Implement Module 4** (Interaction Handler)
   - Create `interaction_handler.py`
   - Test Block Kit rendering
   - Test button callbacks

3. **Implement Module 5** (Storage)
   - Create `storage.py`
   - Test database operations
   - Verify data persistence

4. **Wire Everything in main.py**
   - Connect all modules
   - Add error handling
   - Test end-to-end

5. **Manual Testing**
   - Run bot locally
   - Have real conversation
   - Verify suggestion quality

6. **Iterate on Prompts**
   - Refine based on output quality
   - Adjust tone and style
   - Add more examples

---

## 📝 Notes & Considerations

- **Rate Limits**: Gemini Flash free tier = 15 req/min, 1M tokens/day (plenty for MVP)
- **Privacy**: All data stays local in SQLite (no cloud storage)
- **Scalability**: Current design handles 1 channel well; multi-channel needs buffer per channel
- **Future Enhancements**: 
  - Thread support (currently ignored)
  - Multi-language support
  - Custom prompt templates per user
  - Analytics dashboard
