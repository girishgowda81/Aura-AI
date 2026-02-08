from typing import List, Optional
import sqlite3
import json
from datetime import datetime

DB_PATH = "chat_history.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            session_id TEXT PRIMARY KEY,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            role TEXT,
            content TEXT,
            reasoning_details TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES sessions (session_id)
        )
    """)
    conn.commit()
    
    # Migration: Add column if doesn't exist
    try:
        cursor.execute("ALTER TABLE messages ADD COLUMN reasoning_details TEXT")
        conn.commit()
    except sqlite3.OperationalError:
        pass # Column already exists
    
    conn.close()

def save_message(session_id: str, role: str, content: str, reasoning_details: Optional[any] = None):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Force everything to be SQLite-compatible
    clean_content = str(content) if content is not None else ""
    
    rd_str = None
    if reasoning_details is not None:
        if isinstance(reasoning_details, str):
            rd_str = reasoning_details
        else:
            try:
                rd_str = json.dumps(reasoning_details)
            except:
                rd_str = str(reasoning_details)
        
    cursor.execute("INSERT OR IGNORE INTO sessions (session_id) VALUES (?)", (str(session_id),))
    cursor.execute("INSERT INTO messages (session_id, role, content, reasoning_details) VALUES (?, ?, ?, ?)", 
                   (str(session_id), str(role), clean_content, rd_str))
    conn.commit()
    conn.close()

def get_history(session_id: str, limit: int = 10):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT role, content, reasoning_details FROM messages 
        WHERE session_id = ? 
        ORDER BY timestamp DESC 
        LIMIT ?
    """, (session_id, limit))
    rows = cursor.fetchall()
    conn.close()
    
    history = []
    for r, c, rd in reversed(rows):
        # Try to parse reasoning_details if it looks like JSON
        rd_obj = rd
        if rd and isinstance(rd, str) and (rd.startswith('{') or rd.startswith('[')):
            try:
                rd_obj = json.loads(rd)
            except:
                pass
        history.append({"role": r, "content": c, "reasoning_details": rd_obj})
    return history

# Initialize on import
init_db()
