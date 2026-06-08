import sqlite3


def register_user(username,password):

    conn = sqlite3.connect("database/faq.db")

    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO users(username,password) VALUES(?,?)",
        (username,password)
    )

    conn.commit()

    conn.close()


def validate_user(username,password):

    conn = sqlite3.connect("database/faq.db")

    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM users WHERE username=? AND password=?",
        (username,password)
    )

    user = cursor.fetchone()

    conn.close()

    return user