import os
import sqlite3
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from datetime import datetime
from dotenv import load_dotenv
from groq import Groq

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
            feeling TEXT,
            exercise_done INTEGER
        )
    """)
    conn.commit()
    conn.close()

init_db()

def classify_and_reply(user_message, chat_history=[]):
    """Use Groq AI to generate therapist-like replies"""
    prompt = f"""
    You are Mindful Moments, a warm, kind therapist-like companion.
    Your role is to listen, validate emotions, and ask gentle follow-up questions.
    Speak in a supportive, conversational tone, like a caring friend or therapist.
    Be empathetic, never judgmental, and encourage self-reflection.

    Conversation so far:
    {chat_history}

    User: "{user_message}"
    
    Please respond as if you are continuing this therapy-style conversation.
    """

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "system", "content": "You are a supportive therapist-like companion."},
                  {"role": "user", "content": prompt}],
        temperature=0.8,
    )

    try:
        return response.choices[0].message.content.strip()
    except Exception:
        return "I’m here with you. Can you tell me more about what’s on your mind?"


@app.route("/")
def home():
    return send_from_directory("static", "index.html")

@app.route("/checkin", methods=["POST"])
def checkin():
    data = request.json
    user_id = data.get("user_id", "guest")
    message = data.get("message", "")

    result = classify_and_reply(message)
    intent = result["intent"]
    reply = result["reply"]

    # Default
    exercise_steps = []

    # If negative, prepare guided breathing sequence
    if intent == "negative":
        exercise_steps = [
            "Find a comfortable position and gently close your eyes.",
            "Bring your attention to your breath — just notice it.",
            "Slowly inhale through your nose... and exhale through your mouth.",
            "Expand awareness to your whole body — notice any tension.",
            "When you’re ready, gently open your eyes and return to the present."
        ]


    # Save in DB
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO checkins (user_id, date, feeling, exercise_done) VALUES (?, ?, ?, ?)",
        (user_id, datetime.utcnow().isoformat(), intent, 0)
    )
    checkin_id = cur.lastrowid
    conn.commit()
    conn.close()

    return jsonify({
        "reply": reply,
        "intent": intent,
        "checkin_id": checkin_id,
        "exercise": exercise_steps
    })

import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # Render assigns PORT automatically
    app.run(host="0.0.0.0", port=port)
 