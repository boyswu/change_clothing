import json

import urllib3
import uuid

host = 'https://damotryon.market.alicloudapi.com'
method = 'POST'
appcode = 'c29f5e38c5b24c38bd8f7332db2b0590'
querys = ''
bodys = {}
http = urllib3.PoolManager()
headers = {
    'X-Ca-Nonce': str(uuid.uuid4()),  # 需要给X-Ca-Nonce的值生成随机字符串，每次请求不能相同
    'Content-Type': 'application/json; charset=UTF-8',
    'Authorization': 'APPCODE ' + appcode
}


def change_clothes_api(fit_type, model_image, tops_image, pants_image):
    path = '/api/v1/tryon/submit'
    url = host + path
    if fit_type not in ['FULL_BODY', 'HALF_BODY']:
        print('fit_type参数错误')
        return False

    task = {
        "model_image": model_image,  # 模特图,必填
        "tops_image": tops_image  # 上装图,必填
    }
    if fit_type == 'HALF_BODY' and pants_image:
        task['pants_image'] = pants_image  # 下装图,选填

    data = {
        "data": {
            "fit_type": fit_type,  # 换装类型枚举，FULL_BODY：全身换装，HALF_BODY:半身换装(不加裤子)
            "inference_num": 1,  # 单任务算法结果数量（1~4）
            "task_list": [task]  # 任务列表,最多10项
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
            print(result['data']['result_key'])  # 任务key
            result_key = result['data']['result_key']
            return result_key
        else:
            print(result['message'])  # 错误信息
            error_msg = result['message']
            return error_msg
    else:
        print('请求失败')
        return False


def get_result_api(result_keys):
    path = '/api/v1/tryon/query'
    url = host + path
    # 使用字典来构建请求体
    data_dict = {
        "data": {
            "result_key": result_keys  # 任务key，见任务提交接口返回字段result_key
        }
    }
    # 将字典转换为JSON字符串
    bodys[''] = json.dumps(data_dict)
    post_data = bodys['']
    response = http.request('POST', url, body=post_data, headers=headers)
    content = response.data.decode('utf-8')
    if content:
        result = json.loads(content)
        print(result)
        if result['code'] == 0:
            task_list = result['data']['task_list']  # task_list 是一个列表
            # print("task_list:", task_list)
            # 确保 task_list 不为空
            task_status = task_list[0]['status']  # 获取第一个任务的状态
            if task_status == 'SUCCESS':
                pic_url = task_list[0]['results'][0]
                return pic_url
            elif task_status == 'RUNNING':
                print('任务正在处理中')
                return 'RUNNING'
            else:
                print('任务处理失败')
                return False
        else:
            print(result['message'])  # 错误信息
            error_msg = result['message']
            return error_msg
    else:
        print('请求失败')
        return False


if __name__ == '__main__':
    # fit_type = 'HALF_BODY'  # 换装类型枚举，FULL_BODY：全身换装，HALF_BODY:半身换装(不加裤子)
    # model_image = 'http://43.143.229.40:9000/2303080206/clothes/person.jpg'  # 模特图,必填
    # tops_image = 'http://43.143.229.40:9000/2303080206/clothes/short_clothing.jpg'  # 上装图,必填
    # pants_image = 'https://img.alicdn.com/imgextra/i3/O1CN01hOE0jo1ZnyBltsGnF_!!6000000003240-2-tps-1000-1000.png'  # 下装图,选填
    # result_key = change_clothes_api(fit_type, model_image, tops_image, pants_image)
    # print(result_key)
    result_key = "b5fa0abd833a40908f0bf42e30a06da7" #half body 加裤子
    # result_key = "318c9869c5234db6b12d763bf303ec0d" #full body 加裤子
    # result_key = "318c9869c5234db6b12d763bf303ec0d" #full body 不加裤子
    # result_key = "702b9a2d1125463b94decbdec1fef009" #half body 不加裤子
    pict_url = get_result_api(result_key)
    print(pict_url)
