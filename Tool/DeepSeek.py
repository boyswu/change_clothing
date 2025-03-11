# Please install OpenAI SDK first: `pip3 install openai`

from openai import OpenAI
api_key = 'sk-863e106b4cc1435187583c01fe4a8b06'
client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")

response = client.chat.completions.create(
    model="deepseek-chat",
    messages=[
        {"role": "system", "content": "You are a helpful assistant"},
        {"role": "user", "content": "Hello"},
    ],
    stream=False
)

print(response.choices[0].message.content)