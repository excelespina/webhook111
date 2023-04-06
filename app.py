import os, json, requests
from flask import Flask, request
from database import init_db, store_message
from model import gpt_chatbot, analyze_sentiment
from concurrent.futures import ThreadPoolExecutor

app = Flask(__name__)
executor = ThreadPoolExecutor(max_workers=2)

VERIFY_TOKEN = os.environ.get('VERIFY_TOKEN')
PAGE_ACCESS_TOKEN = os.environ.get('PAGE_ACCESS_TOKEN')

init_db()

@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    if request.method == 'GET':
        if request.args.get("hub.verify_token") == VERIFY_TOKEN:
            return request.args.get("hub.challenge")
        else:
            return "Invalid verification token"
    elif request.method == 'POST':
        data = request.get_json()
        if data['object'] == 'page':
            for entry in data['entry']:
                for messaging_event in entry['messaging']:
                    if messaging_event.get('message'):
                        sender_id = messaging_event['sender']['id']
                        message_text = messaging_event['message']['text']
                        send_message(sender_id, message_text)
        return "ok"

def send_message(recipient_id, message_text):
    store_message(recipient_id, message_text, 'user')
    url = f"https://graph.facebook.com/v13.0/me/messages?access_token={PAGE_ACCESS_TOKEN}"
    response = gpt_chatbot(recipient_id, message_text)
    payload = {
        "recipient": {"id": recipient_id},
        "message": {"text": response},
    }
    headers = {"Content-Type": "application/json"}
    store_message(recipient_id, response, 'assistant')
    requests.post(url, data=json.dumps(payload), headers=headers)

if __name__ == "__main__":
    app.run(debug=True)
