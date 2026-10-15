import os
from flask import Flask, request
import requests

app = Flask(__name__)

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
MOMO = "0240807284"
VERIFY = "becewassce123"

SYSTEM = f"""
You are Ghana BECE/WASSCE teacher on WhatsApp.

RULES:
1. If user says hi/hello/start for first time, FIRST ask:
"Akwaaba! 😊 What is your name? Are you BECE or WASSCE student? Which subjects you need help?"
2. After they answer, remember their name and class and call them by name.
3. Then teach simple, give past questions, explain like good Ghanaian teacher.
4. Always end every answer with:
---
For unlimited access, MoMo {MOMO} - GH30/month
"""

# simple memory to know who is new (resets if server restarts, but ok for now)
users = {}

def ask_ai(user_id, question):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {{"Authorization": f"Bearer {{GROQ_API_KEY}}", "Content-Type": "application/json"}}

    # if new user, add small extra instruction
    is_new = user_id not in users
    if is_new:
        users[user_id] = True
        question = f"[This is first message from this student] {{question}}"

    data = {{
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {{"role":"system","content":SYSTEM}},
            {{"role":"user","content":question}}
        ],
        "max_tokens": 900
    }}
    try:
        r = requests.post(url, json=data, headers=headers, timeout=30)
        return r.json()['choices'][0]['message']['content']
    except Exception as e:
        print(e)
        return f"Network small issue, please ask again.\n---\nMoMo: {{MOMO}}"

@app.route("/")
def home():
    return "BECE/WASSCE Bot Live - MoMo 0240807284"

@app.route("/webhook", methods=["GET","POST"])
def webhook():
    if request.method == "GET":
        if request.args.get("hub.verify_token") == VERIFY:
            return request.args.get("hub.challenge")
        return "verify failed"

    data = request.get_json()
    try:
        entry = data['entry'][0]['changes'][0]['value']
        if 'messages' in entry:
            msg = entry['messages'][0]
            from_number = msg['from']
            text = msg.get('text', {{}}).get('body', 'hi')

            answer = ask_ai(from_number, text)

            # send back to WhatsApp
            TOKEN = os.environ.get("WHATSAPP_TOKEN")
            PHONE_ID = os.environ.get("PHONE_NUMBER_ID")
            if TOKEN and PHONE_ID:
                url = f"https://graph.facebook.com/v20.0/{{PHONE_ID}}/messages"
                h = {{"Authorization": f"Bearer {{TOKEN}}", "Content-Type": "application/json"}}
                payload = {{
                    "messaging_product":"whatsapp",
                    "to": from_number,
                    "text": {{"body": answer}}
                }}
                requests.post(url, json=payload, headers=h)
        return "OK", 200
    except Exception as e:
        print(e)
        return "OK", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
