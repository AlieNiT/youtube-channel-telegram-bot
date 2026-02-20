import os, json, logging, requests, yt_dlp
from telegram import Bot
from telegram.error import TelegramError
import xml.etree.ElementTree as ET

BOT_TOKEN  = os.environ["BOT_TOKEN"]
CHAT_ID    = os.environ["CHAT_ID"]
CHANNEL_ID = os.environ["CHANNEL_ID"]
STATE_FILE = "state.json"
AUDIO_FILE = "audio.mp3"

logging.basicConfig(format="%(asctime)s [%(levelname)s] %(message)s", level=logging.INFO)
log = logging.getLogger(__name__)

def get_latest_video(channel_id):
    rss_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
    resp = requests.get(rss_url, timeout=15)
    resp.raise_for_status()
    ns = {"yt": "http://www.youtube.com/xml/schemas/2015",
          "atom": "http://www.w3.org/2005/Atom"}
    root = ET.fromstring(resp.text)
    entry = root.find("atom:entry", ns)
    if entry is None:
        return None
    return {
        "id":    entry.findtext("yt:videoId", namespaces=ns),
        "title": entry.findtext("atom:title",  namespaces=ns),
    }

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            return json.load(f)
    return {"last_seen_id": None}

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)

def download_audio(video_id):
    url = f"https://www.youtube.com/watch?v={video_id}"
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": AUDIO_FILE.replace(".mp3", ".%(ext)s"),
        "postprocessors": [{"key": "FFmpegExtractAudio",
                            "preferredcodec": "mp3", "preferredquality": "192"}],
        "quiet": True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

def main():
    state = load_state()
    last_seen_id = state.get("last_seen_id")

    video = get_latest_video(CHANNEL_ID)
    if not video:
        log.warning("Could not fetch latest video.")
        return

    if video["id"] == last_seen_id:
        log.info("No new video.")
        return

    if last_seen_id is None:
        log.info("First run — recording latest video without sending.")
        save_state({"last_seen_id": video["id"]})
        return

    log.info("New video: %s", video["title"])
    download_audio(video["id"])
    bot = Bot(token=BOT_TOKEN)
    with open(AUDIO_FILE, "rb") as f:
        bot.send_audio(chat_id=CHAT_ID, audio=f, title=video["title"])
    log.info("Sent!")
    os.remove(AUDIO_FILE)
    save_state({"last_seen_id": video["id"]})

if __name__ == "__main__":
    main()
