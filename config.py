"""
Configuration management for Digital Ghostwriter Slack Bot.
Loads environment variables and provides centralized config access.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Centralized configuration for the Slack bot."""
    
    # Slack credentials
    SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
    SLACK_APP_TOKEN = os.getenv("SLACK_APP_TOKEN")
    
    # Optional: Target channel ID (if you want to restrict to specific channel)
    TARGET_CHANNEL_ID = os.getenv("TARGET_CHANNEL_ID", None)
    
    # Google Gemini API
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    
    # Buffer Engine settings
    BUFFER_TIME_WINDOW_MINUTES = int(os.getenv("BUFFER_TIME_WINDOW_MINUTES", "30"))
    BUFFER_MIN_MESSAGES = int(os.getenv("BUFFER_MIN_MESSAGES", "3"))
    BUFFER_MAX_MESSAGES = int(os.getenv("BUFFER_MAX_MESSAGES", "50"))
    
    # Signal score threshold (0.0 - 1.0)
    MIN_SIGNAL_SCORE = float(os.getenv("MIN_SIGNAL_SCORE", "0.6"))
    
    # Noise filtering settings
    NOISE_KEYWORDS = [
        "call", "meeting", "calendar", "zoom", "meet", 
        "schedule", "reschedule", "sync", "standup"
    ]
    MIN_MESSAGE_LENGTH = int(os.getenv("MIN_MESSAGE_LENGTH", "10"))  # words
    
    # Database path
    DB_PATH = os.getenv("DB_PATH", "data/ghostwriter.db")
    
    @classmethod
    def validate(cls):
        """Validate that required configuration is present."""
        required = {
            "SLACK_BOT_TOKEN": cls.SLACK_BOT_TOKEN,
            "SLACK_APP_TOKEN": cls.SLACK_APP_TOKEN,
            "GEMINI_API_KEY": cls.GEMINI_API_KEY,
        }
        
        missing = [key for key, value in required.items() if not value]
        
        if missing:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing)}\n"
                f"Please check your .env file."
            )
        
        return True
