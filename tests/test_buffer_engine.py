"""
Unit tests for BufferEngine module.
Tests noise filtering, signal scoring, and message buffering logic.
"""

import pytest
from datetime import datetime, timedelta
from buffer_engine import BufferEngine, ConversationBuffer
from tests.fixtures.sample_conversations import (
    HIGH_SIGNAL_CONVERSATION,
    LOW_SIGNAL_CONVERSATION,
    MEDIUM_SIGNAL_CONVERSATION,
    SHORT_CONVERSATION,
    CODE_HEAVY_CONVERSATION
)


@pytest.mark.unit
class TestNoiseFiltering:
    """Test noise filtering functionality."""
    
    def test_scheduling_keywords_filtered(self):
        """Test that messages with scheduling keywords are filtered as noise."""
        engine = BufferEngine()
        
        # Test various scheduling keywords
        scheduling_messages = [
            "Let's schedule a call for tomorrow",
            "Can we have a meeting at 3pm?",
            "I'll send you a calendar invite",
            "Let's jump on a Zoom call",
            "What's your availability this week?"
        ]
        
        for msg in scheduling_messages:
            assert engine._is_noise(msg) is True, f"Should filter: {msg}"
    
    def test_short_messages_filtered(self):
        """Test that messages below minimum length are filtered."""
        engine = BufferEngine()
        
        short_messages = [
            "ok",
            "cool",
            "sounds good",
            "yeah sure",
            "got it",
            "👍",
            ":+1:"
        ]
        
        for msg in short_messages:
            assert engine._is_noise(msg) is True, f"Should filter: {msg}"
    
    def test_acknowledgments_filtered(self):
        """Test that pure acknowledgments are filtered."""
        engine = BufferEngine()
        
        ack_messages = [
            "okay",
            "yep",
            "sure",
            "lol",
            "haha",
            "nice"
        ]
        
        for msg in ack_messages:
            assert engine._is_noise(msg) is True, f"Should filter: {msg}"
    
    def test_code_blocks_without_context_filtered(self):
        """Test that pure code blocks without context are filtered."""
        engine = BufferEngine()
        
        # Pure code block (>80% code, <20 words)
        code_only = "```python\ndef foo():\n    return 'bar'\n```"
        assert engine._is_noise(code_only) is True
        
        # Code with context (should NOT be filtered)
        code_with_context = "Here's the solution to the bug we discussed:\n```python\ndef foo():\n    return 'bar'\n```\nThis fixes the issue by returning a string instead of None."
        assert engine._is_noise(code_with_context) is False


@pytest.mark.unit
class TestSignalScoring:
    """Test signal scoring algorithm."""
    
    def test_high_signal_conversation_scores_high(self):
        """Test that high-signal conversations get high scores."""
        buffer = ConversationBuffer("test_001", "C001")
        
        for msg in HIGH_SIGNAL_CONVERSATION:
            buffer.add_message(msg)
        
        score = buffer.calculate_signal_score()
        
        # High-signal conversation should score > 0.6
        assert score > 0.6, f"Expected score > 0.6, got {score}"
        assert score <= 1.0, f"Score should not exceed 1.0, got {score}"
    
    def test_low_signal_conversation_scores_low(self):
        """Test that low-signal conversations get low scores."""
        buffer = ConversationBuffer("test_002", "C002")
        
        for msg in LOW_SIGNAL_CONVERSATION:
            buffer.add_message(msg)
        
        score = buffer.calculate_signal_score()
        
        # Low-signal conversation should score < 0.6
        assert score < 0.6, f"Expected score < 0.6, got {score}"
        assert score >= 0.0, f"Score should not be negative, got {score}"


@pytest.mark.unit
class TestBufferManagement:
    """Test buffer creation and message grouping."""
    
    def test_buffer_groups_messages_correctly(self):
        """Test that messages are added to buffer correctly."""
        buffer = ConversationBuffer("test_003", "C003")
        
        initial_count = len(buffer.messages)
        assert initial_count == 0
        
        # Add messages
        for msg in MEDIUM_SIGNAL_CONVERSATION:
            buffer.add_message(msg)
        
        assert len(buffer.messages) == len(MEDIUM_SIGNAL_CONVERSATION)
        assert buffer.channel_id == "C003"
    
    def test_topic_keyword_extraction(self):
        """Test that topic keywords are extracted from messages."""
        buffer = ConversationBuffer("test_004", "C004")
        
        # Add messages with technical terms
        buffer.add_message({
            "text": "We need to optimize the API performance and improve the database queries.",
            "user": "U001",
            "channel_id": "C004",
            "ts": "123.001"
        })
        buffer.add_message({
            "text": "The UI is slow because of the LLM inference latency.",
            "user": "U002",
            "channel_id": "C004",
            "ts": "123.002"
        })
        
        # Check that keywords were extracted
        assert len(buffer.topic_keywords) > 0
        # Should contain technical terms like API, UI, LLM
        keywords_str = " ".join(buffer.topic_keywords)
        assert any(term in keywords_str for term in ["API", "UI", "LLM"])
    
    def test_buffer_time_tracking(self):
        """Test that buffer tracks message timestamps correctly."""
        buffer = ConversationBuffer("test_005", "C005")
        
        start_time = buffer.start_time
        
        # Add a message
        buffer.add_message({
            "text": "Test message",
            "user": "U001",
            "channel_id": "C005",
            "ts": "123.001"
        })
        
        # Last message time should be updated
        assert buffer.last_message_time >= start_time
    
    def test_buffer_to_dict_conversion(self):
        """Test that buffer can be converted to dictionary."""
        buffer = ConversationBuffer("test_006", "C006")
        
        buffer.add_message({
            "text": "Test message",
            "user": "U001",
            "channel_id": "C006",
            "ts": "123.001"
        })
        
        buffer_dict = buffer.to_dict()
        
        assert buffer_dict["buffer_id"] == "test_006"
        assert buffer_dict["channel_id"] == "C006"
        assert buffer_dict["message_count"] == 1
        assert "signal_score" in buffer_dict
        assert "topic_keywords" in buffer_dict
        assert "raw_messages" in buffer_dict


@pytest.mark.unit
class TestBufferEngine:
    """Test BufferEngine orchestration."""
    
    def test_engine_filters_noise_messages(self):
        """Test that engine filters noise messages before adding to buffer."""
        callback_called = []
        
        def mock_callback(buffer):
            callback_called.append(buffer)
        
        engine = BufferEngine(on_buffer_ready_callback=mock_callback)
        
        # Add noise message
        engine.add_message({
            "text": "ok",
            "user": "U001",
            "channel_id": "C007",
            "ts": "123.001"
        })
        
        # Should not create a buffer for noise
        assert "C007" not in engine.active_buffers
    
    def test_engine_creates_buffer_for_valid_messages(self):
        """Test that engine creates buffer for non-noise messages."""
        callback_called = []
        
        def mock_callback(buffer):
            callback_called.append(buffer)
        
        engine = BufferEngine(on_buffer_ready_callback=mock_callback)
        
        # Add valid message
        engine.add_message({
            "text": "We should refactor the authentication module to use JWT tokens instead of session cookies.",
            "user": "U001",
            "channel_id": "C008",
            "ts": "123.001"
        })
        
        # Should create a buffer
        assert "C008" in engine.active_buffers
        assert len(engine.active_buffers["C008"].messages) == 1
