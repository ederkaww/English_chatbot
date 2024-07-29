from flask import Flask, request, jsonify
import requests

app = Flask(__name__)


@app.route('/webhook', methods=['POST'])
def webhook():
    user_message = request.json.get("message")
    rasa_response = send_message_to_rasa(user_message)
    return jsonify({"response": rasa_response})


def send_message_to_rasa(message):
    rasa_url = "http://localhost:5005/webhooks/rest/webhook"
    payload = {
        "sender": "user",
        "message": message
    }
    response = requests.post(rasa_url, json=payload)
    if response.status_code == 200:
        responses = response.json()
        if responses:
            return responses[0].get("text")
    return "Sorry, I didn't get that. Can you rephrase?"


if __name__ == '__main__':
    app.run(port=5000)
