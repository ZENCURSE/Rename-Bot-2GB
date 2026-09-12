WORKDIR /app

# Install FFmpeg - FIX FOR METADATA
RUN apt-get update && apt-get install -y ffmpeg && apt-get clean && rm -rf /var/lib/apt/lists/*

COPY . /app/
RUN pip3 install -r requirements.txt

CMD ["python3", "bot.py"]
