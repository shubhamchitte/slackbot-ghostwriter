"""
Digital Ghostwriter Slack Bot - Main Entry Point
Wires all modules together and starts the bot.
"""

import logging
import signal
import sys
import os
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
    
    print("=" * 60)
    print("🤖 Digital Ghostwriter Slack Bot")
    print("=" * 60)
    
    # Validate configuration
    try:
        Config.validate()
        logger.info("✅ Configuration validated")
    except ValueError as e:
        logger.error(f"❌ Configuration error: {e}")
        print(f"\n❌ Configuration error: {e}")
        print("\nPlease check your .env file and ensure all required variables are set:")
        print("  - SLACK_BOT_TOKEN")
        print("  - SLACK_APP_TOKEN")
        print("  - GEMINI_API_KEY")
        sys.exit(1)
    
    # Ensure data directory exists
    os.makedirs('data', exist_ok=True)
    
    # Initialize storage
    try:
        storage = Storage(Config.DB_PATH)
        logger.info("✅ Database initialized")
    except Exception as e:
        logger.error(f"❌ Failed to initialize database: {e}")
        sys.exit(1)
    
    # Initialize LLM
    try:
        ghostwriter = Ghostwriter()
        logger.info("✅ Ghostwriter LLM initialized")
    except Exception as e:
        logger.error(f"❌ Failed to initialize Gemini: {e}")
        print(f"\n❌ Failed to initialize Gemini: {e}")
        print("\nPlease check your GEMINI_API_KEY in .env")
        sys.exit(1)
    
    # Initialize interaction handler (will be set after slack_listener)
    interaction_handler = None
    
    # Define callback for when buffer is ready
    def on_buffer_ready(buffer):
        """Callback when buffer is ready for processing."""
        logger.info(f"📝 Processing buffer {buffer.buffer_id} (signal: {buffer.signal_score:.2f})")
        
        # Save buffer to database
        storage.save_buffer(buffer)
        
        # Generate suggestions
        logger.info("🤖 Generating content suggestions with Gemini...")
        suggestion = ghostwriter.generate_suggestions(buffer)
        
        if suggestion:
            logger.info(f"✨ Generated suggestion - Topic: {suggestion['topic']}")
            # Post to Slack
            interaction_handler.post_suggestion(suggestion)
        else:
            logger.info("⏭️  No suggestion generated (low confidence or error)")
    
    # Initialize buffer engine with callback
    try:
        buffer_engine = BufferEngine(on_buffer_ready_callback=on_buffer_ready)
        logger.info("✅ Buffer Engine initialized")
    except Exception as e:
        logger.error(f"❌ Failed to initialize Buffer Engine: {e}")
        sys.exit(1)
    
    # Initialize Slack listener
    try:
        slack_listener = SlackListener(buffer_engine)
        logger.info("✅ Slack listener initialized")
    except Exception as e:
        logger.error(f"❌ Failed to initialize Slack listener: {e}")
        print(f"\n❌ Failed to initialize Slack: {e}")
        print("\nPlease check your Slack tokens in .env")
        sys.exit(1)
    
    # Initialize interaction handler
    try:
        interaction_handler = InteractionHandler(slack_listener, storage)
        interaction_handler.ghostwriter = ghostwriter  # Inject dependency for retries
        logger.info("✅ Interaction handler initialized")
    except Exception as e:
        logger.error(f"❌ Failed to initialize Interaction handler: {e}")
        sys.exit(1)
    
    # Register slash command
    @slack_listener.app.command("/ghostwrite")
    def handle_ghostwrite_command(ack, command):
        """Handle /ghostwrite slash command."""
        ack()
        
        channel_id = command['channel_id']
        text = command.get('text', '').strip()
        
        if text == 'now':
            # Force close buffer and process immediately
            buffer_engine.force_close_buffer(channel_id)
            slack_listener.post_message(
                channel_id=channel_id,
                text="⚡ Processing your conversation now..."
            )
            logger.info(f"Manual trigger: force closed buffer for {channel_id}")
        
        elif text == 'stats':
            # Show statistics
            stats = storage.get_stats()
            slack_listener.post_message(
                channel_id=channel_id,
                text=(
                    f"📊 *Ghostwriter Statistics*\n\n"
                    f"• Total conversations: {stats.get('total_buffers', 0)}\n"
                    f"• Total suggestions: {stats.get('total_suggestions', 0)}\n"
                    f"• Approval rate: {stats.get('approval_rate', 0):.0%}\n"
                    f"• Avg signal score: {stats.get('avg_signal_score', 0):.2f}"
                )
            )
        
        else:
            # Show help
            slack_listener.post_message(
                channel_id=channel_id,
                text=(
                    "🤖 *Ghostwriter Bot Commands*\n\n"
                    "`/ghostwrite now` - Force process current conversation\n"
                    "`/ghostwrite stats` - Show statistics\n\n"
                    "💡 *How it works:*\n"
                    "Just chat naturally! The bot will automatically suggest content "
                    "after 30 minutes of silence if your conversation has high signal."
                )
            )
    
    # Handle graceful shutdown
    def signal_handler(sig, frame):
        """Handle shutdown signals."""
        logger.info("\n🛑 Shutting down gracefully...")
        print("\n🛑 Shutting down gracefully...")
        buffer_engine.stop()
        print("✅ Goodbye!")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Print startup info
    print("\n✅ All modules initialized successfully!")
    print("\n📋 Configuration:")
    print(f"  • Buffer window: {Config.BUFFER_TIME_WINDOW_MINUTES} minutes")
    print(f"  • Min messages: {Config.BUFFER_MIN_MESSAGES}")
    print(f"  • Min signal score: {Config.MIN_SIGNAL_SCORE}")
    print(f"  • Database: {Config.DB_PATH}")
    
    if Config.TARGET_CHANNEL_ID:
        print(f"  • Target channel: {Config.TARGET_CHANNEL_ID}")
    else:
        print(f"  • Listening to: All channels (invite bot to your channel)")
    
    print("\n🚀 Digital Ghostwriter bot is running!")
    print("💬 Start chatting in your Slack channel...")
    print("⏰ Suggestions will appear after 30 min of silence (or use /ghostwrite now)")
    print("\n⌨️  Press Ctrl+C to stop\n")
    print("=" * 60)
    
    # Start the bot (this blocks)
    try:
        slack_listener.start()
    except KeyboardInterrupt:
        logger.info("\n🛑 Received keyboard interrupt")
        buffer_engine.stop()
        print("\n✅ Goodbye!")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        buffer_engine.stop()
        sys.exit(1)


if __name__ == "__main__":
    main()
