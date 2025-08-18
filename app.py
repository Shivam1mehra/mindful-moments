import os
import sqlite3
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from datetime import datetime
from dotenv import load_dotenv
from groq import Groq
import json

# Load API key
load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

app = Flask(__name__, static_url_path='', static_folder='static')
CORS(app)

DB_FILE = "mindful.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS checkins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            date TEXT,
            stage INTEGER,
            message TEXT,
            feeling TEXT,
            exercise_done INTEGER
        )
    """)
    conn.commit()
    conn.close()

init_db()

def classify_and_reply(user_message):
    """Use Groq AI to generate warm, empathetic replies"""
    prompt = f"""
    You are Mindful Moments, a gentle and sweet mental health companion.
    The user just said: "{user_message}"

    Your job:
    1. Respond warmly in 1–3 sentences.
    2. Use a kind, encouraging, and empathetic tone.
    3. Keep the reply short and caring, like talking to a close friend.
    4. If they share something negative, validate their feelings and remind them of their strength.

    Example tones:
    - "That sounds really tough 💙. Remember, you're not alone in this."
    - "I’m so happy you shared that 🌸. Little joys can mean a lot."
    - "You’re doing better than you think 🌱. Take a deep breath with me."

    Respond only with the reply text.
    """

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": "You are a warm, caring AI companion."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.8,
    )

    try:
        content = response.choices[0].message.content.strip()
        return {"reply": content}
    except Exception:
        return {"reply": "I'm here with you 💙. Would you like to tell me more?"}


@app.route("/")
def home():
    return send_from_directory("static", "index.html")


@app.route("/checkin", methods=["POST"])
def checkin():
    data = request.json
    user_id = data.get("user_id", "guest")
    message = data.get("message", "")

    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()

    # Find last stage
    cur.execute("SELECT stage FROM checkins WHERE user_id=? ORDER BY id DESC LIMIT 1", (user_id,))
    row = cur.fetchone()
    stage = row[0] if row else 0

    reply = ""
    next_stage = 0

    if stage == 0:
        reply = "Hi sweet soul 🌸 How are you feeling today?"
        next_stage = 1
    elif stage == 1:
        reply = "Thank you for sharing that 💙 On a scale of 1–10, how’s your energy right now?"
        next_stage = 2
    elif stage == 2:
        reply = "Got it 🌱 What’s one positive or gentle thing that happened today?"
        next_stage = 3
    elif stage == 3:
        ai = classify_and_reply(message)
        reply = f"{ai['reply']} 🌼 Remember to be kind to yourself."
        next_stage = 0  # reset

    # Save check-in
    cur.execute(
        "INSERT INTO checkins (user_id, date, stage, message, feeling, exercise_done) VALUES (?, ?, ?, ?, ?, ?)",
        (user_id, datetime.utcnow().isoformat(), next_stage, message, "", 0)
    )
    conn.commit()
    conn.close()

    return jsonify({"reply": reply, "stage": next_stage})