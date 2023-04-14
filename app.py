import os, json, asyncio
from flask import Flask, request, jsonify
from database import *
from model import gpt_chatbot
import aiohttp

app = Flask(__name__)

VERIFY_TOKEN = os.environ.get('VERIFY_TOKEN')
PAGE_ACCESS_TOKEN = os.environ.get('PAGE_ACCESS_TOKEN')
PLUSPLUS_PAGE_ACCESS_TOKEN = os.environ.get('PLUSPLUS_PAGE_ACCESS_TOKEN')

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
                        print(messaging_event)
                        sender_id = messaging_event['sender']['id']
                        message_text = messaging_event['message']['text']
                        created_time = messaging_event['timestamp']
                        asyncio.run(send_message(sender_id, message_text, created_time, PAGE_ACCESS_TOKEN))
        return "ok"
    
@app.route('/juan_plus_plus/webhook', methods=['GET', 'POST'])
def juan_plus_plus_webhook():
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
                        print(messaging_event)
                        sender_id = messaging_event['sender']['id']
                        message_text = messaging_event['message']['text']
                        created_time = messaging_event['timestamp']
                        asyncio.run(send_message(sender_id, message_text, created_time, PLUSPLUS_PAGE_ACCESS_TOKEN))
        return "ok"

@app.route('/data_deletion', methods=['POST'])
def data_deletion():
    if request.method == 'POST':
        if request.args.get("hub.verify_token") == VERIFY_TOKEN:
            data = request.get_json()
            # Extract the recipient_id and call the delete_user_data function
            recipient_id = data['user_id']
            delete_user_data(recipient_id)

            # Respond with the confirmation code provided by Facebook
            return jsonify({"url": data['url'], "confirmation_code": data['confirmation_code']})
        else:
            return "Invalid verification token"

async def send_message(recipient_id, message_text, created_time, access_token):
    if message_exists(recipient_id, message_text, created_time):
        pass
    url = f"https://graph.facebook.com/v13.0/me/messages?access_token={access_token}"
    response = await gpt_chatbot(recipient_id, message_text)
    store_message(recipient_id, message_text, 'user', created_time)
    payload = {
        "recipient": {"id": recipient_id},
        "message": {"text": response},
    }
    headers = {"Content-Type": "application/json"}

    async with aiohttp.ClientSession() as session:
        async with session.post(url, data=json.dumps(payload), headers=headers) as resp:
            store_message(recipient_id, response, 'assistant', created_time)
            print(await resp.text())

if __name__ == "__main__":
    app.run(debug=True)
