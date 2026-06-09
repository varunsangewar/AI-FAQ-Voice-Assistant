import sqlite3
from google import genai
from dotenv import load_dotenv
import os
from flask import session

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

client = genai.Client(api_key=GEMINI_API_KEY)

def get_answer(question):
    # --- PHASE 1: Check Local Database ---
    try:
        conn = sqlite3.connect("database/faq.db")
        cursor = conn.cursor()
        
        # We use LIKE with % wildcards to find partial matches
        cursor.execute("SELECT answer FROM faq WHERE question LIKE ?", ('%' + question + '%',))
        local_match = cursor.fetchone()
        
        # If we found an answer in our own database, return it immediately!
        if local_match:
            conn.close()
            return local_match[0]
            
        # --- PHASE 1.5: FETCH CONVERSATIONAL MEMORY ---
        # Safely get the username (default to 'Guest' if not found)
        username = session.get("user", "Guest")
        
        # Grab the last 4 questions and answers for this specific user
        cursor.execute("""
            SELECT question, answer 
            FROM chat_history 
            WHERE username = ? 
            ORDER BY id DESC LIMIT 4
        """, (username,))
        
        # fetchall() gets them newest-to-oldest, so we reverse it to chronological order
        recent_chats = cursor.fetchall()[::-1] 
        conn.close()

        # Format the history into a readable string for the AI
        history_text = ""
        for chat in recent_chats:
            history_text += f"User: {chat[0]}\nAI: {chat[1]}\n\n"
            
    except Exception as db_error:
        # If the database crashes, print it to the chat screen!
        return f"⚠️ Database Error: {str(db_error)}"

    # --- PHASE 2: The AI Fallback ---
    try:
        custom_prompt = f"""
        You are a helpful, friendly, and professional AI assistant. 
        You are allowed to casually greet the user, make small talk, and answer their questions concisely.
        
        Here is the recent conversation history with this user for context:
        {history_text}
        
        Current User Question: {question}
        """
        
        # New modern syntax for the Gemini API
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=custom_prompt
        )
        
        # Catch empty AI responses
        if not response.text:
            return "I'm sorry, my AI brain just drew a blank! Could you rephrase that?"
            
        return response.text
        
    except Exception as e:
        # If the API crashes, print the EXACT error to the chat screen!
        return f"⚠️ AI Error: {str(e)}"