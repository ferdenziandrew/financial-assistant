from openai import OpenAI

client = OpenAI()

def ask_ai(question):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a personal finance assistant."},
            {"role": "user", "content": question}
        ]
    )

    return response.choices[0].message.content