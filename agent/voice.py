# agent/voice.py — Deepgram STT and TTS
import os
import time
import requests
import sounddevice as sd
import soundfile as sf
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "../.env"))

DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY", "")

def record_audio(duration=5, filename="input.wav", samplerate=16000):
    """Record audio from the microphone."""
    print(f"\n🎤 Recording for {duration} seconds (speak now)...")
    myrecording = sd.rec(int(duration * samplerate), samplerate=samplerate, channels=1)
    
    # Simple countdown
    for i in range(duration, 0, -1):
        print(f"   ⏳ {i}s remaining...", end='\r')
        time.sleep(1)
        
    sd.wait()
    sf.write(filename, myrecording, samplerate)
    print("✅ Recording complete.          ")
    return filename


def transcribe_audio(filename="input.wav") -> str:
    """Convert speech to text using Deepgram."""
    if not DEEPGRAM_API_KEY or DEEPGRAM_API_KEY == "your_deepgram_api_key_here":
        return "DEEPGRAM_API_KEY not configured"

    print("🧠 Transcribing audio...")
    url = "https://api.deepgram.com/v1/listen?model=nova-2&smart_format=true"
    headers = {
        "Authorization": f"Token {DEEPGRAM_API_KEY}"
    }
    
    with open(filename, "rb") as f:
        response = requests.post(url, headers=headers, data=f)
        
    if response.status_code == 200:
        data = response.json()
        try:
            transcript = data["results"]["channels"][0]["alternatives"][0]["transcript"]
            return transcript
        except KeyError:
            return ""
    else:
        print(f"❌ Transcription error: {response.status_code} - {response.text}")
        return ""


def speak_text(text: str, filename="output.mp3"):
    """Convert text to speech using Deepgram and play it."""
    if not DEEPGRAM_API_KEY or DEEPGRAM_API_KEY == "your_deepgram_api_key_here":
        print("❌ DEEPGRAM_API_KEY not configured for TTS")
        return

    # Clean the text (remove markdown formatting)
    clean_text = text.replace("*", "").replace("#", "")

    print("🗣️  Generating voice reply...")
    url = "https://api.deepgram.com/v1/speak?model=aura-asteria-en"
    headers = {
        "Authorization": f"Token {DEEPGRAM_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {"text": clean_text}

    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 200:
        with open(filename, "wb") as f:
            f.write(response.content)
        # Play the audio using macOS native afplay
        os.system(f"afplay {filename}")
    else:
        print(f"❌ TTS error: {response.status_code} - {response.text}")
