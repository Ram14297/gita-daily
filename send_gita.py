def generate_message(chapter, verse):
    prompt = f"Generate a Telegram message for Bhagavad Gita Chapter {chapter}, Verse {verse}. Include: Sanskrit Shloka, Pronunciation, Translation, simple Explanation like for a child, and 3 Daily Life lessons. End with Jai Shri Krishna."
    
    response = requests.post(
        f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={CLAUDE_KEY}",
        headers={"content-type": "application/json"},
        json={
            "contents": [{"parts": [{"text": prompt}]}]
        }
    )
    resp_json = response.json()
    print("Gemini API response keys:", list(resp_json.keys()))
    if "candidates" not in resp_json:
        raise Exception(f"Gemini API Error: {resp_json}")
    return resp_json["candidates"][0]["content"]["parts"][0]["text"]

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
