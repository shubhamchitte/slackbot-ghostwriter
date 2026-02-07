"""
Module 5: Local Storage
SQLite database for tracking conversations, suggestions, and user feedback.
"""

import sqlite3
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional
import os
from config import Config
from buffer_engine import ConversationBuffer

logger = logging.getLogger(__name__)


class Storage:
    """SQLite storage for conversation buffers and suggestions."""
    
    def __init__(self, db_path: str = None):
        """
        Initialize storage.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path or Config.DB_PATH
        
        # Ensure data directory exists
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        # Initialize database
        self._init_database()
        
        logger.info(f"Storage initialized at {self.db_path}")
    
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
        
        logger.info("Database tables initialized")
    
    def save_buffer(self, buffer: ConversationBuffer):
        """
        Save conversation buffer to database.
        
        Args:
            buffer: ConversationBuffer to save
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO conversation_buffers 
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
            
            logger.info(f"Saved buffer {buffer.buffer_id} to database")
            
        except Exception as e:
            logger.error(f"Error saving buffer: {e}")
    
    def get_buffer_data(self, buffer_id: str) -> Optional[ConversationBuffer]:
        """
        Retrieve a conversation buffer from database.
        
        Args:
            buffer_id: Buffer ID to retrieve
        
        Returns:
            ConversationBuffer object or None
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM conversation_buffers
                WHERE buffer_id = ?
            """, (buffer_id,))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                # Reconstruct ConversationBuffer
                buffer = ConversationBuffer(row['buffer_id'], row['channel_id'])
                buffer.start_time = datetime.fromisoformat(row['start_time'])
                buffer.last_message_time = datetime.fromisoformat(row['end_time'])
                buffer.signal_score = row['signal_score']
                buffer.topic_keywords = json.loads(row['topic_keywords'])
                buffer.messages = json.loads(row['raw_messages'])
                return buffer
                
            return None
            
        except Exception as e:
            logger.error(f"Error getting buffer data: {e}")
            return None
    
    def save_suggestion(self, suggestion: Dict):
        """
        Save LLM-generated suggestion to database.
        
        Args:
            suggestion: Dict with x_draft, linkedin_draft, etc.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            suggestion_id = suggestion['buffer_id']  # Use buffer_id as suggestion_id
            
            cursor.execute("""
                INSERT OR REPLACE INTO suggestions 
                (suggestion_id, buffer_id, x_draft, linkedin_draft, 
                 confidence, topic, message_ts)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                suggestion_id,
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
            
            logger.info(f"Saved suggestion {suggestion_id} to database")
            
        except Exception as e:
            logger.error(f"Error saving suggestion: {e}")
    
    def get_suggestion(self, buffer_id: str) -> Optional[Dict]:
        """
        Get suggestion by buffer_id.
        
        Args:
            buffer_id: Buffer ID to look up
        
        Returns:
            Dict with suggestion data or None
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM suggestions
                WHERE suggestion_id = ?
            """, (buffer_id,))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return dict(row)
            return None
            
        except Exception as e:
            logger.error(f"Error getting suggestion: {e}")
            return None
    
    def update_suggestion(self, buffer_id: str, updates: Dict):
        """
        Update suggestion fields.
        
        Args:
            buffer_id: Buffer ID to update
            updates: Dict with fields to update (e.g., {'x_draft': 'new text'})
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Build UPDATE query dynamically
            set_clauses = []
            values = []
            
            for key, value in updates.items():
                set_clauses.append(f"{key} = ?")
                values.append(value)
            
            # Add updated_at
            set_clauses.append("updated_at = ?")
            values.append(datetime.now().isoformat())
            
            # Add buffer_id for WHERE clause
            values.append(buffer_id)
            
            query = f"""
                UPDATE suggestions
                SET {', '.join(set_clauses)}
                WHERE suggestion_id = ?
            """
            
            cursor.execute(query, values)
            conn.commit()
            conn.close()
            
            logger.info(f"Updated suggestion {buffer_id}")
            
        except Exception as e:
            logger.error(f"Error updating suggestion: {e}")
    
    def record_user_action(self, buffer_id: str, action: str):
        """
        Record user action (approve/dismiss/edit).
        
        Args:
            buffer_id: Buffer ID
            action: Action taken ("approved", "dismissed", "edited")
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE suggestions
                SET user_action = ?, updated_at = ?
                WHERE suggestion_id = ?
            """, (action, datetime.now().isoformat(), buffer_id))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Recorded action '{action}' for suggestion {buffer_id}")
            
        except Exception as e:
            logger.error(f"Error recording user action: {e}")
    
    def get_recent_topics(self, days: int = 30) -> List[str]:
        """
        Get topics used in last N days (to avoid repetition).
        
        Args:
            days: Number of days to look back
        
        Returns:
            List of topic strings
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT topic FROM used_topics
                WHERE last_used >= datetime('now', '-' || ? || ' days')
            """, (days,))
            
            topics = [row[0] for row in cursor.fetchall()]
            conn.close()
            
            return topics
            
        except Exception as e:
            logger.error(f"Error getting recent topics: {e}")
            return []
    
    def get_approval_rate(self) -> float:
        """
        Calculate approval rate for analytics.
        
        Returns:
            Float between 0.0 and 1.0
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    COUNT(CASE WHEN user_action = 'approved' THEN 1 END) * 1.0 / 
                    NULLIF(COUNT(*), 0) as rate
                FROM suggestions
                WHERE user_action IS NOT NULL
            """)
            
            result = cursor.fetchone()
            conn.close()
            
            return result[0] if result[0] is not None else 0.0
            
        except Exception as e:
            logger.error(f"Error calculating approval rate: {e}")
            return 0.0
    
    def get_stats(self) -> Dict:
        """
        Get overall statistics.
        
        Returns:
            Dict with stats
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Total buffers
            cursor.execute("SELECT COUNT(*) FROM conversation_buffers")
            total_buffers = cursor.fetchone()[0]
            
            # Total suggestions
            cursor.execute("SELECT COUNT(*) FROM suggestions")
            total_suggestions = cursor.fetchone()[0]
            
            # Approval rate
            approval_rate = self.get_approval_rate()
            
            # Average signal score
            cursor.execute("SELECT AVG(signal_score) FROM conversation_buffers")
            avg_signal = cursor.fetchone()[0] or 0.0
            
            conn.close()
            
            return {
                "total_buffers": total_buffers,
                "total_suggestions": total_suggestions,
                "approval_rate": approval_rate,
                "avg_signal_score": avg_signal
            }
            
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {}
