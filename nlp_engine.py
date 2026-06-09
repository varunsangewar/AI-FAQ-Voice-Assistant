import sqlite3
import time
from google import genai
from dotenv import load_dotenv
import os

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY)

def get_answer(question, username="Guest"):
    history_text = ""
    
    # --- PHASE 1: Check Local Database ---
    try:
        conn = sqlite3.connect("database/faq.db")
        cursor = conn.cursor()
        
        # Check partial match queries
        cursor.execute("SELECT answer FROM faq WHERE question LIKE ?", ('%' + question + '%',))
        local_match = cursor.fetchone()
        
        if local_match:
            conn.close()
            return local_match[0]
            
        # --- PHASE 1.5: FETCH CONVERSATIONAL MEMORY ---
        cursor.execute("""
            SELECT question, answer 
            FROM chat_history 
            WHERE username = ? 
            ORDER BY id DESC LIMIT 4
        """, (username,))
        
        recent_chats = cursor.fetchall()[::-1] 
        conn.close()

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
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model='gemini-2.5-flash', # Or switch to 'gemini-2.0-flash' if needed
                contents=custom_prompt
            )
            
            if not response or not response.text:
                return "I'm sorry, my AI brain just drew a blank! Could you rephrase that?"
                
            return response.text
            
        except Exception as e:
            error_message = str(e)
            # Handle rate limiting or server overloads dynamically
            if "503" in error_message or "429" in error_message:
                if attempt < (max_retries - 1):
                    time.sleep(3) 
                    continue
            
            return f"⚠️ AI Error: {error_message}"