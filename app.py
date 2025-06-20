from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import requests
import threading
import time

app = Flask(__name__)

user_buffers = {}
summary_timeout = 30

OLLAMA_API_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "gemma3:1b"


def call_ollama(text):
    prompt = f"Summarize these WhatsApp messages briefly:\n\n{text}\n\nSummary:"
    resp = requests.post(OLLAMA_API_URL, json={
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False
    })
    resp.raise_for_status()
    data = resp.json()
    return data.get("response", "Sorry, no summary available.")

def send_summary(user_id):
    buffer = user_buffers.get(user_id)
    if not buffer or not buffer["messages"]:
        return  # Nothing to summarize

    messages_text = "\n".join(buffer["messages"])
    print(f"Summarizing messages for {user_id}: {len(buffer['messages'])} messages")

    try:
        summary = call_ollama(messages_text)
    except Exception as e:
        summary = f"Sorry, summarization failed: {e}"

    buffer["messages"] = []
    print(f"Summary for {user_id}:\n{summary}")
    buffer["last_summary"] = summary

def reset_timer(user_id):
    buffer = user_buffers.get(user_id)
    if buffer and buffer["timer"]:
        buffer["timer"].cancel()

    timer = threading.Timer(summary_timeout, lambda: send_summary(user_id))
    if buffer:
        buffer["timer"] = timer
        timer.start()

@app.route("/bot", methods=["POST"])
def whatsapp_bot():
    from_user = request.values.get("From")
    incoming_msg = request.values.get("Body", "").strip()

    if from_user not in user_buffers:
        user_buffers[from_user] = {"messages": [], "timer": None, "last_summary": None}

    buffer = user_buffers[from_user]

    # Command to manually trigger summary
    if incoming_msg.lower() == "summarize":
        if not buffer["messages"]:
            reply = "No messages to summarize."
        else:
            # Cancel timer because we're summarizing now
            if buffer["timer"]:
                buffer["timer"].cancel()

            messages_text = "\n".join(buffer["messages"])
            try:
                summary = call_ollama(messages_text)
                buffer["messages"] = []
                reply = summary
            except Exception as e:
                reply = f"Summarization error: {e}"
    else:
        # Add incoming message to buffer
        buffer["messages"].append(incoming_msg)
        reset_timer(from_user)

    resp = MessagingResponse()
    resp.message(reply)
    return str(resp)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
