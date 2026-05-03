# tools/vision_tools.py — Vision Analysis via Gemini
import os
import base64
import requests
from langchain_core.tools import tool

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")


@tool
def analyze_image(image_path: str, question: str = "What's in this image? Describe it in detail.") -> str:
    """
    Analyze an image using Google's Gemini vision model.
    Args:
        image_path: Path to image file (e.g., ~/Desktop/photo.jpg, /tmp/boss_screenshot.png)
        question: What to ask about the image
    """
    if not GEMINI_API_KEY:
        return "❌ Set GEMINI_API_KEY environment variable first."
    
    try:
        path = os.path.expanduser(image_path)
        if not os.path.exists(path):
            return f"Image not found: {path}"
        
        # Read and encode image
        with open(path, "rb") as f:
            image_b64 = base64.b64encode(f.read()).decode("utf-8")
        
        # Determine MIME type
        ext = os.path.splitext(path)[1].lower()
        mime = "image/jpeg" if ext in [".jpg", ".jpeg"] else "image/png" if ext == ".png" else "image/webp"
        
        # Call Gemini
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
        
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": question},
                        {
                            "inline_data": {
                                "mime_type": mime,
                                "data": image_b64
                            }
                        }
                    ]
                }
            ]
        }
        
        response = requests.post(
            url,
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=30
        ).json()
        
        if "error" in response:
            return f"Gemini error: {response['error'].get('message', str(response['error']))}"
        
        content = response["candidates"][0]["content"]["parts"][0]["text"]
        return f"👁️ Vision Analysis:\n\n{content}"
        
    except Exception as e:
        return f"Vision error: {str(e)[:100]}"



