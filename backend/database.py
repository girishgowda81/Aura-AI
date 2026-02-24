from typing import List, Optional
import sqlite3
import json
import os
from datetime import datetime

DB_PATH = "chat_history.db"
DATABASE_URL = os.getenv("DATABASE_URL")

def get_connection():
    if DATABASE_URL:
        # PostgreSQL (for Render)
        import psycopg2
        from psycopg2.extras import RealDictCursor
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    else:
        # SQLite (local)
        return sqlite3.connect(DB_PATH)

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    # Adapt SQL for PostgreSQL if needed
    is_postgres = bool(DATABASE_URL)
    
    session_sql = """
        CREATE TABLE IF NOT EXISTS sessions (
            session_id TEXT PRIMARY KEY,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """ if not is_postgres else """
        CREATE TABLE IF NOT EXISTS sessions (
            session_id TEXT PRIMARY KEY,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """
    
    messages_sql = """
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            role TEXT,
            content TEXT,
            reasoning_details TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES sessions (session_id)
        )
    """ if not is_postgres else """
        CREATE TABLE IF NOT EXISTS messages (
            id SERIAL PRIMARY KEY,
            session_id TEXT,
            role TEXT,
            content TEXT,
            reasoning_details TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES sessions (session_id)
        )
    """
    
    cursor.execute(session_sql)
    cursor.execute(messages_sql)
    conn.commit()
    
    # Migration for SQLite (reasoning_details)
    if not is_postgres:
        try:
            cursor.execute("ALTER TABLE messages ADD COLUMN reasoning_details TEXT")
            conn.commit()
        except sqlite3.OperationalError:
            pass
    
    conn.close()

def save_message(session_id: str, role: str, content: str, reasoning_details: Optional[any] = None):
    conn = get_connection()
    cursor = conn.cursor()
    
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
        
    cursor.execute("INSERT INTO sessions (session_id) VALUES (%s) ON CONFLICT (session_id) DO NOTHING" if DATABASE_URL else "INSERT OR IGNORE INTO sessions (session_id) VALUES (?)", (str(session_id),))
    
    msg_sql = "INSERT INTO messages (session_id, role, content, reasoning_details) VALUES (%s, %s, %s, %s)" if DATABASE_URL else "INSERT INTO messages (session_id, role, content, reasoning_details) VALUES (?, ?, ?, ?)"
    cursor.execute(msg_sql, (str(session_id), str(role), clean_content, rd_str))
    
    conn.commit()
    conn.close()

def get_history(session_id: str, limit: int = 10):
    conn = get_connection()
    cursor = conn.cursor()
    
    query = """
        SELECT role, content, reasoning_details FROM messages 
        WHERE session_id = %s 
        ORDER BY timestamp DESC 
        LIMIT %s
    """ if DATABASE_URL else """
        SELECT role, content, reasoning_details FROM messages 
        WHERE session_id = ? 
        ORDER BY timestamp DESC 
        LIMIT ?
    """
    
    cursor.execute(query, (str(session_id), limit))
    rows = cursor.fetchall()
    conn.close()
    
    history = []
    for r, c, rd in reversed(rows):
        rd_obj = rd
        if rd and isinstance(rd, str) and (rd.startswith('{') or rd.startswith('[')):
            try:
                rd_obj = json.loads(rd)
            except:
                pass
        history.append({"role": r, "content": c, "reasoning_details": rd_obj})
    return history

def get_all_sessions():
    conn = get_connection()
    cursor = conn.cursor()
    
    query = """
        SELECT session_id, created_at FROM sessions 
        ORDER BY created_at DESC
    """
    
    cursor.execute(query)
    rows = cursor.fetchall()
    conn.close()
    
    return [{"session_id": r[0], "created_at": r[1]} for r in rows]

# Initialize on import
init_db()
