import openai, os, threading, asyncio, random, re
from database import fetch_messages, update_likelihood

openai.api_key = os.environ.get('OPENAI_KEY')

async def gpt_chatbot(recipient_id, input):
    if input:
        messages_with_formatting = []

        message_history = fetch_messages(recipient_id)
        for line in message_history:
            if line['role'] == "user":
                messages_with_formatting.append({"role": "user", "content": "Them: " + line['content']})
            if line['role'] == "assistant":
                messages_with_formatting.append({"role": "assistant", "content": "You: " + line['content']})
            if line['role'] == "system":
                messages_with_formatting.append({"role": "system", "content": line['content']})

        messages_with_formatting.append({"role": "user", "content": "Them: " + input})

        # Add delay here (in seconds)
        await asyncio.sleep(random.uniform(1, 5))

        chat = openai.ChatCompletion.create(
            model="gpt-3.5-turbo", messages=messages_with_formatting
        )
        reply = chat.choices[0].message.content
        print(reply)

        if reply.startswith("You: "):
            reply = reply[4:].strip()

        if reply.startswith("Juan: "):
            reply = reply[5:].strip()

        # Extract percentage values from the reply
        likelihoods = re.findall(r'\{\{.*?(\d+)%\}\}', reply)

        # Remove the brackets and likelihood information from the reply
        reply = re.sub(r'\{\{.*?\}\}', '', reply).strip()

        # Store the extracted percentage values in the database
        print(likelihoods)
        if likelihoods:
            likelihood_data = {
                "sunday_service": likelihoods[0] or 0,
                "bible_study": likelihoods[1] or 0,
                "bible_talk": likelihoods[2] or 0,
            }
            update_likelihood(recipient_id, likelihood_data)

    return reply
