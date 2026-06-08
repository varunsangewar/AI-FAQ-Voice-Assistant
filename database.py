import sqlite3
import os

# Ensure the database directory exists
os.makedirs('database', exist_ok=True)

conn = sqlite3.connect('database/faq.db')
cursor = conn.cursor()

# 1. THE NUCLEAR OPTION: Destroy the old chat table if it exists
cursor.execute('DROP TABLE IF EXISTS chat_history')

# 2. Build the NEW Chat History Table (with the timestamp feature!)
cursor.execute('''
CREATE TABLE chat_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
)
''')

# 3. Create the Knowledge Base Table (Keeps your existing FAQs safe)
cursor.execute('''
CREATE TABLE IF NOT EXISTS faq (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question TEXT NOT NULL,
    answer TEXT NOT NULL
)
''')

# 4. Create the Users Table (Keeps your logins safe)
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL
)
''')

# 5. Create the Feedback Table (for future use in AI training)
cursor.execute('''
CREATE TABLE IF NOT EXISTS feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id INTEGER,
    rating TEXT, -- Store 'up' or 'down'
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
)
''')
conn.commit()
conn.close()

print("✅ Database FORCE RESET successfully with timestamps!")