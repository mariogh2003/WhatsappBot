from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import requests
import os

openai.api_key = os.getenv("OPENAI_API_KEY")

app = Flask(__name__)

@app.route("/bot", methods=["POST"])
def whatsapp_bot():
    incoming_msg = request.values.get("Body", "")
    
    # Use OpenAI to summarize
    summary = summarize_with_gpt(incoming_msg)

    # Send response
    resp = MessagingResponse()
    msg = resp.message(summary)
    return str(resp)

def summarize_with_gpt(text):
    prompt = f"Summarize the following WhatsApp chat:\n\n{text}\n\nSummary:"
    response = requests.post("http://localhost:11434/api/generate", json={
        "model": "llama3",
        "prompt": prompt,
        "stream": False
    })
    result = response.json()
    return result.get("response", "Sorry, I couldn't summarize that.")

if __name__ == "__main__":
    app.run(port=5000)
