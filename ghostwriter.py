"""
Module 3: Ghostwriter LLM Integration
Transforms buffered conversations into platform-specific content suggestions
using Google Gemini Flash.
"""

import google.generativeai as genai
import json
import logging
from typing import Dict, Optional
from config import Config
from buffer_engine import ConversationBuffer

logger = logging.getLogger(__name__)


class Ghostwriter:
    """
    LLM-powered content generator for X (Twitter) and LinkedIn.
    Uses Google Gemini Flash for fast, free content generation.
    """
    
    def __init__(self):
        """Initialize Gemini client."""
        try:
            genai.configure(api_key=Config.GEMINI_API_KEY)
            self.model = genai.GenerativeModel('gemini-2.5-flash')
            logger.info("Gemini Flash model initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini: {e}")
            raise
    
    def generate_suggestions(self, buffer: ConversationBuffer, refinement_instruction: Optional[str] = None) -> Optional[Dict]:
        """
        Generate X and LinkedIn content suggestions from conversation buffer.
        
        Args:
            buffer: ConversationBuffer with messages to process
            refinement_instruction: Optional instruction to refine content
        
        Returns:
            Dict with x_draft, linkedin_draft, confidence, topic, etc.
            None if generation fails or confidence is too low
        """
        try:
            conversation_text = buffer.get_conversation_text()
            
            logger.info(f"Generating suggestions for buffer {buffer.buffer_id}")
            
            # Generate X (Twitter) draft
            x_draft, x_confidence, topic = self._generate_x_draft(conversation_text, refinement_instruction)
            
            if not x_draft:
                logger.warning("Failed to generate X draft")
                return None
            
            # Generate LinkedIn draft
            linkedin_draft, linkedin_confidence = self._generate_linkedin_draft(
                conversation_text, topic, refinement_instruction
            )
            
            if not linkedin_draft:
                logger.warning("Failed to generate LinkedIn draft")
                return None
            
            # Calculate average confidence
            avg_confidence = (x_confidence + linkedin_confidence) / 2
            
            # Validate content quality
            if not self._validate_content(x_draft, "x"):
                logger.warning("X draft failed quality validation")
                return None
            
            if not self._validate_content(linkedin_draft, "linkedin"):
                logger.warning("LinkedIn draft failed quality validation")
                return None
            
            # Check confidence threshold
            if avg_confidence < 0.7:
                logger.info(f"Confidence too low ({avg_confidence:.2f}) - skipping")
                return None
            
            suggestion = {
                "x_draft": x_draft,
                "linkedin_draft": linkedin_draft,
                "confidence": avg_confidence,
                "topic": topic,
                "buffer_id": buffer.buffer_id,
                "channel_id": buffer.channel_id,
                "start_time": buffer.start_time.isoformat(),
                "end_time": buffer.last_message_time.isoformat()
            }
            
            logger.info(
                f"Successfully generated suggestions - "
                f"Topic: {topic}, Confidence: {avg_confidence:.2f}"
            )
            
            return suggestion
            
        except Exception as e:
            logger.error(f"Error generating suggestions: {e}")
            return None
    
    def _generate_x_draft(self, conversation_text: str, refinement_instruction: Optional[str] = None) -> tuple:
        """
        Generate X (Twitter) draft.
        
        Returns:
            (draft_text, confidence, topic)
        """
        prompt = f"""You are a ghostwriter for a technical CEO.

Context: Below is a conversation between two founders:

{conversation_text}

Task: Extract ONE high-signal insight and write a punchy tweet (240 chars max).

Style Guidelines:
- Start with a hook (contrarian take, surprising stat, or question)
- Use simple words, avoid jargon
- Be specific, not generic
- End with a zinger or call-to-action
- NO promotional content ("we're hiring", "check out our product")
- NO generic motivation ("hustle harder", "stay focused")

Good Examples:
- "Most founders optimize for valuation. The best optimize for learning rate."
- "We just spent 3 hours debugging. The bug? A missing comma. The lesson? Priceless."
- "Freemium paradox: 60% never upgrade, but 100% of our growth comes from them."

Bad Examples:
- "Excited to announce..." (promotional)
- "Hustle harder!" (generic motivation)
- "Just shipped a new feature" (not insightful)

Output ONLY valid JSON in this exact format:
{{
  "x_draft": "your tweet here (max 240 chars)",
  "confidence": 0.85,
  "topic": "Pricing Strategy"
}}"""

        if refinement_instruction:
            prompt += f"\n\nIMPORTANT REFINEMENT INSTRUCTION: {refinement_instruction}\nPlease rewrite the content following this specific instruction."

        try:
            response = self.model.generate_content(prompt)
            
            # Extract JSON from response
            response_text = response.text.strip()
            
            # Remove markdown code blocks if present
            if response_text.startswith("```"):
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]
                response_text = response_text.strip()
            
            data = json.loads(response_text)
            
            return (
                data.get("x_draft", ""),
                data.get("confidence", 0.5),
                data.get("topic", "General")
            )
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse X draft JSON: {e}")
            logger.debug(f"Response text: {response.text}")
            return ("", 0.0, "")
        except Exception as e:
            logger.error(f"Error generating X draft: {e}")
            return ("", 0.0, "")
    
    def _generate_linkedin_draft(self, conversation_text: str, topic: str, refinement_instruction: Optional[str] = None) -> tuple:
        """
        Generate LinkedIn draft.
        
        Returns:
            (draft_text, confidence)
        """
        prompt = f"""You are a ghostwriter for a technical CEO sharing founder lessons.

Context: Below is a conversation between two founders:

{conversation_text}

Topic identified: {topic}

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

Bad Examples:
- Generic advice without specifics
- Promotional content about your product
- Motivational quotes without substance

Output ONLY valid JSON in this exact format:
{{
  "linkedin_draft": "your post here (150-250 words)",
  "confidence": 0.90
}}"""

        if refinement_instruction:
            prompt += f"\n\nIMPORTANT REFINEMENT INSTRUCTION: {refinement_instruction}\nPlease rewrite the content following this specific instruction."

        try:
            response = self.model.generate_content(prompt)
            
            # Extract JSON from response
            response_text = response.text.strip()
            
            # Remove markdown code blocks if present
            if response_text.startswith("```"):
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]
                response_text = response_text.strip()
            
            data = json.loads(response_text)
            
            return (
                data.get("linkedin_draft", ""),
                data.get("confidence", 0.5)
            )
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LinkedIn draft JSON: {e}")
            logger.debug(f"Response text: {response.text}")
            return ("", 0.0)
        except Exception as e:
            logger.error(f"Error generating LinkedIn draft: {e}")
            return ("", 0.0)
    
    def _validate_content(self, draft: str, platform: str) -> bool:
        """
        Validate content quality.
        
        Args:
            draft: Content to validate
            platform: "x" or "linkedin"
        
        Returns:
            bool: True if content passes validation
        """
        if not draft or len(draft.strip()) == 0:
            return False
        
        # Check length constraints
        if platform == "x":
            if len(draft) > 280:
                logger.warning(f"X draft too long: {len(draft)} chars")
                return False
            if len(draft) < 50:
                logger.warning(f"X draft too short: {len(draft)} chars")
                return False
        
        elif platform == "linkedin":
            word_count = len(draft.split())
            if word_count > 300:
                logger.warning(f"LinkedIn draft too long: {word_count} words")
                return False
            if word_count < 100:
                logger.warning(f"LinkedIn draft too short: {word_count} words")
                return False
        
        # Check for promotional content
        promo_keywords = [
            "we're hiring",
            "we're excited to announce",
            "check out our",
            "join our team",
            "now available",
            "launching soon"
        ]
        draft_lower = draft.lower()
        for keyword in promo_keywords:
            if keyword in draft_lower:
                logger.warning(f"Promotional content detected: {keyword}")
                return False
        
        # Check for generic motivational content
        generic_phrases = [
            "hustle harder",
            "stay focused",
            "never give up",
            "believe in yourself",
            "dream big",
            "work hard play hard"
        ]
        for phrase in generic_phrases:
            if phrase in draft_lower:
                logger.warning(f"Generic content detected: {phrase}")
                return False
        
        return True
