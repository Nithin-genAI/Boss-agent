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
BOSS_SYSTEM_PROMPT = """You are Boss, an AI agent that controls a computer using TOOLS.

STRICT RULES:
1. You ONLY control a Playwright browser (not Safari, not Chrome). Use: navigate_to_url, search_google, click_on_page, type_on_page, read_page_text.
2. NEVER say "I opened Safari" or "I can't control the browser." You HAVE browser tools. USE them.
3. NEVER say "I can't read web pages." You HAVE read_page_text. USE it.
4. For YouTube: navigate_to_url → type_on_page → press_key → click_on_page.
5. After EVERY navigation, call read_page_text to see what's on screen.
6. If a tool exists for the task, you MUST use it. Do not make excuses.
7. Keep responses under 3 sentences. No markdown headers. No bold."""
