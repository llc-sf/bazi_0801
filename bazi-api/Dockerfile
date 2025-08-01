FROM python:3.11-slim
RUN apt-get update && apt-get install -y build-essential vim curl \
 && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt .

RUN pip install --upgrade pip -i https://mirrors.aliyun.com/pypi/simple/ && \
    pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/

RUN pip install --no-cache-dir -r requirements.txt
COPY app/ ./app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

# CMD ["tail", "-f", "/dev/null"]

