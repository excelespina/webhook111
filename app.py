import os
import json
import requests
from flask import Flask, request
import openai, random, time

#### SETUP
app = Flask(__name__)

VERIFY_TOKEN = os.environ.get('VERIFY_TOKEN')
PAGE_ACCESS_TOKEN = os.environ.get('PAGE_ACCESS_TOKEN')
openai.api_key = os.environ.get('OPENAI_KEY')

user_messages = {}

##### END SETUP

def gpt_chatbot(recipient_id, input):
    global user_messages

    if input:
        messages_with_formatting = []

        for line in user_messages[recipient_id]:
            if line['role'] == "user":
                messages_with_formatting.append({"role": "user", "content": "Them: " + line['content']})
            if line['role'] == "assistant":
                messages_with_formatting.append({"role": "assistant", "content": "You: " + line['content']})
            if line['role'] == "system":
                messages_with_formatting.append({"role": "system", "content": line['content']})

        messages_with_formatting.append({"role": "user", "content": "Them: " + input})

        chat = openai.ChatCompletion.create(
            model="gpt-3.5-turbo", messages=messages_with_formatting
        )
        reply = chat.choices[0].message.content

        if reply.startswith("You: "):
            reply = reply[4:].strip()

        return reply

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
    global user_messages

    # If the user is not in user_messages, initialize their message history
    if recipient_id not in user_messages:
        user_messages[recipient_id] = [
            {"role": "system", "content": os.environ.get('ENGINE_PROMPT')},
        ]

    # Add the user's message to their message history
    user_messages[recipient_id].append({"role": "user", "content": message_text})

    # Call the gpt_chatbot function with the received message_text
    gpt_response = gpt_chatbot(recipient_id, message_text)

    # Add the GPT-3 response to the user's message history
    user_messages[recipient_id].append({"role": "assistant", "content": gpt_response})

    url = f"https://graph.facebook.com/v13.0/me/messages?access_token={PAGE_ACCESS_TOKEN}"
    payload = {
        "recipient": {"id": recipient_id},
        "message": {"text": gpt_response},
    }
    headers = {"Content-Type": "application/json"}
    response = requests.post(url, data=json.dumps(payload), headers=headers)

if __name__ == "__main__":
    app.run(debug=True)
