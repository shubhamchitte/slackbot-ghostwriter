"""
Unit tests for Storage module.
Tests SQLite database operations, CRUD functionality, and statistics.
"""

import pytest
import os
from datetime import datetime
from storage import Storage
from buffer_engine import ConversationBuffer


@pytest.mark.unit
class TestDatabaseInitialization:
    """Test database setup and table creation."""
    
    def test_database_tables_created(self, temp_db):
        """Test that all required tables are created."""
        import sqlite3
        
        conn = sqlite3.connect(temp_db.db_path)
        cursor = conn.cursor()
        
        # Check that tables exist
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name IN ('conversation_buffers', 'suggestions', 'used_topics')
        """)
        tables = [row[0] for row in cursor.fetchall()]
        
        assert 'conversation_buffers' in tables
        assert 'suggestions' in tables
        assert 'used_topics' in tables
        
        conn.close()
    
    def test_database_file_created(self):
        """Test that database file is created at specified path."""
        import tempfile
        
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        # Remove the file so Storage creates it
        os.remove(db_path)
        
        storage = Storage(db_path)
        
        assert os.path.exists(db_path)
        
        # Cleanup
        os.remove(db_path)


@pytest.mark.unit
class TestBufferOperations:
    """Test buffer CRUD operations."""
    
    def test_save_buffer(self, temp_db, sample_buffer):
        """Test saving a buffer to database."""
        temp_db.save_buffer(sample_buffer)
        
        # Verify it was saved
        import sqlite3
        conn = sqlite3.connect(temp_db.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT buffer_id FROM conversation_buffers WHERE buffer_id = ?", 
                      (sample_buffer.buffer_id,))
        result = cursor.fetchone()
        
        assert result is not None
        assert result[0] == sample_buffer.buffer_id
        
        conn.close()
    
    def test_save_buffer_with_metadata(self, temp_db, sample_buffer):
        """Test that buffer metadata is saved correctly."""
        sample_buffer.calculate_signal_score()
        temp_db.save_buffer(sample_buffer)
        
        import sqlite3
        conn = sqlite3.connect(temp_db.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM conversation_buffers WHERE buffer_id = ?", 
                      (sample_buffer.buffer_id,))
        row = cursor.fetchone()
        
        assert row['channel_id'] == sample_buffer.channel_id
        assert row['message_count'] == len(sample_buffer.messages)
        assert row['signal_score'] == sample_buffer.signal_score
        
        conn.close()


@pytest.mark.unit
class TestSuggestionOperations:
    """Test suggestion CRUD operations."""
    
    def test_save_suggestion(self, temp_db, sample_buffer, sample_suggestion):
        """Test saving a suggestion to database."""
        # First save the buffer
        temp_db.save_buffer(sample_buffer)
        
        # Then save suggestion
        temp_db.save_suggestion(sample_suggestion)
        
        # Verify it was saved
        import sqlite3
        conn = sqlite3.connect(temp_db.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT suggestion_id FROM suggestions WHERE buffer_id = ?", 
                      (sample_suggestion['buffer_id'],))
        result = cursor.fetchone()
        
        assert result is not None
        
        conn.close()
    
    def test_get_suggestion(self, temp_db, sample_buffer, sample_suggestion):
        """Test retrieving a suggestion from database."""
        temp_db.save_buffer(sample_buffer)
        temp_db.save_suggestion(sample_suggestion)
        
        retrieved = temp_db.get_suggestion(sample_suggestion['buffer_id'])
        
        assert retrieved is not None
        assert retrieved['x_draft'] == sample_suggestion['x_draft']
        assert retrieved['linkedin_draft'] == sample_suggestion['linkedin_draft']
        assert retrieved['topic'] == sample_suggestion['topic']
    
    def test_update_suggestion(self, temp_db, sample_buffer, sample_suggestion):
        """Test updating a suggestion."""
        temp_db.save_buffer(sample_buffer)
        temp_db.save_suggestion(sample_suggestion)
        
        # Update the suggestion
        new_x_draft = "Updated tweet content"
        temp_db.update_suggestion(
            sample_suggestion['buffer_id'],
            {'x_draft': new_x_draft}
        )
        
        # Verify update
        retrieved = temp_db.get_suggestion(sample_suggestion['buffer_id'])
        assert retrieved['x_draft'] == new_x_draft
    
    def test_record_user_action(self, temp_db, sample_buffer, sample_suggestion):
        """Test recording user actions (approve/dismiss/edit)."""
        temp_db.save_buffer(sample_buffer)
        temp_db.save_suggestion(sample_suggestion)
        
        # Record approval
        temp_db.record_user_action(sample_suggestion['buffer_id'], 'approved')
        
        # Verify action was recorded
        retrieved = temp_db.get_suggestion(sample_suggestion['buffer_id'])
        assert retrieved['user_action'] == 'approved'


@pytest.mark.unit
class TestStatistics:
    """Test statistics and analytics functions."""
    
    def test_get_stats_empty_database(self, temp_db):
        """Test getting stats from empty database."""
        stats = temp_db.get_stats()
        
        assert stats['total_buffers'] == 0
        assert stats['total_suggestions'] == 0
        assert stats['approval_rate'] == 0.0
        assert stats['avg_signal_score'] == 0.0
    
    def test_get_stats_with_data(self, temp_db, sample_buffer, sample_suggestion):
        """Test getting stats with data."""
        temp_db.save_buffer(sample_buffer)
        temp_db.save_suggestion(sample_suggestion)
        temp_db.record_user_action(sample_suggestion['buffer_id'], 'approved')
        
        stats = temp_db.get_stats()
        
        assert stats['total_buffers'] == 1
        assert stats['total_suggestions'] == 1
        assert stats['approval_rate'] == 1.0  # 100% approved
    
    def test_approval_rate_calculation(self, temp_db):
        """Test approval rate calculation with mixed actions."""
        # Create multiple suggestions with different actions
        for i in range(5):
            buffer = ConversationBuffer(f"buffer_{i}", "C001")
            buffer.add_message({
                "text": f"Test message {i}",
                "user": "U001",
                "channel_id": "C001",
                "ts": f"123.00{i}"
            })
            temp_db.save_buffer(buffer)
            
            suggestion = {
                "buffer_id": f"buffer_{i}",
                "x_draft": "Test tweet",
                "linkedin_draft": "Test post",
                "confidence": 0.8,
                "topic": "Test",
                "channel_id": "C001",
                "start_time": datetime.now().isoformat(),
                "end_time": datetime.now().isoformat()
            }
            temp_db.save_suggestion(suggestion)
        
        # Approve 3, dismiss 2
        temp_db.record_user_action("buffer_0", "approved")
        temp_db.record_user_action("buffer_1", "approved")
        temp_db.record_user_action("buffer_2", "approved")
        temp_db.record_user_action("buffer_3", "dismissed")
        temp_db.record_user_action("buffer_4", "dismissed")
        
        approval_rate = temp_db.get_approval_rate()
        
        assert approval_rate == 0.6  # 3/5 = 60%
    
    def test_get_recent_topics(self, temp_db, sample_buffer, sample_suggestion):
        """Test retrieving recently used topics."""
        temp_db.save_buffer(sample_buffer)
        temp_db.save_suggestion(sample_suggestion)
        
        recent_topics = temp_db.get_recent_topics(days=30)
        
        assert len(recent_topics) > 0
        assert sample_suggestion['topic'] in recent_topics
