import os
import uuid
from datetime import datetime
import sqlite3
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, AIMessage

load_dotenv()

SQLITE_DB_PATH = os.getenv('SQLITE_DB_PATH', 'data/chat_history.db')


class SQLiteMemory:
    """
    SQLite-based conversation memory with windowed history.
    
    Features:
    - Unique session IDs (UUID-based)
    - Windowed memory (configurable limit)
    - Persistent storage across runs
    - Session management (clear, list, etc.)
    """
    
    def __init__(self, session_id: str = None, window_size: int = 10):
        """
        Initialize memory with optional session ID.
        
        Args:
            session_id: Unique session identifier. If None, generates a new one.
            window_size: Number of conversation turns to keep in memory (default: 10)
        """
        self.conn = sqlite3.connect(SQLITE_DB_PATH)
        self.cursor = self.conn.cursor()
        self.window_size = window_size
        
        # Generate unique session ID or use provided one
        if session_id:
            self.session_id = session_id
        else:
            # Create unique session ID with timestamp for readability
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            unique_id = str(uuid.uuid4())[:8]
            self.session_id = f"session_{timestamp}_{unique_id}"
        
        self._create_table()
        print(f"📝 Memory initialized - Session: {self.session_id}")
    
    def _create_table(self):
        """Create the messages table if it doesn't exist"""
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS chat_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                type TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_session_timestamp (session_id, timestamp)
            )
        """)
        self.conn.commit()

    def add_user_message(self, content: str):
        """Add a user message to the current session"""
        self.cursor.execute(
            "INSERT INTO chat_messages (session_id, type, content) VALUES (?, ?, ?)",
            (self.session_id, "human", content)
        )
        self.conn.commit()

    def add_ai_message(self, content: str):
        """Add an AI message to the current session"""
        self.cursor.execute(
            "INSERT INTO chat_messages (session_id, type, content) VALUES (?, ?, ?)",
            (self.session_id, "ai", content)
        )
        self.conn.commit()

    def load_history(self, limit: int = None):
        """
        Load recent conversation history with windowing.
        
        Args:
            limit: Maximum number of conversation turns to load.
                   If None, uses the window_size from init.
                   Note: Each turn = 1 user + 1 AI message, so we load limit*2 messages.
        
        Returns:
            List of LangChain messages (HumanMessage, AIMessage)
        """
        if limit is None:
            limit = self.window_size
        
        # Load last N*2 messages (each turn has user + AI message)
        self.cursor.execute(
            """SELECT type, content FROM chat_messages 
               WHERE session_id = ? 
               ORDER BY timestamp DESC 
               LIMIT ?""",
            (self.session_id, limit * 2)
        )
        
        # Reverse to get chronological order
        messages = []
        for type_, content in reversed(self.cursor.fetchall()):
            if type_ == "human":
                messages.append(HumanMessage(content=content))
            else:
                messages.append(AIMessage(content=content))
        
        return messages

    def get_message_count(self) -> int:
        """Get total number of messages in current session"""
        self.cursor.execute(
            "SELECT COUNT(*) FROM chat_messages WHERE session_id = ?",
            (self.session_id,)
        )
        return self.cursor.fetchone()[0]

    def clear(self):
        """Clear current session's messages"""
        self.cursor.execute(
            "DELETE FROM chat_messages WHERE session_id = ?", 
            (self.session_id,)
        )
        self.conn.commit()
        print(f"✅ Cleared session: {self.session_id}")
    
    def clear_all(self):
        """Clear ALL messages from database (useful for testing)"""
        self.cursor.execute("DELETE FROM chat_messages")
        self.conn.commit()
        print("✅ Cleared all sessions from database")
    
    def list_sessions(self) -> list:
        """List all available sessions with message counts"""
        self.cursor.execute("""
            SELECT session_id, COUNT(*) as msg_count, 
                   MIN(timestamp) as first_msg, 
                   MAX(timestamp) as last_msg
            FROM chat_messages 
            GROUP BY session_id 
            ORDER BY last_msg DESC
        """)
        return self.cursor.fetchall()
    
    def switch_session(self, session_id: str):
        """Switch to a different session"""
        self.session_id = session_id
        print(f"🔄 Switched to session: {session_id}")
    
    def close(self):
        """Close the database connection"""
        self.conn.close()


# Global memory instance
# For interactive mode: uses unique session per run
# For production: pass session_id from user context (e.g., user_id, conversation_id)
memory = SQLiteMemory(window_size=10)