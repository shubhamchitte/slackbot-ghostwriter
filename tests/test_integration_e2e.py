"""
Integration tests for end-to-end flows with REAL Gemini API calls.
WARNING: These tests consume API tokens. Run sparingly.

Run with: pytest -m integration -v
Skip with: pytest -m "not integration" -v
"""

import pytest
import os
from buffer_engine import ConversationBuffer, BufferEngine
from ghostwriter import Ghostwriter
from storage import Storage
from tests.fixtures.sample_conversations import HIGH_SIGNAL_CONVERSATION


@pytest.mark.integration
class TestRealLLMGeneration:
    """Integration tests with real Gemini API calls."""
    
    def test_real_llm_short_conversation(self):
        """
        Test real LLM generation with a short conversation.
        Estimated tokens: ~500
        """
        # Skip if no API key
        if not os.getenv('GEMINI_API_KEY'):
            pytest.skip("GEMINI_API_KEY not set")
        
        # Create buffer with short conversation
        buffer = ConversationBuffer("integration_test_001", "C001")
        
        # Add 3 messages from high-signal conversation
        for msg in HIGH_SIGNAL_CONVERSATION[:3]:
            buffer.add_message(msg)
        
        # Generate with real LLM
        ghostwriter = Ghostwriter()
        suggestion = ghostwriter.generate_suggestions(buffer)
        
        # Verify suggestion was generated
        assert suggestion is not None, "Should generate suggestion for high-signal conversation"
        assert 'x_draft' in suggestion
        assert 'linkedin_draft' in suggestion
        assert len(suggestion['x_draft']) > 0
        assert len(suggestion['linkedin_draft']) > 0
        
        # Verify content quality
        assert len(suggestion['x_draft']) <= 280, "X draft should be under 280 chars"
        linkedin_words = len(suggestion['linkedin_draft'].split())
        assert 100 <= linkedin_words <= 300, f"LinkedIn draft should be 100-300 words, got {linkedin_words}"
        
        print(f"\n✅ Generated X draft: {suggestion['x_draft']}")
        print(f"✅ Generated LinkedIn draft (first 100 chars): {suggestion['linkedin_draft'][:100]}...")
    
    def test_real_llm_medium_conversation(self):
        """
        Test real LLM generation with a medium conversation.
        Estimated tokens: ~800
        """
        if not os.getenv('GEMINI_API_KEY'):
            pytest.skip("GEMINI_API_KEY not set")
        
        # Create buffer with full high-signal conversation
        buffer = ConversationBuffer("integration_test_002", "C002")
        
        for msg in HIGH_SIGNAL_CONVERSATION:
            buffer.add_message(msg)
        
        # Calculate signal score
        score = buffer.calculate_signal_score()
        assert score > 0.6, f"High-signal conversation should score > 0.6, got {score}"
        
        # Generate with real LLM
        ghostwriter = Ghostwriter()
        suggestion = ghostwriter.generate_suggestions(buffer)
        
        assert suggestion is not None
        assert suggestion['confidence'] >= 0.7, "Should have high confidence for good conversation"
        
        print(f"\n✅ Signal score: {score:.2f}")
        print(f"✅ Confidence: {suggestion['confidence']:.2f}")
        print(f"✅ Topic: {suggestion['topic']}")
    
    def test_full_pipeline_buffer_to_storage(self, temp_db):
        """
        Test complete pipeline: buffer → LLM → storage.
        Estimated tokens: ~1000
        """
        if not os.getenv('GEMINI_API_KEY'):
            pytest.skip("GEMINI_API_KEY not set")
        
        # Create buffer
        buffer = ConversationBuffer("integration_test_003", "C003")
        for msg in HIGH_SIGNAL_CONVERSATION:
            buffer.add_message(msg)
        
        # Calculate signal score
        buffer.calculate_signal_score()
        
        # Save buffer
        temp_db.save_buffer(buffer)
        
        # Generate suggestion
        ghostwriter = Ghostwriter()
        suggestion = ghostwriter.generate_suggestions(buffer)
        
        assert suggestion is not None
        
        # Save suggestion
        temp_db.save_suggestion(suggestion)
        
        # Retrieve and verify
        retrieved = temp_db.get_suggestion(buffer.buffer_id)
        assert retrieved is not None
        assert retrieved['x_draft'] == suggestion['x_draft']
        assert retrieved['linkedin_draft'] == suggestion['linkedin_draft']
        
        # Test user action
        temp_db.record_user_action(buffer.buffer_id, 'approved')
        
        # Verify stats
        stats = temp_db.get_stats()
        assert stats['total_buffers'] == 1
        assert stats['total_suggestions'] == 1
        assert stats['approval_rate'] == 1.0
        
        print(f"\n✅ Full pipeline test completed successfully")
        print(f"✅ Buffer saved, suggestion generated and stored, user action recorded")


@pytest.mark.integration
class TestBufferEngineIntegration:
    """Integration tests for buffer engine with real processing."""
    
    def test_buffer_engine_callback_flow(self):
        """
        Test that buffer engine correctly triggers callback when buffer is ready.
        Note: This test doesn't make LLM calls, just tests the flow.
        """
        callback_triggered = []
        
        def test_callback(buffer):
            callback_triggered.append(buffer)
        
        engine = BufferEngine(on_buffer_ready_callback=test_callback)
        
        # Add high-signal messages
        for msg in HIGH_SIGNAL_CONVERSATION:
            engine.add_message(msg)
        
        # Force close buffer
        engine.force_close_buffer("C001")
        
        # Verify callback was triggered
        assert len(callback_triggered) == 1
        assert callback_triggered[0].buffer_id is not None
        assert callback_triggered[0].signal_score > 0.6
        
        # Cleanup
        engine.stop()
        
        print(f"\n✅ Buffer engine callback flow working correctly")
