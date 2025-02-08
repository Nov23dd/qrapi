# 使用官方 Python 基礎映像
FROM python:3.8

# 設置工作目錄
WORKDIR /app

# 復制當前目錄內容到工作目錄
COPY . /app

# 安裝依賴項
RUN pip install -r requirements.txt

# 安裝 WeasyPrint 依賴項
RUN apt-get update && apt-get install -y \
    libpangocairo-1.0-0 libcairo2 libgdk-pixbuf2.0-0

# 暴露 Flask 默認端口
EXPOSE 5000

# 運行應用
CMD ["python", "qr_api.py"]
