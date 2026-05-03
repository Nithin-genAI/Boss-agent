# agent/gui.py — Simple Jarvis-like Web GUI for Boss Agent
import os
import uuid
import base64
import requests
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel

from boss_kernel import BossKernel
from tools.system_tools import *
from tools.visual_tools import *
from tools.selenium_tools import *
from tools.api_tools import *
from tools.vision_tools import *
from tools.github_tools import *
from voice import transcribe_audio, DEEPGRAM_API_KEY

app = FastAPI()

# Initialize Boss
print("Initializing Boss Kernel...")
boss = BossKernel(model_key="default", user_id="ramesh")
boss.register_tools([
    get_system_info, get_current_time, find_file,
    search_file_content, read_file, list_directory,
    summarize_directory, run_shell_command,
    take_screenshot, open_application, open_folder,
    browser_go, browser_search, browser_click,
    browser_type, browser_press, browser_read,
    browser_screenshot, browser_close, browser_get_url,
    get_weather, get_news, get_crypto_price, translate_text,
    get_joke, send_email, create_reminder, book_flight,
    analyze_image,
    github_create_repo, github_get_repo, github_read_readme,
    github_update_repo, github_list_repos,
    github_create_issue, github_list_issues,
    github_comment_on_issue, github_close_issue,
    github_create_file, github_search_code
])

class ChatRequest(BaseModel):
    text: str

class VoiceRequest(BaseModel):
    audio_base64: str

# Ensure audio output directory exists
os.makedirs("audio_cache", exist_ok=True)

def generate_tts(text: str) -> str:
    """Generate TTS via Deepgram and return filename."""
    if not DEEPGRAM_API_KEY or DEEPGRAM_API_KEY == "your_deepgram_api_key_here":
        return ""
    
    clean_text = text.replace("*", "").replace("#", "")
    filename = f"audio_cache/resp_{uuid.uuid4().hex}.mp3"
    
    url = "https://api.deepgram.com/v1/speak?model=aura-asteria-en"
    headers = {
        "Authorization": f"Token {DEEPGRAM_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {"text": clean_text}
    
    resp = requests.post(url, headers=headers, json=payload)
    if resp.status_code == 200:
        with open(filename, "wb") as f:
            f.write(resp.content)
        return filename
    return ""

@app.get("/")
def get_ui():
    with open("ui.html", "r", encoding="utf-8") as f:
        return HTMLResponse(f.read())

@app.post("/chat")
def chat(req: ChatRequest):
    print(f"You: {req.text}")
    response = boss.think(req.text)
    print(f"Boss: {response}")
    
    audio_file = generate_tts(response)
    audio_url = f"/audio/{os.path.basename(audio_file)}" if audio_file else ""
    
    return {"response": response, "audio_url": audio_url}

@app.post("/voice")
def voice_chat(req: VoiceRequest):
    # Decode incoming base64 webm audio
    audio_data = base64.b64decode(req.audio_base64)
    input_file = f"audio_cache/input_{uuid.uuid4().hex}.webm"
    with open(input_file, "wb") as f:
        f.write(audio_data)
        
    transcript = transcribe_audio(input_file)
    if not transcript or "DEEPGRAM" in transcript:
        return {"transcript": "", "response": "Could not understand audio.", "audio_url": ""}
        
    print(f"You (Voice): {transcript}")
    response = boss.think(transcript)
    print(f"Boss: {response}")
    
    audio_file = generate_tts(response)
    audio_url = f"/audio/{os.path.basename(audio_file)}" if audio_file else ""
    
    return {"transcript": transcript, "response": response, "audio_url": audio_url}

@app.get("/audio/{filename}")
def get_audio(filename: str):
    return FileResponse(f"audio_cache/{filename}")

if __name__ == "__main__":
    print("\n🚀 Starting Boss Web GUI on http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="warning")
