# 📚 SuperAssistant Vocabulary Tutor (MCP)

An AI-powered language learning assistant designed to manage your personal vocabulary database using the Model Context Protocol. This project helps users move words from "passive" recognition to "active" mastery through spaced repetition and contextual practice.

---

## 🚀 Getting Started

### Prerequisites
* A host environment supporting **Model Context Protocol (MCP)** (e.g., Gemini on the browser).
* The **SuperAssistant Extension** installed in your browser.

### Setup Instructions
1.  **Install the Extension:** Ensure the SuperAssistant extension is active in your browser.
2.  **Verify Connection:** Open the extension settings and ensure the **MCP**, **Auto Insert**, and **Auto Execute** toggles are enabled.
3.  **Database Initialization:** The first time you interact, the system will automatically prepare the `vocabulary` table to track your progress.
4.  **Troubleshooting:** If the sidebar shows "Loading instructions...", perform a hard refresh (`Ctrl + F5`) or toggle the extension off and on to reset the connection.

---

## 🛠 Available Tools

The assistant interacts with your database using the following functions:

| Function | Description |
| :--- | :--- |
| `get_learning_stats` | Summarizes word counts across all mastery levels (1–5). |
| `get_due_words` | Fetches words ready for review based on their last rating date. |
| `update_word_rating` | Adds a new word or updates the rating/notes for an existing one. |
| `get_words_by_rating`| Retrieves all words at a specific difficulty level. |
| `get_random_words` | Picks a random selection of words for varied practice. |
| `get_recent_words` | Retrieves the most recently added words to the database. |

---

## 📖 How to Use

### 1. Starting a Session
Begin by asking the assistant for your learning stats or due words. The assistant will generate a **JSONL** block like this:

```jsonl
{"type": "function_call_start", "name": "get_learning_stats", "call_id": 1}
{"type": "description", "text": "Checking current vocabulary progress."}
{"type": "function_call_end", "call_id": 1}

📊 Mastery Levels Defined
Rating 1: Brand new / Hard to remember.
Rating 2: In progress / Familiar but requires effort.'
Rating 3: Intermediate / Can use in simple sentences.
Rating 4: Advanced / Confident usage.
Rating 5: Mastered / Natural part of vocabulary.