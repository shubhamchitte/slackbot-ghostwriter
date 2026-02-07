"""
Module 2: Buffer Engine
Groups conversational messages by topic/thread context.
Implements noise filtering to distinguish 'founder banter' from 'actual insights'.
"""

import time
import threading
from datetime import datetime, timedelta
from collections import defaultdict
from typing import List, Dict, Optional
import logging
import re

from config import Config

logger = logging.getLogger(__name__)


class ConversationBuffer:
    """Represents a buffered conversation window."""
    
    def __init__(self, buffer_id: str, channel_id: str):
        self.buffer_id = buffer_id
        self.channel_id = channel_id
        self.messages: List[Dict] = []
        self.start_time = datetime.now()
        self.last_message_time = datetime.now()
        self.topic_keywords: List[str] = []
        self.signal_score = 0.0
    
    def add_message(self, message: Dict):
        """Add a message to the buffer."""
        self.messages.append(message)
        self.last_message_time = datetime.now()
        self._update_topic_keywords(message["text"])
    
    def _update_topic_keywords(self, text: str):
        """Extract and update topic keywords from message text."""
        # Simple keyword extraction - look for capitalized words and technical terms
        words = re.findall(r'\b[A-Z][a-z]+\b|\b(?:API|UI|UX|MVP|SaaS|AI|ML|LLM)\b', text)
        self.topic_keywords.extend(words)
        # Keep only unique keywords (last 10)
        self.topic_keywords = list(set(self.topic_keywords))[-10:]
    
    def calculate_signal_score(self) -> float:
        """
        Calculate signal score for this buffer.
        Higher score = more likely to contain valuable insights.
        
        Returns:
            float: Signal score between 0.0 and 1.0
        """
        if not self.messages:
            return 0.0
        
        score = 0.0
        total_words = 0
        question_count = 0
        technical_terms = 0
        first_person_insights = 0
        
        for msg in self.messages:
            text = msg["text"]
            words = text.split()
            word_count = len(words)
            total_words += word_count
            
            # Count questions (debates are valuable)
            if "?" in text:
                question_count += 1
            
            # Count technical terms
            technical_patterns = [
                r'\b(?:API|SDK|database|server|client|backend|frontend|deploy|bug|feature|code|function|class|algorithm)\b',
                r'\b(?:product|market|user|customer|revenue|growth|metric|KPI|conversion)\b',
                r'\b(?:AI|ML|LLM|model|training|inference|prompt)\b'
            ]
            for pattern in technical_patterns:
                technical_terms += len(re.findall(pattern, text, re.IGNORECASE))
            
            # Count first-person insights
            insight_patterns = [
                r'\bI (?:learned|realized|discovered|found|think|believe)\b',
                r'\bWe (?:should|could|need to|decided|learned)\b',
                r'\b(?:insight|lesson|takeaway|conclusion)\b'
            ]
            for pattern in insight_patterns:
                first_person_insights += len(re.findall(pattern, text, re.IGNORECASE))
        
        avg_message_length = total_words / len(self.messages)
        
        # Scoring algorithm
        # 1. Message length (sweet spot: 20-150 words per message)
        if 20 <= avg_message_length <= 150:
            score += 0.3
        elif 10 <= avg_message_length < 20:
            score += 0.15
        
        # 2. Questions indicate debate/discussion
        if question_count >= 2:
            score += 0.25
        elif question_count == 1:
            score += 0.1
        
        # 3. Technical terms indicate substantive discussion
        if technical_terms >= 5:
            score += 0.25
        elif technical_terms >= 2:
            score += 0.15
        
        # 4. First-person insights are gold
        if first_person_insights >= 2:
            score += 0.3
        elif first_person_insights >= 1:
            score += 0.15
        
        # 5. Conversation length (more messages = more context)
        if len(self.messages) >= 5:
            score += 0.1
        
        self.signal_score = min(score, 1.0)
        return self.signal_score
    
    def get_conversation_text(self) -> str:
        """Get all messages as a single conversation string."""
        return "\n".join([f"User: {msg['text']}" for msg in self.messages])
    
    def to_dict(self) -> Dict:
        """Convert buffer to dictionary for storage."""
        return {
            "buffer_id": self.buffer_id,
            "channel_id": self.channel_id,
            "start_time": self.start_time.isoformat(),
            "end_time": self.last_message_time.isoformat(),
            "message_count": len(self.messages),
            "signal_score": self.signal_score,
            "topic_keywords": self.topic_keywords,
            "raw_messages": self.messages
        }


