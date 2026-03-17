import requests
import os
from gtts import gTTS

# === CONFIG ===
TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]
CLAUDE_KEY = os.environ["CLAUDE_KEY"]

# Total verses per chapter
VERSES = {1:47, 2:72, 3:43, 4:42, 5:29, 6:47, 7:30, 8:28,
          9:34, 10:42, 11:55, 12:20, 13:35, 14:27, 15:20,
          16:24, 17:28, 18:78}

def get_current_verse():
    with open("verse_tracker.txt", "r") as f:
        ch, vs = map(int, f.read().strip().split(":"))
    return ch, vs

def save_next_verse(ch, vs):
    if vs < VERSES[ch]:
        next_ch, next_vs = ch, vs + 1
    elif ch < 18:
        next_ch, next_vs = ch + 1, 1
    else:
        next_ch, next_vs = 1, 1
    with open("verse_tracker.txt", "w") as f:
        f.write(f"{next_ch}:{next_vs}")
    print(f"Next verse saved: Chapter {next_ch}, Verse {next_vs}")

def generate_message(chapter, verse):
    prompt = f"Generate a Telegram message for Bhagavad Gita Chapter {chapter}, Verse {verse}. Include: Sanskrit Shloka, Pronunciation, Translation, simple Explanation like for a child, and 3 Daily Life lessons. End with Jai Shri Krishna."
    response = requests.post(
        f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={CLAUDE_KEY}",
        headers={"content-type": "application/json"},
        json={"contents": [{"parts": [{"text": prompt}]}]}
    )
    resp_json = response.json()
    print("API response keys:", list(resp_json.keys()))
    if "candidates" not in resp_json:
        raise Exception(f"API Error: {resp_json}")
    return resp_json["candidates"][0]["content"]["parts"][0]["text"]

def generate_audio(message):
    clean = message
    for s in ["*", "_", "`", "#", "~"]:
        clean = clean.replace(s, "")
    tts = gTTS(text=clean, lang="en", slow=False)
    tts.save("verse_audio.mp3")
    print("Audio generated")

def send_text(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    r = requests.post(url, json={"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"})
    print(f"Text sent: {r.status_code}")

def send_audio(chapter, verse):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendAudio"
    with open("verse_audio.mp3", "rb") as audio:
        r = requests.post(url,
            data={"chat_id": CHAT_ID, "title": f"Gita Ch{chapter} V{verse}", "performer": "Gita Daily"},
            files={"audio": audio})
    print(f"Audio sent: {r.status_code}")

if __name__ == "__main__":
    ch, vs = get_current_verse()
    print(f"Sending Chapter {ch}, Verse {vs}")
    message = generate_message(ch, vs)
    print("Message generated")
    send_text(message)
    generate_audio(message)
    send_audio(ch, vs)
    save_next_verse(ch, vs)
    print("Done!")
