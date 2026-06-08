import sqlite3
from google import genai
from dotenv import load_dotenv
import os

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

client = genai.Client(api_key=GEMINI_API_KEY)

def get_answer(question):
    # --- PHASE 1: Check Local Database ---
    conn = sqlite3.connect("database/faq.db")
    cursor = conn.cursor()
    
    # We use LIKE with % wildcards to find partial matches
    cursor.execute("SELECT answer FROM faq WHERE question LIKE ?", ('%' + question + '%',))
    local_match = cursor.fetchone()
    conn.close()
    
    # If we found an answer in our own database, return it immediately!
    if local_match:
        return local_match[0]
        
    # --- PHASE 2: The AI Fallback ---
    # If the code gets here, it means the database didn't have the answer.
    try:
        custom_prompt = f"""
        You are a helpful, professional FAQ assistant for a company. 
        Please answer the following user question concisely (in 2 to 3 sentences maximum).
        
        User Question: {question}
        """
        
        # New modern syntax for the Gemini API
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=custom_prompt
        )
        return response.text
        
    except Exception as e:
        print(f"AI Error: {e}")
        return "I'm sorry, I don't have the answer to that in my database, and my AI connection is currently offline."