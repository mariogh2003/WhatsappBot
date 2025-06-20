from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import requests
import os

app = Flask(__name__)

@app.route("/bot", methods=["POST"])
def whatsapp_bot():
    incoming_msg = request.values.get("Body", "")
    print(f"Incoming message: {incoming_msg}")
    
    try:
        summary = summarize(incoming_msg)
    except Exception as e:
        print(f"Error summarizing: {e}")
        summary = "Sorry, I couldn't summarize that right now."

    resp = MessagingResponse()
    msg = resp.message(summary)
    return str(resp)

def summarize(text):
    prompt = f"{text}"
    response = requests.post("http://localhost:11434/api/generate", json={
        "model": "gemma3:1b",
        "prompt": prompt,
        "stream": False
    })
    response.raise_for_status()  # Raises exception if status != 200
    result = response.json()
    return result.get("response", "Sorry, I couldn't summarize that.")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
