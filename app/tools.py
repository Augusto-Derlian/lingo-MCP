import sqlite3
import datetime
from typing import Union
from . import mcp
from .database import DB_PATH

# 3. Helper Logic (Simplified Spaced Repetition System)
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
def update_word_rating(expression: str | list[str], new_rating: int | list[int]):
    """Updates or Inserts words and refreshes last_seen/next_review."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        
        # Standardize to lists
        expressions = [expression] if isinstance(expression, str) else expression
        if isinstance(new_rating, int):
            ratings = [new_rating] * len(expressions)
        else:
            ratings = new_rating

        now = datetime.datetime.now()
        data = []
        for word, rate in zip(expressions, ratings):
            # Normalizing to lowercase here prevents case-based duplicates
            clean_word = word.strip().lower() 
            next_date = now + datetime.timedelta(days=rate * 2)
            data.append((clean_word, rate, now, next_date))

        cursor.executemany("""
            INSERT INTO vocabulary (expression, rating, last_seen, next_review) 
            VALUES (?, ?, ?, ?)
            ON CONFLICT(expression) DO UPDATE SET 
                rating = excluded.rating,
                last_seen = excluded.last_seen,
                next_review = excluded.next_review
        """, data)
        
    return f"Processed {len(expressions)} word(s)."

@mcp.tool()
def get_learning_stats():
    """Returns a summary of how many words are at each rating level and grammar count."""
    with sqlite3.connect(DB_PATH) as conn:
        # Get Vocabulary stats
        cursor = conn.execute("SELECT rating, COUNT(*) FROM vocabulary GROUP BY rating")
        stats = {f"Rating {r}": count for r, count in cursor.fetchall()}
        
        # Get Grammar stats
        cursor = conn.execute("SELECT COUNT(*) FROM grammar_focus WHERE status = 'Active'")
        grammar_count = cursor.fetchone()[0]
        
        # Merge them into one status object
        stats["Active Grammar Targets"] = grammar_count
        return stats

@mcp.tool()
def get_words_by_rating(rating: int):
    """Retrieves words from the 'vocabulary' table by rating."""
    # We keep it simple: No complex type hints in the header
    
    conn = sqlite3.connect(DB_PATH)
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
    with sqlite3.connect(DB_PATH) as conn:
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
    with sqlite3.connect(DB_PATH) as conn:
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

@mcp.tool()
def delete_expression(expression: Union[str, list[str]]):
    """Permanently removes one or more expressions from the vocabulary database."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        # Normalize input to a list
        targets = [expression] if isinstance(expression, str) else expression
        
        cursor.executemany("DELETE FROM vocabulary WHERE expression = ?", [(t,) for t in targets])
        changes = conn.total_changes
        
    return f"Successfully removed {changes} entries."

@mcp.tool()
def add_grammar_subject(subject: str, mistake_context: str = None):
    """Saves a grammar topic the user needs to work on."""
    with sqlite3.connect(DB_PATH) as conn:
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
    with sqlite3.connect(DB_PATH) as conn:
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