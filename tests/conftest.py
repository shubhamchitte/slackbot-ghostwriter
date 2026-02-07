"""
Pytest configuration and fixtures for slackbot-ghostwriter tests.
"""

import pytest
import tempfile
import os
from datetime import datetime
from unittest.mock import Mock, MagicMock
from storage import Storage
from buffer_engine import ConversationBuffer


@pytest.fixture
def temp_db():
    """Create a temporary SQLite database for testing."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    
    # Create storage instance
    storage = Storage(db_path)
    
    yield storage
    
    # Cleanup
    if os.path.exists(db_path):
        os.remove(db_path)


@pytest.fixture
def sample_buffer():
    """Create a sample conversation buffer for testing."""
    buffer = ConversationBuffer(
        buffer_id="test_buffer_001",
        channel_id="C001"
    )
    
    # Add some sample messages
    buffer.add_message({
        "text": "This is a test message about product strategy and API design.",
        "user": "U001",
        "channel_id": "C001",
        "ts": "1234567890.001"
    })
    buffer.add_message({
        "text": "I think we should focus on the user experience and make the onboarding flow smoother.",
        "user": "U002",
        "channel_id": "C001",
        "ts": "1234567890.002"
    })
    buffer.add_message({
        "text": "Good point. What if we add a tutorial that walks users through the key features?",
        "user": "U001",
        "channel_id": "C001",
        "ts": "1234567890.003"
    })
    
    return buffer


@pytest.fixture
def mock_gemini_response():
    """Mock Gemini API response for testing."""
    mock_response = Mock()
    mock_response.text = """{
        "x_draft": "Most founders optimize for valuation. The best optimize for learning rate.",
        "confidence": 0.85,
        "topic": "Startup Strategy"
    }"""
    return mock_response


@pytest.fixture
def mock_gemini_linkedin_response():
    """Mock Gemini API response for LinkedIn draft."""
    mock_response = Mock()
    mock_response.text = """{
        "linkedin_draft": "We debated for weeks: freemium or paid-only?\\n\\nThe data was clear—60% of free users never upgrade. But here's what the data didn't show: 100% of our word-of-mouth growth came from free users.\\n\\nWe decided to keep freemium but add usage caps. The result? 2x signups, same conversion rate, but now we're not subsidizing power users.\\n\\nLesson: Don't just look at conversion funnels. Look at acquisition loops.\\n\\nWhat's your take on freemium? 👇",
        "confidence": 0.90
    }"""
    return mock_response


@pytest.fixture
def mock_gemini_model(mock_gemini_response, mock_gemini_linkedin_response):
    """Mock Gemini model for testing."""
    mock_model = MagicMock()
    
    # Set up side_effect to return different responses for X and LinkedIn
    mock_model.generate_content.side_effect = [
        mock_gemini_response,
        mock_gemini_linkedin_response
    ]
    
    return mock_model


@pytest.fixture
def sample_suggestion():
    """Sample suggestion data for testing."""
    return {
        "x_draft": "Most founders optimize for valuation. The best optimize for learning rate.",
        "linkedin_draft": "We debated for weeks: freemium or paid-only?\n\nThe data was clear—60% of free users never upgrade. But here's what the data didn't show: 100% of our word-of-mouth growth came from free users.\n\nWe decided to keep freemium but add usage caps. The result? 2x signups, same conversion rate, but now we're not subsidizing power users.\n\nLesson: Don't just look at conversion funnels. Look at acquisition loops.\n\nWhat's your take on freemium? 👇",
        "confidence": 0.875,
        "topic": "Startup Strategy",
        "buffer_id": "test_buffer_001",
        "channel_id": "C001",
        "start_time": datetime.now().isoformat(),
        "end_time": datetime.now().isoformat()
    }
