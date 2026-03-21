import requests
import os
import time
from gtts import gTTS

TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]
GROQ_API_KEY = os.environ["CLAUDE_KEY"]

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
    prompt = (
        f"Generate a Telegram message for Bhagavad Gita Chapter {chapter}, Verse {verse}.\n"
        f"Use this exact format with a blank line between every section:\n\n"
        f"Namaste friends,\n\n"
        f"Today's verse: Bhagavad Gita Chapter {chapter}, Verse {verse}\n\n"
        f"Sanskrit Shloka: [actual shloka]\n\n"
        f"Pronunciation: [pronunciation]\n\n"
        f"Translation: [translation]\n\n"
        f"Explanation for kids: [simple explanation]\n\n"
        f"Daily Life Lessons:\n"
        f"1. [lesson 1]\n"
        f"2. [lesson 2]\n"
        f"3. [lesson 3]\n\n"
        f"Jai Shri Krishna\n\n"
        f"IMPORTANT: Keep a blank line between every section. Do not merge any sections together."
    )
    for attempt in range(1, 4):
        print(f"Calling Groq API (attempt {attempt}/3)...")
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 1024
            },
            timeout=60
        )
        resp_json = response.json()
        if response.status_code == 200 and "choices" in resp_json:
            return resp_json["choices"][0]["message"]["content"]
        code = response.status_code
        print(f"API error (code {code}): {resp_json}")
        if code == 429 and attempt < 3:
            wait = 30 * attempt
            print(f"Rate limited. Waiting {wait}s before retry...")
            time.sleep(wait)
        else:
            raise Exception(f"Groq API failed after {attempt} attempt(s): {resp_json}")
    raise Exception("Max retries exceeded")

def generate_audio(message):
    clean = message
    for s in ["*", "_", "`", "#", "~"]:
        clean = clean.replace(s, "")
    tts = gTTS(text=clean, lang="en", slow=False)
    tts.save("verse_audio.mp3")
    print("Audio generated")

def send_text(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    r = requests.post(url, json={
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }, timeout=30)
    print(f"Text sent: {r.status_code}")
    if r.status_code != 200:
        print(f"Telegram error: {r.text}")

def send_audio(chapter, verse):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendAudio"
    with open("verse_audio.mp3", "rb") as audio:
        r = requests.post(url,
            data={
                "chat_id": CHAT_ID,
                "title": f"Gita Ch{chapter} V{verse}",
                "performer": "Gita Daily"
            },
            files={"audio": audio},
            timeout=60
        )
    print(f"Audio sent: {r.status_code}")
    if r.status_code != 200:
        print(f"Telegram error: {r.text}")

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
