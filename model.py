import openai, os, threading
from database import fetch_messages, update_likelihood

openai.api_key = os.environ.get('OPENAI_KEY')

def gpt_chatbot(recipient_id, input):
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

        chat = openai.ChatCompletion.create(
            model="gpt-3.5-turbo", messages=messages_with_formatting
        )
        reply = chat.choices[0].message.content

        if reply.startswith("You: "):
            reply = reply[4:].strip()

        if reply.startswith("Juan: "):
            reply = reply[5:].strip()

        threading.Thread(target=run_analysis, args=(recipient_id,)).start()

    return reply

def run_analysis(recipient_id):
    messages = fetch_messages(recipient_id)
    likelihood = analyze_sentiment(recipient_id, messages)
    update_likelihood(recipient_id, likelihood)

def analyze_sentiment(recipient_id, messages):
    prompt = "Given the following conversation, estimate the likelihood of the user attending church, expressed as a percentage (0% to 100%):\n\n"

    for line in messages:
        if line['role'] == "user":
            prompt += f"User: {line['content']}\n"
        if line['role'] == "assistant":
            prompt += f"Assistant: {line['content']}\n"

    prompt += "\nLikelihood: "

    response = openai.Completion.create(
        engine="text-davinci-002",
        prompt=prompt,
        max_tokens=10,
        n=1,
        stop=None,
        temperature=0.5,
    )

    likelihood = response.choices[0].text.strip()
    return likelihood
