FROM python:3.10.4-slim-buster

RUN apt update && apt install -y git curl ffmpeg && apt clean

COPY requirements.txt .
RUN pip3 install --upgrade pip wheel && \
    pip3 install --no-cache-dir -r requirements.txt

WORKDIR /app
COPY . .

CMD ["python3", "-m", "snigdha"]
