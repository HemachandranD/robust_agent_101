import os
from datetime import datetime
import sqlite3
import os
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, AIMessage

load_dotenv()

SQLITE_DB_PATH = os.getenv('SQLITE_DB_PATH', 'chat_history.db')  # Default to local file
SESSION_ID = f"robust_agent_101_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"  # Unique per session/user


class SQLiteMemory:
    def __init__(self):
        self.conn = sqlite3.connect(SQLITE_DB_PATH)
        self.cursor = self.conn.cursor()
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS chat_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                type TEXT,
                content TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.conn.commit()

    def add_user_message(self, content):
        self.cursor.execute(
            "INSERT INTO chat_messages (session_id, type, content) VALUES (?, ?, ?)",
            (SESSION_ID, "human", content)
        )
        self.conn.commit()

    def add_ai_message(self, content):
        self.cursor.execute(
            "INSERT INTO chat_messages (session_id, type, content) VALUES (?, ?, ?)",
            (SESSION_ID, "ai", content)
        )
        self.conn.commit()

    def load_history(self):
        self.cursor.execute(
            "SELECT type, content FROM chat_messages WHERE session_id = ? ORDER BY timestamp",
            (SESSION_ID,)
        )
        messages = []
        for type_, content in self.cursor.fetchall():
            if type_ == "human":
                messages.append(HumanMessage(content=content))
            else:
                messages.append(AIMessage(content=content))
        return messages

    def clear(self):
        self.cursor.execute("DELETE FROM chat_messages WHERE session_id = ?", (SESSION_ID,))
        self.conn.commit()

memory = SQLiteMemory()