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

import json

@app.route("/checkin", methods=["POST"])
def checkin():
    data = request.json
    user_message = data.get("message", "")

    # Call Groq or your AI
    response = client.chat.completions.create(
        model="llama3-8b-8192",
        messages=[
            {"role": "system", "content": "You are a friendly therapist-style chatbot."},
            {"role": "user", "content": user_message},
        ]
    )

    raw_result = response.choices[0].message["content"]

    try:
        # Try parsing as JSON
        result = json.loads(raw_result)
        intent = result.get("intent", "unknown")
        reply = result.get("reply", raw_result)
    except json.JSONDecodeError:
        # If not JSON, just treat it as plain text
        intent = "unknown"
        reply = raw_result

    return jsonify({"reply": reply, "intent": intent})


import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # Render assigns PORT automatically
    app.run(host="0.0.0.0", port=port)
 