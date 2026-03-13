import sqlite3

DB_PATH = "data/lingo_vocab.db"

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS vocabulary (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                expression TEXT UNIQUE,
                rating INTEGER DEFAULT 1,
                last_seen TIMESTAMP,
                next_review TIMESTAMP,
                notes TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS grammar_focus (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject TEXT NOT NULL,
                last_mistake TEXT,
                priority INTEGER DEFAULT 1,
                status TEXT DEFAULT 'Active'
            )
        """)
    print("Database initialized.")