FROM python:3.10.4-slim-buster

# Install system dependencies
RUN apt update && apt install -y git curl ffmpeg && apt clean

# Install Python dependencies
COPY requirements.txt .
RUN pip3 install --upgrade pip wheel && \
    pip3 install --no-cache-dir -r requirements.txt

# Set working directory and copy project files
WORKDIR /app
COPY . .

# Run your module
CMD ["python3", "-m", "snigdha"]
