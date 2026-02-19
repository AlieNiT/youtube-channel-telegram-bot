import os
import time
import requests
import feedparser
import subprocess

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
CHANNEL_ID = os.getenv("CHANNEL_ID")
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", 600))

RSS_URL = f"https://www.youtube.com/feeds/videos.xml?channel_id={CHANNEL_ID}"
LAST_FILE = "last_video.txt"

def get_latest_video():
    feed = feedparser.parse(RSS_URL)
    if not feed.entries:
        return None
    entry = feed.entries[0]
    return entry.yt_videoid, entry.link

def send_audio(file_path):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendAudio"
    with open(file_path, "rb") as f:
        requests.post(url, data={"chat_id": CHAT_ID}, files={"audio": f})

def download_audio(video_url):
    output = "audio.%(ext)s"
    subprocess.run(["yt-dlp", "-x", "--audio-format", "mp3", "--cookies", "cookies.txt", "-o", output, video_url])
    return "audio.mp3"

def main():
    while True:
        video = get_latest_video()
        if video:
            video_id, link = video
            last_id = None
            if os.path.exists(LAST_FILE):
                with open(LAST_FILE) as f:
                    last_id = f.read().strip()

            if video_id != last_id:
                audio_file = download_audio(link)
                send_audio(audio_file)
                with open(LAST_FILE, "w") as f:
                    f.write(video_id)

        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()
