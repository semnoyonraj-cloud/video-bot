FROM python:3.9-slim

# ffmpeg ইনস্টল করা হচ্ছে
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# পাইথন প্যাকেজগুলো ইনস্টল করা হচ্ছে
RUN pip install --no-cache-dir telethon Pillow yt-dlp

COPY . .

EXPOSE 10000

# বট রান করার কমান্ড
CMD ["python", "main.py"]