class BufferEngine:
    """
    Manages conversation buffers and noise filtering.
    This is the 'intelligence layer' that distinguishes banter from insights.
    """
    
    def __init__(self, on_buffer_ready_callback=None):
        """
        Initialize Buffer Engine.
        
        Args:
            on_buffer_ready_callback: Function to call when buffer is ready for LLM processing
        """
        self.active_buffers: Dict[str, ConversationBuffer] = {}
        self.on_buffer_ready = on_buffer_ready_callback
        self.lock = threading.Lock()
        
        # Start background thread to check for closed buffers
        self.running = True
        self.monitor_thread = threading.Thread(target=self._monitor_buffers, daemon=True)
        self.monitor_thread.start()
        
        logger.info("Buffer Engine initialized")
    
    def add_message(self, message: Dict):
        """
        Add a message to the appropriate buffer.
        
        Args:
            message: Message data from Slack
        """
        # First, check if message is noise
        if self._is_noise(message["text"]):
            logger.debug(f"Filtered out noise message: {message['text'][:50]}...")
            return
        
        channel_id = message["channel_id"]
        
        with self.lock:
            # Get or create buffer for this channel
            if channel_id not in self.active_buffers:
                buffer_id = f"{channel_id}_{int(time.time())}"
                self.active_buffers[channel_id] = ConversationBuffer(buffer_id, channel_id)
                logger.info(f"Created new buffer: {buffer_id}")
            
            # Add message to buffer
            buffer = self.active_buffers[channel_id]
            buffer.add_message(message)
            logger.info(f"Added message to buffer {buffer.buffer_id} (total: {len(buffer.messages)})")
    
    def _is_noise(self, text: str) -> bool:
        """
        Determine if a message is 'noise' (admin talk, not insights).
        
        Args:
            text: Message text
        
        Returns:
            bool: True if message is noise
        """
        text_lower = text.lower()
        
        # 1. Check for scheduling/admin keywords
        for keyword in Config.NOISE_KEYWORDS:
            if keyword in text_lower:
                logger.debug(f"Noise detected: contains keyword '{keyword}'")
                return True
        
        # 2. Check message length (too short = likely acknowledgment)
        word_count = len(text.split())
        if word_count < Config.MIN_MESSAGE_LENGTH:
            logger.debug(f"Noise detected: too short ({word_count} words)")
            return True
        
        # 3. Check for pure acknowledgments
        ack_patterns = [
            r'^(?:ok|okay|sure|yep|yeah|yup|got it|sounds good|cool|nice|lol|haha)\.?$',
            r'^👍$',
            r'^:\w+:$'  # Just emoji
        ]
        for pattern in ack_patterns:
            if re.match(pattern, text_lower.strip()):
                logger.debug("Noise detected: pure acknowledgment")
                return True
        
        # 4. Check for pure code blocks without context
        # If message is >80% code and <20 words of text, it's noise
        code_block_pattern = r'```[\s\S]*?```|`[^`]+`'
        code_blocks = re.findall(code_block_pattern, text)
        if code_blocks:
            code_length = sum(len(block) for block in code_blocks)
            text_length = len(text)
            if code_length / text_length > 0.8 and word_count < 20:
                logger.debug("Noise detected: pure code without context")
                return True
        
        return False
    
    def _monitor_buffers(self):
        """
        Background thread that monitors buffers and closes them when ready.
        Runs every 60 seconds.
        """
        while self.running:
            time.sleep(60)  # Check every minute
            
            with self.lock:
                channels_to_close = []
                
                for channel_id, buffer in self.active_buffers.items():
                    # Check if buffer should be closed
                    time_since_last_message = datetime.now() - buffer.last_message_time
                    
                    # Close buffer if:
                    # 1. No messages for 30+ minutes
                    # 2. Has minimum number of messages
                    if time_since_last_message > timedelta(minutes=Config.BUFFER_TIME_WINDOW_MINUTES):
                        if len(buffer.messages) >= Config.BUFFER_MIN_MESSAGES:
                            channels_to_close.append(channel_id)
                            logger.info(f"Buffer {buffer.buffer_id} ready to close (silence timeout)")
                
                # Close buffers and trigger callback
                for channel_id in channels_to_close:
                    buffer = self.active_buffers.pop(channel_id)
                    self._process_closed_buffer(buffer)
    
    def _process_closed_buffer(self, buffer: ConversationBuffer):
        """
        Process a closed buffer - calculate signal score and trigger callback.
        
        Args:
            buffer: Closed ConversationBuffer
        """
        # Calculate signal score
        signal_score = buffer.calculate_signal_score()
        
        logger.info(
            f"Buffer {buffer.buffer_id} closed: "
            f"{len(buffer.messages)} messages, signal score: {signal_score:.2f}"
        )
        
        # Only process if signal score is high enough
        if signal_score >= Config.MIN_SIGNAL_SCORE:
            logger.info(f"Buffer {buffer.buffer_id} has high signal - triggering LLM processing")
            
            if self.on_buffer_ready:
                # Call the callback (will be the Ghostwriter LLM module)
                self.on_buffer_ready(buffer)
        else:
            logger.info(f"Buffer {buffer.buffer_id} signal too low - discarding")
    
    def force_close_buffer(self, channel_id: str):
        """
        Manually force close a buffer (e.g., via slash command).
        
        Args:
            channel_id: Channel ID to close buffer for
        """
        with self.lock:
            if channel_id in self.active_buffers:
                buffer = self.active_buffers.pop(channel_id)
                self._process_closed_buffer(buffer)
                logger.info(f"Manually closed buffer for channel {channel_id}")
            else:
                logger.warning(f"No active buffer for channel {channel_id}")
    
    def stop(self):
        """Stop the buffer engine and monitoring thread."""
        self.running = False
        if self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=2)
        logger.info("Buffer Engine stopped")
