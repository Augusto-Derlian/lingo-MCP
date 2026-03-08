import sqlite3
import datetime
from fastmcp import FastMCP
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
import uvicorn

# 1. Initialize MCP Server
mcp = FastMCP("LingoRate")

# 2. Database Initialization
DB_PATH = "lingo_vocab.db"

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
    print("Database initialized.")

init_db()

# 3. Helper Logic (Simplified SRS)
def calculate_next_review(rating):
    days = {1: 1, 2: 3, 3: 7, 4: 15, 5: 30}
    delta = days.get(rating, 1)
    return (datetime.datetime.now() + datetime.timedelta(days=delta)).isoformat()

# 4. MCP Tools for the Agent
@mcp.tool()
def get_due_words(limit: int = 5):
    """Fetch words that are due for review based on their rating."""
    now = datetime.datetime.now().isoformat()
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute(
            "SELECT expression, rating, notes FROM vocabulary WHERE next_review <= ? OR next_review IS NULL LIMIT ?", 
            (now, limit)
        )
        return cursor.fetchall()

@mcp.tool()
def update_word_rating(expression: str, new_rating: int, notes: str = ""):
    """Updates the user's mastery rating (1-5) for a specific word/phrase."""
    # Ensure rating is within 1-5
    rating = max(1, min(5, new_rating))
    next_review = calculate_next_review(rating)
    last_seen = datetime.datetime.now().isoformat()

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            INSERT INTO vocabulary (expression, rating, last_seen, next_review, notes)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(expression) DO UPDATE SET
                rating = excluded.rating,
                last_seen = excluded.last_seen,
                next_review = excluded.next_review,
                notes = COALESCE(NULLIF(excluded.notes, ''), vocabulary.notes)
        """, (expression.lower(), rating, last_seen, next_review, notes))
    
    return f"Success: '{expression}' updated to Rating {rating}. Next review: {next_review[:10]}"

@mcp.tool()
def get_learning_stats():
    """Returns a summary of how many words are at each rating level."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute("SELECT rating, COUNT(*) FROM vocabulary GROUP BY rating")
        stats = cursor.fetchall()
        return {f"Rating {r}": count for r, count in stats}

@mcp.tool()
def get_words_by_rating(rating: int):
    """Retrieves words from the 'vocabulary' table by rating."""
    # We keep it simple: No complex type hints in the header
    
    conn = sqlite3.connect("lingo_vocab.db")
    cursor = conn.cursor()
    cursor.execute(
        "SELECT expression, rating FROM vocabulary WHERE rating = ? LIMIT 5",
        (rating,)
    )
    words = cursor.fetchall()
    conn.close()
    
    if not words:
        return f"No words found with Rating {rating}."
    
    # Return a simple string
    output = [f"Words with Rating {rating}:"]
    for w in words:
        output.append(f"- {w[0]}")
    return "\n".join(output)

@mcp.tool()
def get_random_words(limit: int = 5):
    """Retrieves a random selection of words from the 'vocabulary' table."""
    with sqlite3.connect("lingo_vocab.db") as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT expression, rating FROM vocabulary ORDER BY RANDOM() LIMIT ?",
            (limit,)
        )
        words = cursor.fetchall()
    
    if not words:
        return "Your vocabulary list is currently empty."
    
    result = ["Random Vocabulary Warm-up:"]
    for w in words:
        result.append(f"- {w[0]} (Rating: {w[1]})")
    return "\n".join(result)

@mcp.tool()
def get_recent_words(limit: int = 5):
    """Retrieves the most recently added words from the 'vocabulary' table."""
    with sqlite3.connect("lingo_vocab.db") as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT expression, rating FROM vocabulary ORDER BY id DESC LIMIT ?",
            (limit,)
        )
        words = cursor.fetchall()
    
    if not words:
        return "No words found in your database."
    
    result = ["Recently Added Words:"]
    for w in words:
        result.append(f"- {w[0]} (Rating: {w[1]})")
    return "\n".join(result)

with sqlite3.connect("lingo_vocab.db") as conn:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS grammar_focus (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject TEXT NOT NULL,
            last_mistake TEXT,
            priority INTEGER DEFAULT 1,
            status TEXT DEFAULT 'Active'
        )
    """)

@mcp.tool()
def add_grammar_subject(subject: str, mistake_context: str = None):
    """Saves a grammar topic the user needs to work on."""
    import sqlite3
    with sqlite3.connect("lingo_vocab.db") as conn:
        cursor = conn.cursor()
        # Check if subject exists to update priority instead of duplicating
        cursor.execute("SELECT id, priority FROM grammar_focus WHERE subject = ?", (subject,))
        exists = cursor.fetchone()
        
        if exists:
            new_priority = exists[1] + 1
            cursor.execute("UPDATE grammar_focus SET priority = ?, last_mistake = ? WHERE id = ?", 
                           (new_priority, mistake_context, exists[0]))
            return f"Updated grammar focus: '{subject}' (Priority increased to {new_priority})"
        else:
            cursor.execute("INSERT INTO grammar_focus (subject, last_mistake) VALUES (?, ?)", 
                           (subject, mistake_context))
            return f"Added new grammar focus: '{subject}'"

@mcp.tool()
def get_grammar_targets(limit: int = 3):
    """Retrieves high-priority grammar subjects for review."""
    with sqlite3.connect("lingo_vocab.db") as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT subject, priority, last_mistake 
            FROM grammar_focus 
            WHERE status = 'Active' 
            ORDER BY priority DESC 
            LIMIT ?
        """, (limit,))
        rows = cursor.fetchall()
    
    if not rows:
        return "No active grammar targets found! You're doing great."
    
    res = ["🎯 Current Grammar Focus Areas:"]
    for r in rows:
        res.append(f"- {r[0]} (Priority Level: {r[1]})")
        if r[2]: 
            res.append(f"  * Context: \"{r[2]}\"")
    return "\n".join(res)

if __name__ == "__main__":
    # 1. Create the MCP app with CORS middleware included
    # This is the built-in way FastMCP handles web integrations
    mcp_app = mcp.http_app(
        transport="sse",
        middleware=[
            Middleware(
                CORSMiddleware,
                allow_origins=["*"],
                allow_methods=["*"],
                allow_headers=["*"],
            )
        ]
    )

    # 2. Start the server using the mcp_app we just created
    print("🚀 LingoRate Server starting on http://127.0.0.1:3006")
    uvicorn.run(mcp_app, host="127.0.0.1", port=3006)