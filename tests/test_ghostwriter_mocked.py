"""
Unit tests for Ghostwriter module with mocked LLM responses.
Tests content generation, validation, and JSON parsing without making real API calls.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import json
from ghostwriter import Ghostwriter
from buffer_engine import ConversationBuffer


@pytest.mark.unit
class TestContentGeneration:
    """Test content generation with mocked Gemini responses."""
    
    @patch('google.generativeai.GenerativeModel')
    def test_generate_suggestions_success(self, mock_model_class, sample_buffer):
        """Test successful suggestion generation with mocked responses."""
        # Create mock responses
        mock_x_response = Mock()
        mock_x_response.text = json.dumps({
            "x_draft": "Most founders optimize for valuation. The best optimize for learning rate.",
            "confidence": 0.85,
            "topic": "Startup Strategy"
        })
        
        mock_linkedin_response = Mock()
        mock_linkedin_response.text = json.dumps({
            "linkedin_draft": "We debated for weeks: freemium or paid-only?\n\nThe data was clear—60% of free users never upgrade. But here's what the data didn't show: 100% of our word-of-mouth growth came from free users.\n\nWe decided to keep freemium but add usage caps. The result? 2x signups, same conversion rate, but now we're not subsidizing power users who never pay.\n\nLesson: Don't just look at conversion funnels. Look at acquisition loops. Free users are your growth engine even if they never convert.\n\nThis changed how we think about pricing entirely. Now we optimize for viral coefficient first, revenue second.\n\nWhat's your take on freemium? 👇",
            "confidence": 0.90
        })
        
        # Setup mock model
        mock_instance = MagicMock()
        mock_instance.generate_content.side_effect = [mock_x_response, mock_linkedin_response]
        mock_model_class.return_value = mock_instance
        
        # Create ghostwriter and generate
        ghostwriter = Ghostwriter()
        suggestion = ghostwriter.generate_suggestions(sample_buffer)
        
        # Verify suggestion was generated
        assert suggestion is not None
        assert 'x_draft' in suggestion
        assert 'linkedin_draft' in suggestion
        assert 'confidence' in suggestion
        assert 'topic' in suggestion
        assert suggestion['topic'] == "Startup Strategy"
    
    @patch('google.generativeai.GenerativeModel')
    def test_generate_suggestions_low_confidence(self, mock_model_class, sample_buffer):
        """Test that low confidence suggestions are rejected."""
        # Create mock responses with low confidence
        mock_x_response = Mock()
        mock_x_response.text = json.dumps({
            "x_draft": "Generic tweet",
            "confidence": 0.3,
            "topic": "General"
        })
        
        mock_linkedin_response = Mock()
        mock_linkedin_response.text = json.dumps({
            "linkedin_draft": "Generic post",
            "confidence": 0.4
        })
        
        mock_instance = MagicMock()
        mock_instance.generate_content.side_effect = [mock_x_response, mock_linkedin_response]
        mock_model_class.return_value = mock_instance
        
        ghostwriter = Ghostwriter()
        suggestion = ghostwriter.generate_suggestions(sample_buffer)
        
        # Should return None due to low confidence (avg = 0.35 < 0.7)
        assert suggestion is None


@pytest.mark.unit
class TestContentValidation:
    """Test content validation rules."""
    
    def test_validate_x_length_too_long(self):
        """Test that X drafts over 280 chars are rejected."""
        ghostwriter = Ghostwriter()
        
        long_draft = "a" * 300  # 300 characters
        assert ghostwriter._validate_content(long_draft, "x") is False
    
    def test_validate_x_length_too_short(self):
        """Test that X drafts under 50 chars are rejected."""
        ghostwriter = Ghostwriter()
        
        short_draft = "Too short"
        assert ghostwriter._validate_content(short_draft, "x") is False
    
    def test_validate_x_length_valid(self):
        """Test that X drafts within range are accepted."""
        ghostwriter = Ghostwriter()
        
        valid_draft = "Most founders optimize for valuation. The best optimize for learning rate."
        assert ghostwriter._validate_content(valid_draft, "x") is True
    
    def test_validate_linkedin_length_too_long(self):
        """Test that LinkedIn posts over 300 words are rejected."""
        ghostwriter = Ghostwriter()
        
        long_draft = " ".join(["word"] * 350)  # 350 words
        assert ghostwriter._validate_content(long_draft, "linkedin") is False
    
    def test_validate_linkedin_length_too_short(self):
        """Test that LinkedIn posts under 100 words are rejected."""
        ghostwriter = Ghostwriter()
        
        short_draft = " ".join(["word"] * 50)  # 50 words
        assert ghostwriter._validate_content(short_draft, "linkedin") is False
    
    def test_validate_linkedin_length_valid(self):
        """Test that LinkedIn posts within range are accepted."""
        ghostwriter = Ghostwriter()
        
        valid_draft = " ".join(["word"] * 150)  # 150 words
        assert ghostwriter._validate_content(valid_draft, "linkedin") is True
    
    def test_validate_promotional_content_rejected(self):
        """Test that promotional content is rejected."""
        ghostwriter = Ghostwriter()
        
        promo_drafts = [
            "We're excited to announce our new product launch!",
            "We're hiring for multiple positions. Check out our careers page!",
            "Join our team and help us build the future!",
            "Now available on the App Store!",
            "Launching soon - stay tuned!"
        ]
        
        for draft in promo_drafts:
            assert ghostwriter._validate_content(draft, "x") is False, f"Should reject: {draft}"
    
    def test_validate_generic_content_rejected(self):
        """Test that generic motivational content is rejected."""
        ghostwriter = Ghostwriter()
        
        generic_drafts = [
            "Hustle harder and you'll succeed!",
            "Stay focused on your goals and never give up!",
            "Believe in yourself and dream big!",
            "Work hard play hard is the key to success!"
        ]
        
        for draft in generic_drafts:
            assert ghostwriter._validate_content(draft, "x") is False, f"Should reject: {draft}"


@pytest.mark.unit
class TestJSONParsing:
    """Test JSON parsing from LLM responses."""
    
    @patch('google.generativeai.GenerativeModel')
    def test_json_parsing_with_markdown_code_blocks(self, mock_model_class, sample_buffer):
        """Test that JSON is correctly extracted from markdown code blocks."""
        # Mock response with markdown code blocks
        mock_response = Mock()
        mock_response.text = """```json
{
    "x_draft": "Most founders optimize for valuation. The best optimize for learning rate.",
    "confidence": 0.85,
    "topic": "Test"
}
```"""
        
        mock_linkedin_response = Mock()
        linkedin_text = "Test post with enough words to pass validation. " + " ".join([f"word{i}" for i in range(100)])
        mock_linkedin_response.text = f"""```json
{{
    "linkedin_draft": "{linkedin_text}",
    "confidence": 0.90
}}
```"""
        
        mock_instance = MagicMock()
        mock_instance.generate_content.side_effect = [mock_response, mock_linkedin_response]
        mock_model_class.return_value = mock_instance
        
        ghostwriter = Ghostwriter()
        suggestion = ghostwriter.generate_suggestions(sample_buffer)
        
        # Should successfully parse despite markdown wrapper
        assert suggestion is not None
        assert suggestion['x_draft'] == "Most founders optimize for valuation. The best optimize for learning rate."
    
    @patch('google.generativeai.GenerativeModel')
    def test_json_parsing_plain_json(self, mock_model_class, sample_buffer):
        """Test that plain JSON (no markdown) is parsed correctly."""
        mock_response = Mock()
        mock_response.text = json.dumps({
            "x_draft": "Plain JSON tweet that is long enough to pass validation checks",
            "confidence": 0.85,
            "topic": "Test"
        })
        
        mock_linkedin_response = Mock()
        mock_linkedin_response.text = json.dumps({
            "linkedin_draft": "Plain JSON post " + " ".join(["word"] * 120),
            "confidence": 0.90
        })
        
        mock_instance = MagicMock()
        mock_instance.generate_content.side_effect = [mock_response, mock_linkedin_response]
        mock_model_class.return_value = mock_instance
        
        ghostwriter = Ghostwriter()
        suggestion = ghostwriter.generate_suggestions(sample_buffer)
        
        assert suggestion is not None
    
    @patch('google.generativeai.GenerativeModel')
    def test_json_parsing_invalid_json_returns_none(self, mock_model_class, sample_buffer):
        """Test that invalid JSON returns None gracefully."""
        mock_response = Mock()
        mock_response.text = "This is not valid JSON at all!"
        
        mock_instance = MagicMock()
        mock_instance.generate_content.return_value = mock_response
        mock_model_class.return_value = mock_instance
        
        ghostwriter = Ghostwriter()
        suggestion = ghostwriter.generate_suggestions(sample_buffer)
        
        # Should return None for invalid JSON
        assert suggestion is None
