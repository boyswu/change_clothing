from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from Fastapi import fastapi_user
import uvicorn
import fastapi_cdn_host

app = FastAPI()
# monkey_patch_for_docs_ui(app)
fastapi_cdn_host.patch_docs(app)
# 2、声明一个 源 列表；重点：要包含跨域的客户端 源
origins = ['*']

# 3、配置 CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # 允许访问的源
    allow_credentials=True,  # 支持 cookie
    allow_methods=["*"],  # 允许使用的请求方法
    allow_headers=["*"]  # 允许携带的 Headers
)

app.include_router(fastapi_user.router)

"""
终端运行该命令启动后端接口服务：uvicorn main:app --reload --port 8080
"""
#
# if __name__ == '__main__':
#     uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=8000)
