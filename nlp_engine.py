import sqlite3
import time # <--- NEW: Allows the app to pause and wait
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
        username = session.get("user", "Guest")
        
        cursor.execute("""
            SELECT question, answer 
            FROM chat_history 
            WHERE username = ? 
            ORDER BY id DESC LIMIT 4
        """, (username,))
        
        recent_chats = cursor.fetchall()[::-1] 
        conn.close()

        history_text = ""
        for chat in recent_chats:
            history_text += f"User: {chat[0]}\nAI: {chat[1]}\n\n"
            
    except Exception as db_error:
        return f"⚠️ Database Error: {str(db_error)}"

    # --- PHASE 2: The AI Fallback (WITH AUTOMATIC RETRY) ---
    custom_prompt = f"""
    You are a helpful, friendly, and professional AI assistant. 
    You are allowed to casually greet the user, make small talk, and answer their questions concisely.
    
    Here is the recent conversation history with this user for context:
    {history_text}
    
    Current User Question: {question}
    """
    
    # Try up to 3 times before giving up
    max_retries = 3
    for attempt in range(max_retries):
        try:
            # Switched to the highly stable 1.5-flash model
            response = client.models.generate_content(
                model='gemini-1.5-flash',
                contents=custom_prompt
            )
            
            if not response.text:
                return "I'm sorry, my AI brain just drew a blank! Could you rephrase that?"
                
            return response.text
            
        except Exception as e:
            error_message = str(e)
            # If Google is busy (503) and we haven't run out of retries, wait 2 seconds and try again
            if "503" in error_message and attempt < (max_retries - 1):
                print(f"Server busy, retrying... (Attempt {attempt + 1})")
                time.sleep(2) 
                continue # Loops back to the top of the 'for' loop
            else:
                # If it's a different error, or we ran out of retries, finally show the error
                return f"⚠️ AI Error: {error_message}"