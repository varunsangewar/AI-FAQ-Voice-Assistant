from flask import Flask, render_template, request, redirect, session, jsonify 
import sqlite3
import threading 
from auth import register_user, validate_user
from nlp_engine import get_answer

app = Flask(__name__)
app.secret_key = "AI_FAQ_SECRET"

@app.route("/")
def home():
    if "user" not in session:
        return redirect("/login")
    return render_template("index.html")

# ----------------------------
# Register
# ----------------------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        
        try:
            register_user(username, password)
            return redirect("/login")
        except:
            return "User already exists"
            
    return render_template("register.html")

# ----------------------------
# Login
# ----------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        
        user = validate_user(username, password)
        if user:
            session["user"] = username
            return redirect("/")
        return "Invalid Credentials"
        
    return render_template("login.html")

# ----------------------------
# Logout
# ----------------------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

# ----------------------------
# Ask Question (UPDATED FOR REAL DATABASE ID)
# ----------------------------
@app.route("/ask", methods=["POST"])
def ask():
    user_question = request.form["question"]
    answer = get_answer(user_question)
    
    conn = sqlite3.connect("database/faq.db")
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO chat_history
        (username,question,answer)
        VALUES(?,?,?)
        """,
        (
            session["user"],
            user_question,
            answer
        )
    )
    # Get the exact ID of the row we just inserted
    real_chat_id = cursor.lastrowid 
    
    conn.commit()
    conn.close()
    
    # Send the answer AND the real database ID back to the user
    return jsonify({"answer": answer, "chat_id": real_chat_id})

# ----------------------------
# Dashboard (UPGRADED FOR REAL DATA)
# ----------------------------
@app.route("/dashboard")
def dashboard():
    conn = sqlite3.connect("database/faq.db")
    cursor = conn.cursor()
    
    # 1. AUTO-UPGRADE DATABASE: Add timestamp if it doesn't exist
    try:
        cursor.execute("ALTER TABLE chat_history ADD COLUMN timestamp DATETIME DEFAULT CURRENT_TIMESTAMP")
        conn.commit()
    except:
        pass # Safely ignore if the column already exists
        
    # 2. GET TOP COUNTERS
    cursor.execute("SELECT * FROM chat_history ORDER BY id DESC")
    chats = cursor.fetchall()
    total_questions = len(chats)
    
    try:
        cursor.execute("SELECT COUNT(*) FROM faq")
        total_faqs = cursor.fetchone()[0]
    except:
        total_faqs = 0
        
    try:
        cursor.execute("SELECT COUNT(DISTINCT username) FROM chat_history")
        total_users = cursor.fetchone()[0]
    except:
        total_users = 0

    # 3. REAL CHART DATA: DAILY ACTIVITY
    cursor.execute("""
        SELECT date(timestamp), COUNT(*) 
        FROM chat_history 
        WHERE timestamp IS NOT NULL 
        GROUP BY date(timestamp) 
        ORDER BY date(timestamp) DESC 
        LIMIT 7
    """)
    daily_stats = cursor.fetchall()
    
    bar_labels = []
    bar_data = []
    for stat in reversed(daily_stats): # Reverse so graph goes left (old) to right (new)
        bar_labels.append(stat[0])
        bar_data.append(stat[1])
        
    # Fallback if no questions exist today yet
    if not bar_labels:
        from datetime import date
        bar_labels = [str(date.today())]
        bar_data = [0]

    # 4. REAL CHART DATA: TOP USERS
    cursor.execute("""
        SELECT username, COUNT(*) 
        FROM chat_history 
        GROUP BY username 
        ORDER BY COUNT(*) DESC 
        LIMIT 5
    """)
    user_stats = cursor.fetchall()
    
    pie_labels = [row[0] for row in user_stats]
    pie_data = [row[1] for row in user_stats]

    if not pie_labels:
        pie_labels = ["No Users Yet"]
        pie_data = [1]

    # 5. REAL CHART DATA: FEEDBACK COUNTS (NEW)
    try:
        cursor.execute("SELECT rating, COUNT(*) FROM feedback GROUP BY rating")
        data = cursor.fetchall()
        feedback_counts = {'up': 0, 'down': 0}
        for row in data:
            feedback_counts[row[0]] = row[1]
    except:
        feedback_counts = {'up': 0, 'down': 0}

    conn.close()
    
    return render_template(
        "dashboard.html",
        chats=chats,
        total_users=total_users,
        total_faqs=total_faqs,
        total_questions=total_questions,
        bar_labels=bar_labels, 
        bar_data=bar_data,
        pie_labels=pie_labels,
        pie_data=pie_data,
        feedback_counts=feedback_counts  # <--- Passed to frontend here
    )

# ----------------------------
# Admin
# ----------------------------
@app.route("/admin")
def admin():
    conn = sqlite3.connect("database/faq.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM faq")
    faqs = cursor.fetchall()
    conn.close()
    
    return render_template(
        "admin.html",
        faqs=faqs
    )

@app.route("/add_faq", methods=["POST"])
def add_faq():
    question = request.form["question"]
    answer = request.form["answer"]
    
    conn = sqlite3.connect("database/faq.db")
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO faq
        (question,answer)
        VALUES(?,?)
        """,
        (question, answer)
    )
    conn.commit()
    conn.close()
    
    return redirect("/admin")

@app.route("/update_faq", methods=["POST"])
def update_faq():
    faq_id = request.form.get("faq_id")
    question = request.form.get("question")
    answer = request.form.get("answer")
    
    if faq_id:
        conn = sqlite3.connect("database/faq.db")
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE faq 
            SET question = ?, answer = ? 
            WHERE id = ?
            """,
            (question, answer, faq_id)
        )
        conn.commit()
        conn.close()
        
    return redirect("/admin")

@app.route("/delete_faq/<int:faq_id>", methods=["POST"])
def delete_faq(faq_id):
    conn = sqlite3.connect("database/faq.db")
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM faq WHERE id = ?", (faq_id,))
    
    conn.commit()
    conn.close()
    
    return redirect("/admin")

# ----------------------------
# Feedback
# ----------------------------
@app.route('/feedback', methods=['POST'])
def save_feedback():
    data = request.json
    chat_id = data.get('chat_id')
    rating = data.get('rating') # Expecting 'up' or 'down'
    
    conn = sqlite3.connect('database/faq.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO feedback (chat_id, rating) VALUES (?, ?)", (chat_id, rating))
    conn.commit()
    conn.close()
    return jsonify({"status": "success"})

@app.route('/feedback-logs')
def view_feedback():
    conn = sqlite3.connect('database/faq.db')
    cursor = conn.cursor()
    # Join with chat_history to see the actual questions people rated!
    cursor.execute('''
        SELECT f.rating, c.question, c.answer, f.timestamp 
        FROM feedback f
        JOIN chat_history c ON f.chat_id = c.id
    ''')
    feedbacks = cursor.fetchall()
    conn.close()
    return render_template('feedback_logs.html', feedbacks=feedbacks)


if __name__ == "__main__":
    app.run(debug=True, port=5005)