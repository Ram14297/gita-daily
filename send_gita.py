import requests
import os
import urllib.parse
from gtts import gTTS

# === CONFIG ===
TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]
CLAUDE_KEY = os.environ["CLAUDE_KEY"]

# Total verses per chapter
VERSES = {1:47, 2:72, 3:43, 4:42, 5:29, 6:47, 7:30, 8:28,
          9:34, 10:42, 11:55, 12:20, 13:35, 14:27, 15:20,
          16:24, 17:28, 18:78}

# =====================
# VERSE TRACKER
# =====================
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
        next_ch, next_vs = 1, 1  # restart after all 700 verses
    with open("verse_tracker.txt", "w") as f:
        f.write(f"{next_ch}:{next_vs}")
    print(f"Next verse saved: Chapter {next_ch}, Verse {next_vs}")

# =====================
# GENERATE MESSAGE
# =====================
def generate_message(chapter, verse):
    prompt = f"""Generate a Telegram message for Bhagavad Gita Chapter {chapter}, Verse {verse}.

Use Telegram markdown formatting. Format EXACTLY like this:

🕉️ *Hinduism Lessons*

*Chapter {chapter} | Verse {verse}*

📿 *Sanskrit Shloka:*
[Sanskrit text here]

🔤 *Pronunciation:*
[Roman transliteration here]

📖 *Translation:*
"[Simple English translation here]"

💡 *Explanation:*
[Explain very simply, like explaining to a child. 3-4 sentences. Anyone should understand.]

🌱 *How to Apply in Daily Life:*
1. [Practical lesson 1]
2. [Practical lesson 2]
3. [Practical lesson 3]

_Jai Shri Krishna_ 🙏"""

    response = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": CLAUDE_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        },
        json={
            "model": "claude-haiku-4-5-20251001",
            "max_tokens": 1000,
            "messages": [{"role": "user", "content": prompt}]
        }
    )
    resp_json = response.json()
    print("Claude API full response:", resp_json)
    if "content" not in resp_json:
        raise Exception(f"Claude API Error: {resp_json}")
    return resp_json["content"][0]["text"]

# =====================
# GENERATE AUDIO
# =====================
def generate_audio(message):
    # Remove markdown symbols so audio sounds natural
    clean = message
    for symbol in ["*", "_", "`", "#", "🕉️", "📿", "🔤",
                   "📖", "💡", "🌱", "🙏", "~"]:
        clean = clean.replace(symbol, "")
    tts = gTTS(text=clean, lang='en', slow=False)
    tts.save("verse_audio.mp3")
    print("Audio generated successfully")

# =====================
# SEND TEXT TO TELEGRAM
# =====================
def send_text(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    response = requests.post(url, json={
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    })
    print(f"Text sent — Status: {response.status_code}")

# =====================
# SEND AUDIO TO TELEGRAM
# =====================
def send_audio(chapter, verse):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendAudio"
    with open("verse_audio.mp3", "rb") as audio:
        response = requests.post(url,
            data={
                "chat_id": CHAT_ID,
                "title": f"Gita Ch{chapter} Verse{verse}",
                "performer": "Gita Daily 🕉️"
            },
            files={"audio": audio}
        )
    print(f"Audio sent — Status: {response.status_code}")

# =====================
# MAIN
# =====================
if __name__ == "__main__":
    ch, vs = get_current_verse()
    print(f"Sending Chapter {ch}, Verse {vs}")

    # Step 1 — Generate message content
    message = generate_message(ch, vs)
    print("Message generated")

    # Step 2 — Send text message
    send_text(message)

    # Step 3 — Generate and send audio
    generate_audio(message)
    send_audio(ch, vs)

    # Step 4 — Advance tracker to next verse
    save_next_verse(ch, vs)
    print("Done! ✅")
