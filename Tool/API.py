import urllib, urllib3, sys, uuid
import ssl
import json

host = 'https://damotryon.market.alicloudapi.com'
path = '/api/v1/tryon/submit'
method = 'POST'
appcode = 'c29f5e38c5b24c38bd8f7332db2b0590'
querys = ''
bodys = {}
url = host + path

http = urllib3.PoolManager()
headers = {
    'X-Ca-Nonce': str(uuid.uuid4()),  # 需要给X-Ca-Nonce的值生成随机字符串，每次请求不能相同
    'Content-Type': 'application/json; charset=UTF-8',
    'Authorization': 'APPCODE ' + appcode
}

data = {
    "data": {
        "fit_type": "FULL_BODY",  # 换装类型枚举，FULL_BODY：全身换装，HALF_BODY:半身换装
        "inference_num": 1,  # 单任务算法结果数量（1~4）
        "task_list": [  # 任务列表,最多10项
            {
                "model_image": "http://43.143.229.40:9000/2303080206/clothes/person.jpg",  # 模特图,必填
                "tops_image": "http://43.143.229.40:9000/2303080206/clothes/long_clothing.jpg",  # 上装图,必填
                "pants_image": ""  # 下装图,选填
                # "mask_image": "https://img.alicdn.com/abc.png"      # 选填mask图⽚,确保上传的mask图与原图尺⼨⼀致，mask为0/255图格式
            }
        ]
    }
}

bodys[''] = json.dumps(data)
post_data = bodys['']
response = http.request('POST', url, body=post_data, headers=headers)
content = response.data.decode('utf-8')
if content:
    print(content)
    result = json.loads(content)
    if result['code'] == 0:
        print(result['data']['result_key'])  # 换装结果图url
        result_key = result['data']['result_key']
        # 使用字典来构建请求体
        data_dict = {
            "data": {
                "result_key": result_key  # 任务key，见任务提交接口返回字段result_key
            }
        }
        # 将字典转换为JSON字符串
        bodys[''] = json.dumps(data_dict)
        post_data = bodys['']
        response = http.request('POST', url, body=post_data, headers=headers)
        content = response.data.decode('utf-8')
        # TODO: 多线程，等待15秒图片生成
        if content:
            if result['code'] == 0:
                print(result['data']['task_list']['results'])  # 换装结果图url
                pic_url = result['data']['task_list']['results']

    else:
        print(result['Detail'])  # 错误信息
