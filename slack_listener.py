"""
Module 1: Slack Socket Listener
Establishes persistent connection to Slack using Socket Mode.
Listens for messages and passes them to the Buffer Engine.
"""

from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from config import Config
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SlackListener:
    """Handles Slack Socket Mode connection and message events."""
    
    def __init__(self, buffer_engine):
        """
        Initialize Slack listener.
        
        Args:
            buffer_engine: Instance of BufferEngine to receive messages
        """
        self.buffer_engine = buffer_engine
        
        # Initialize Slack app with bot token
        self.app = App(token=Config.SLACK_BOT_TOKEN)
        
        # Register event handlers
        self._register_handlers()
        
        logger.info("Slack listener initialized")
    
    def _register_handlers(self):
        """Register Slack event handlers."""
        
        @self.app.event("message")
        def handle_message(event, say):
            """
            Handle incoming message events.
            Filters out noise and passes valid messages to Buffer Engine.
            """
            # Extract message details
            channel_id = event.get("channel")
            user_id = event.get("user")
            text = event.get("text", "")
            timestamp = event.get("ts")
            thread_ts = event.get("thread_ts")  # For threaded messages
            subtype = event.get("subtype")
            
            # Filter conditions - ignore these messages
            if self._should_ignore_message(event, subtype, user_id):
                return
            
            # Optional: Filter by target channel
            if Config.TARGET_CHANNEL_ID and channel_id != Config.TARGET_CHANNEL_ID:
                logger.debug(f"Ignoring message from non-target channel: {channel_id}")
                return
            
            # Log received message
            logger.info(f"Received message from user {user_id} in channel {channel_id}")
            
            # Pass to buffer engine
            message_data = {
                "channel_id": channel_id,
                "user_id": user_id,
                "text": text,
                "timestamp": timestamp,
                "thread_ts": thread_ts,
                "is_threaded": bool(thread_ts and thread_ts != timestamp)
            }
            
            self.buffer_engine.add_message(message_data)
    
    def _should_ignore_message(self, event, subtype, user_id):
        """
        Determine if a message should be ignored.
        
        Args:
            event: Slack event object
            subtype: Message subtype (e.g., 'message_changed', 'bot_message')
            user_id: User ID who sent the message
        
        Returns:
            bool: True if message should be ignored
        """
        # Ignore messages with subtypes (edits, deletes, etc.)
        if subtype is not None:
            logger.debug(f"Ignoring message with subtype: {subtype}")
            return True
        
        # Ignore bot messages (including our own)
        if not user_id or event.get("bot_id"):
            logger.debug("Ignoring bot message")
            return True
        
        # Ignore messages in threads (for now - can be enhanced later)
        # This prevents duplicate processing of threaded conversations
        thread_ts = event.get("thread_ts")
        timestamp = event.get("ts")
        if thread_ts and thread_ts != timestamp:
            logger.debug("Ignoring threaded reply")
            return True
        
        return False
    
    def start(self):
        """Start the Socket Mode handler (blocking)."""
        logger.info("Starting Slack Socket Mode listener...")
        
        # Create Socket Mode handler
        handler = SocketModeHandler(
            app=self.app,
            app_token=Config.SLACK_APP_TOKEN
        )
        
        # Start listening (this blocks)
        handler.start()
    
    def post_message(self, channel_id, blocks=None, text=None):
        """
        Post a message to a Slack channel.
        
        Args:
            channel_id: Channel to post to
            blocks: Block Kit blocks for rich formatting
            text: Plain text fallback
        
        Returns:
            Response from Slack API
        """
        try:
            response = self.app.client.chat_postMessage(
                channel=channel_id,
                blocks=blocks,
                text=text
            )
            logger.info(f"Posted message to channel {channel_id}")
            return response
        except Exception as e:
            logger.error(f"Error posting message: {e}")
            raise
