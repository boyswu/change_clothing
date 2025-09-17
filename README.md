# Change Clothing Project

## 简介

**Change Clothing** 是一个基于 Python 和 FastAPI 的虚拟换衣项目。它提供了图像处理、服装替换、用户接口和工具集成，帮助用户实现人物图像的虚拟换装效果。

## 功能特性

* 🧑‍💻 **FastAPI 接口**：提供用户相关的接口服务。
* 👕 **虚拟换衣**：支持人物图像与不同服装图片的替换。
* ⚡ **工具模块**：包含图像处理、异步处理、缓存、加密、上传和邮件发送等功能。
* 💾 **数据库支持**：通过 `connect_tool` 提供数据库连接与操作。
* 🖼 **示例图片**：提供多种服装和人物样例图片（如 `dress.jpg`, `trousers.jpg`）。

## 目录结构

```
change_clothing-master/
├── README.md              # 项目说明文档
├── main.py                # 项目入口文件
├── Fastapi/               # FastAPI 接口模块
│   └── fastapi_user.py
├── Model/                 # 模型定义
│   └── ToDoModel.py
├── Tool/                  # 工具类模块
│   ├── API.py
│   ├── DeepSeek.py
│   ├── Kolors_to_image.py
│   ├── Threading_await.py
│   ├── cache_code.py
│   ├── downland_url.py
│   ├── email_send.py
│   ├── minion_bag.py
│   ├── password_utf.py
│   ├── tokens.py
│   └── upload.py
├── connect_tool/          # 数据库与连接工具
│   ├── minion_connect.py
│   └── sql.py
└── image/                 # 示例图片
    ├── dress.jpg
    ├── long_clothing.jpg
    ├── people.jpg
    ├── person.jpg
    ├── short_clothing.jpg
    └── trousers.jpg
```

## 环境依赖

请确保已安装以下依赖：

* Python >= 3.8
* FastAPI
* Uvicorn
* Pillow
* requests
* 其他依赖请参考代码中的 `import`。

安装依赖：

```bash
pip install -r requirements.txt
```

（如果没有 `requirements.txt`，请手动安装 FastAPI、Uvicorn 及常用依赖）

## 使用方法

1. 克隆或下载本项目：

```bash
git clone <repo-url>
cd change_clothing-master
```

2. 启动 FastAPI 服务：

```bash
uvicorn Fastapi.fastapi_user:app --reload
```

服务启动后，可通过 `http://127.0.0.1:8000` 访问。

3. 或直接运行主程序：

```bash
python main.py
```

## 示例

项目内置了一些示例图片（人物和服装），可用于测试换衣功能。

## 作者

**wujiahang**

---
