from openai import OpenAI

api_key = 'yours'
client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")


# TODO: 问题和答案的对话存储在txt文件中，读取文件内容进行对话,前端发送用户的输入内容，和对应的哪一次对话，然后调用deepseek_chat函数进行对话

def deepseek_chat(content):
    # Round 1
    messages = [{"role": "user", "content": content}]
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=messages,
        stream=True
    )
    content = ""

    for chunk in response:
        if chunk.choices[0].delta.content:
            content += chunk.choices[0].delta.content
            print(chunk.choices[0].delta.content, end='\n')

    # Round 2
    messages.append({"role": "assistant", "content": content})
    messages.append({'role': 'user', 'content': "你的名字是什么？"})
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=messages,
        stream=True
    )
    for chunk in response:
        if chunk.choices[0].delta.content:
            print(chunk.choices[0].delta.content, end='\n')
