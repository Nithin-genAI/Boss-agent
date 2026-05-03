# config.py — Boss Agent Configuration
import os
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# OpenRouter API (free tier)
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# Model selection
MODELS = {
    "default": "openai/gpt-oss-120b:free",                        # General reasoning
    "fast": "google/gemma-3-4b-it:free",                           # Quick responses
    "smart": "nvidia/nemotron-3-super-120b-a12b:free",             # Complex tasks
    "coding": "qwen/qwen3-coder:free",                             # Code generation
}

# Boss personality — now aware tools exist
BOSS_SYSTEM_PROMPT = """You are Boss, an AI agent that controls a macOS computer using TOOLS.

STRICT RULES:
1. You control the real Google Chrome browser natively. Use: browser_go, browser_search, browser_click, browser_type, browser_read, browser_get_url.
2. NEVER say "I opened Safari" or "I opened Playwright". You HAVE Chrome tools. USE them.
3. NEVER say "I can't read web pages." You HAVE read_page_text. USE it.
4. For YouTube: just use browser_go or browser_search.
5. If the user asks to analyze the screen or a website: FIRST use `take_screenshot` (or `browser_screenshot`), then pass the returned path to `analyze_image`. Do NOT use `analyze_image` without a valid path.
6. If a tool exists for the task (weather, crypto, news), you MUST use it. Do not make excuses.
7. Keep responses concise. No markdown headers. No bold."""
