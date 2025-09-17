import requests

#
# url = "https://api.siliconflow.cn/v1/images/generations"
# key = "sk-kmigoyyjgnarzacrdrsrmpgikcjafpoewrttuhjlagdurdyw"
# payload = {
#     "model": "Kwai-Kolors/Kolors",
#     "prompt": "an island near sea, with seagulls, moon shining over the sea, light house, boats int he background, "
#               "fish flying over the sea",
#     "negative_prompt": "a beautiful sunset, with a girl in a pink dress, and a giant pink flower, ",
#     "image_size": "1024x1024",
#     "batch_size": 1,
#     "seed": 4999999999,
#     "num_inference_steps": 20,
#     "guidance_scale": 7.5,
#     "image": "data:D:\\pycharm_project\\change_clothes\\image\\dress.jpg;base64, XXX"
# }
# headers = {
#     "Authorization": key,
#     "Content-Type": "application/json"
# }

# response = requests.request("POST", url, json=payload, headers=headers)

# print(response.text)
import requests

api_url = "https://api.siliconflow.cn/v1/images/generations"
key = "yours-key"
headers = {
    "Authorization": key,
    "Content-Type": "application/json"
}

data = {
    "prompt": "生成一幅水墨画中的老虎奔跑图像",
    "model": "Kolors"
}

response = requests.post(api_url, headers=headers, json=data)
print(response.json())
