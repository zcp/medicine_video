import uvicorn

from dotenv import load_dotenv
import os

# 加载当前目录的 .env 文件
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8002, reload=True)