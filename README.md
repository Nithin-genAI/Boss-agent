
readme_content = """# 🤖 Boss Agent — Autonomous Multi-Agent Voice Assistant

> **Beyond Chatbots. Real Task Completion.**
> 
> An agentic AI assistant that controls your computer, browses the web, calls real APIs, and remembers everything — built for the Voice Agent Hackathon.

---

## 🎯 What is Boss?

Boss is an autonomous AI agent that **completes real tasks**, not just answers questions. Unlike chatbots that forget context after every message, Boss maintains persistent memory, handles multi-step workflows, and takes actual actions on your behalf.

### Key Capabilities

| Feature | Description |
|---------|-------------|
| 🧠 **Persistent Memory** | Remembers your name, preferences, and conversation history across sessions (powered by Mem0) |
| 🌐 **Web Browser Control** | Opens Chrome, navigates websites, clicks buttons, fills forms, reads page content |
| 💻 **System Control** | Reads files, lists directories, opens apps, runs safe shell commands |
| 🌤️ **Real-Time APIs** | Live weather, news, crypto prices, translation — no mock data |
| 👁️ **Vision Analysis** | Analyzes screenshots and images using Gemini 2.5 Flash |
| 🔄 **Multi-Step Workflows** | Books tables, checks orders, plans trips — tracks state across turns |
| 🛡️ **Safety & Resilience** | Retries failed calls, circuit breakers, policy blocks, undo stack |
| 🎙️ **Voice Ready** | Architecture prepared for Whisper STT + Kokoro TTS integration |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────┐
│           USER (Voice/Text)             │
└─────────────────┬───────────────────────┘
                  ▼
┌─────────────────────────────────────────┐
│  INTENT ROUTER (Zero-Tolerance)         │
│  • Classifies: NEW_TASK / CORRECTION    │
│    / CANCEL / WEB_ACTION / SHELL / CHAT │
│  • Prevents intent drift & restarts     │
└─────────────────┬───────────────────────┘
                  ▼
┌─────────────────────────────────────────┐
│  ORCHESTRATOR (Multi-Agent Conductor)   │
│  • BrowserAgent  → Chrome/Selenium      │
│  • SystemAgent   → Files, Apps, Shell   │
│  • MemoryAgent   → Mem0 / Local JSON    │
│  • CriticAgent   → Validates outputs    │
└─────────────────┬───────────────────────┘
                  ▼
┌─────────────────────────────────────────┐
│  STATE MACHINE (Task Tracker)           │
│  • Tracks: collecting → confirming    │
│    → executing → completed              │
│  • Handles corrections without restart  │
│  • Manages missing fields per task      │
└─────────────────┬───────────────────────┘
                  ▼
┌─────────────────────────────────────────┐
│  RESILIENCE STACK                       │
│  • Retry Engine (exponential backoff)   │
│  • Circuit Breaker (3 failures = stop)  │
│  • Fallback Chain (alt tools)           │
│  • Error Translator (user-friendly)     │
│  • Safety Policy (blocks rm -rf /)      │
│  • Undo Stack (reversible actions)      │
└─────────────────┬───────────────────────┘
                  ▼
┌─────────────────────────────────────────┐
│  TOOL REGISTRY (Pluggable Tools)        │
│  • System: files, shell, screenshots    │
│  • Browser: Chrome via Selenium        │
│  • APIs: weather, news, crypto, translate│
│  • Vision: Gemini image analysis        │
│  • Mock: email, reminders, flights      │
└─────────────────────────────────────────┘
```

---

## 📁 Project Structure

```
Boss-agent/
├── agent/
│   ├── main.py                    # Entry point (interactive mode)
│   ├── boss_kernel.py             # Core orchestrator + intent routing
│   ├── config.py                  # API keys, model settings, prompts
│   │
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── registry.py            # Tool registration & execution
│   │   ├── resilient_registry.py  # Retry + circuit breaker wrapper
│   │   ├── system_tools.py        # File ops, shell, screenshots
│   │   ├── selenium_tools.py      # Chrome browser control
│   │   ├── api_tools.py           # Weather, news, crypto, translate
│   │   └── vision_tools.py        # Gemini image analysis
│   │
│   ├── memory/
│   │   ├── __init__.py
│   │   ├── short_term.py          # Last 10 conversation turns
│   │   ├── working.py             # Active task state
│   │   └── long_term.py           # Mem0 / local JSON persistence
│   │
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── planner.py             # Task decomposition
│   │   ├── browser_agent.py       # Web automation specialist
│   │   ├── system_agent.py        # Computer control specialist
│   │   ├── memory_agent.py        # Memory operations specialist
│   │   └── critic.py              # Output validation
│   │
│   ├── state_machine.py           # Task state tracking
│   ├── intent_router.py           # Intent classification (zero-tolerance)
│   │
│   ├── tasks/
│   │   ├── __init__.py
│   │   └── templates.py           # Pre-built task workflows
│   │
│   ├── resilience/
│   │   ├── __init__.py
│   │   ├── retry_engine.py        # Exponential backoff retries
│   │   ├── circuit_breaker.py     # Failure threshold blocking
│   │   ├── fallback.py            # Alternative tool chains
│   │   └── error_translator.py    # User-friendly errors
│   │
│   └── safety/
│       ├── __init__.py
│       ├── classifier.py          # READ / WRITE / DESTRUCTIVE tags
│       ├── confirmation_gate.py   # Smart confirmation prompts
│       ├── undo_stack.py          # Action reversal
│       └── policy.py              # Hard security rules
│
├── .env                           # API keys (never commit)
├── requirements.txt               # Python dependencies
└── README.md                      # This file
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.12+
- macOS (for system tools & Safari/Chrome control)
- Chrome + ChromeDriver installed
- OpenRouter API key (free tier)
- Mem0 API key (optional, falls back to local JSON)
- Groq API key (optional, for vision)

### Installation

```bash
# Clone the repository
git clone <your-repo-url>
cd Boss-agent

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install ChromeDriver (macOS)
brew install chromedriver
xattr -cr /opt/homebrew/bin/chromedriver  # Allow macOS security

# Set environment variables
cp .env.example .env
# Edit .env with your keys:
#   OPENROUTER_API_KEY=sk-or-v1-...
#   MEM0_API_KEY=m0-...          (optional)
#   GROQ_API_KEY=gsk-...         (optional)
```

### Run Boss

```bash
cd agent
python main.py
```

You'll see:
```
============================================================
  🤖 BOSS AGENT — PHASE 9: REAL APIS + VISION
  Commands: exit | reset | status | undo | mock
============================================================

🧠 Boss Kernel initialized
   Model: openai/gpt-oss-120b:free
   User: ramesh
   Tools loaded: [28 tools]
   Resilience: Retry=2, Circuit=3 failures, Mock=OFF

You:
```

---

## 🎮 Demo Commands

### Real-Time APIs
```
You: What's the weather in Boston?
Boss: ☀️ Clear sky in Boston, United States
     🌡️ Now: 18°C
     💧 Humidity: 45%
     💨 Wind: 12 km/h
     📈 Today: High 22° / Low 14°

You: Bitcoin price
Boss: Bitcoin: $67,420.50 📈 (+2.34% / 24h)

You: Top tech news
Boss: Hacker News Top Stories:
     • Show HN: I built an AI agent that... (234 pts)
     • ...

You: Translate 'hello world' to Spanish
Boss: Translated to Spanish: Hola mundo
```

### Browser Control
```
You: Open youtube.com and search for Feel the Power
Boss: Chrome: https://youtube.com | Title: YouTube
      Searched 'Feel the Power'. Results shown.

You: Open irctc.com
Boss: Chrome: https://irctc.co.in | Title: IRCTC
      The IRCTC website has opened.

You: Search Google for Python courses
Boss: Google results for 'Python courses':
      1. Python.org — Welcome to Python
      2. Coursera: Python for Everybody
      ...
```

### System Control
```
You: List files in current directory
Boss: Files:
      📄 main.py (2.4 KB)
      📄 boss_kernel.py (8.1 KB)
      📁 tools/
      📁 memory/
      ...

You: Read file config.py
Boss: File contents:
      # config.py — Boss Agent Configuration
      ...

You: Take a screenshot
Boss: Screenshot saved: /Users/ramesh/Desktop/boss_screenshot.png
```

### Vision Analysis
```
You: Take a screenshot and describe it
Boss: [Gemini analyzes screen]
      I see a terminal window showing the Boss Agent
      interactive mode. The user is testing the agent's
      capabilities. There are several files listed in
      the directory structure...

You: Analyze image ~/Desktop/photo.jpg
Boss: [Gemini analyzes image]
      This is a landscape photo showing a mountain
      range at sunset with vibrant orange and purple
      colors in the sky...
```

### Multi-Step Task (State Machine)
```
You: Book me a table
Boss: I'll help you with that. Which restaurant?

You: Oleana
Boss: What time?

You: 7pm
Boss: How many people?

You: 2
Boss: Ready: {"restaurant": "Oleana", "time": "7pm", "people": 2}. Proceed?

You: Actually make it 8pm
Boss: Updated time to 8pm. How many people?

You: 2
Boss: Ready: {"restaurant": "Oleana", "time": "8pm", "people": 2}. Proceed?

You: Yes
Boss: Executing your request...
      Done! book_restaurant completed successfully.
```

### Safety & Corrections
```
You: run command rm -rf /
Boss: BLOCKED: That command is permanently forbidden for safety.

You: Book me a table → Oleana → why people
Boss: I need a valid answer. How many people?

You: undo
Boss: Undid last action.

You: cancel
Boss: Cancelled. What would you like to do?
```

---

## 🔧 Configuration

### `.env` File

```bash
# Required
OPENROUTER_API_KEY=sk-or-v1-your-key-here

# Optional — enables persistent memory
MEM0_API_KEY=m0-your-key-here
MEM0_BASE_URL=https://api.mem0.ai/v1

# Optional — enables image analysis
GROQ_API_KEY=gsk-your-key-here

# Model selection (OpenRouter free tier)
DEFAULT_MODEL=openai/gpt-oss-120b:free
FAST_MODEL=google/gemma-2-9b-it:free
SMART_MODEL=nvidia/llama-3.1-nemotron-70b-instruct:free
```

### Model Options (Free Tier via OpenRouter)

| Model | Use Case |
|-------|----------|
| `openai/gpt-oss-120b:free` | Default — balanced reasoning |
| `google/gemma-2-9b-it:free` | Fast responses |
| `nvidia/llama-3.1-nemotron-70b-instruct:free` | Complex tasks |
| `qwen/qwen-2.5-coder-32b-instruct:free` | Code generation |

---

## 🧩 Core Components

### 1. Intent Router (Zero-Tolerance Classification)

Every user message is classified before processing. Prevents the #1 agent failure mode: **intent drift**.

```python
# Example classifications:
"Book me a table"          → NEW_TASK (book_restaurant)
"Actually make it 8pm"     → CORRECTION (time=8pm)
"Open youtube.com"         → WEB_ACTION
"run command ls"           → SHELL_COMMAND
"What's my name?"          → MEMORY_QUERY
"why people" (mid-task)    → CLARIFICATION (rejected)
"hey" / "hi"               → GENERAL_CHAT (no corruption)
```

### 2. State Machine (Task Tracking)

```
idle → collecting → confirming → executing → completed
              ↑________↓
              (corrections loop back)
```

- Tracks what fields are collected vs missing
- Handles "Actually..." without restarting
- Prevents garbage input ("why people") from corrupting state

### 3. Resilience Stack

| Layer | What It Does |
|-------|-------------|
| Retry Engine | 2 retries with exponential backoff + jitter |
| Circuit Breaker | 3 failures in 60s = block for 30s |
| Fallback Chain | read_file fails → try find_file |
| Error Translator | "Permission denied" → "Grant access in System Settings" |
| Safety Policy | Blocks `rm -rf /`, `sudo`, sensitive paths |
| Confirmation Gate | Destructive actions need typed "YES" |
| Undo Stack | Reverses file creation, app opens |

### 4. Memory Architecture

| Layer | Storage | Purpose |
|-------|---------|---------|
| Short-Term | In-memory (10 turns) | Conversation context |
| Working | In-memory | Active task state |
| Long-Term | Mem0 API / Local JSON | User preferences, facts, history |

---

## 🛡️ Safety Features

- **Command Blocklist**: `rm -rf /`, `sudo`, `mkfs`, `dd`, `:(){:|:&};:`
- **Path Blocklist**: `/etc/passwd`, `~/.ssh/id_rsa`, `/System`
- **Shell Restrictions**: No pipes (`|`), redirects (`>`), or subshells
- **Confirmation Required**: Destructive actions need explicit "YES"
- **Undo Available**: `undo` command reverses last action

---

## 🎙️ Voice Integration (Planned)

Architecture prepared for Team 1's voice server:

```
User Speech → Whisper STT (fine-tuned) → Boss Kernel → Kokoro TTS → User
                    ↑___________________________________________↓
                                    (interrupt handling)
```

- **STT**: OpenAI Whisper (fine-tuned locally for conversational turn-taking)
- **TTS**: Kokoro (fine-tuned locally for low-latency streaming)
- **VAD**: Voice Activity Detection for barge-in handling
- **WebSocket**: Real-time streaming pipeline

---

## 📊 Hackathon Demo Script (5 Minutes)

| Turn | User Says | Boss Does | Wow Factor |
|------|-----------|-----------|------------|
| 1 | "Good morning, what's my briefing?" | Weather + News + Crypto in one flow | Real APIs, live data |
| 2 | "Open IRCTC and search trains Bangalore to Mysore" | Chrome opens IRCTC, searches, reads results | Real browser control |
| 3 | "Take a screenshot and tell me what you see" | Screenshot → Gemini analyzes | Vision AI |
| 4 | "Actually I meant tomorrow not today" | Correction detected, updates date | No restart |
| 5 | "Book me a table at Oleana for 8pm, 2 people" | State machine collects, confirms, executes | Multi-step task |
| 6 | "Translate 'thank you' to Japanese" | 「ありがとう」 | Instant utility |
| 7 | "Send summary to my email" | Mock email sent | Action completion |

---

## 🐛 Troubleshooting

### Chrome won't launch
```bash
# Check Chrome is installed
/Applications/Google Chrome.app/Contents/MacOS/Google Chrome --version

# Reinstall ChromeDriver
brew reinstall chromedriver
xattr -cr /opt/homebrew/bin/chromedriver

# Check chromedriver version matches Chrome
chromedriver --version
```

### API calls fail
```bash
# Check API keys
echo $OPENROUTER_API_KEY
echo $GROQ_API_KEY

# Test OpenRouter directly
curl https://openrouter.ai/api/v1/auth/key \
  -H "Authorization: Bearer $OPENROUTER_API_KEY"
```

### Mem0 not connecting
- Falls back to local JSON automatically
- Check `boss_memory_default_user.json` in agent directory

---

## 🏆 Hackathon Criteria Mapping

| Criteria | How Boss Delivers |
|----------|-------------------|
| **Real task completion** | Browser automation + API calls + system control |
| **Handles failure gracefully** | Resilience stack + user-friendly errors |
| **Natural voice experience** | Prepared for Whisper + Kokoro integration |
| **Technical depth** | 12-phase architecture, multi-agent orchestration |
| **Innovation** | Mem0 persistent memory + local fine-tuned models |

---

## 📝 License

MIT License — Built for the Voice Agent Hackathon 2026.

---

## 🙏 Acknowledgments

- **OpenRouter** — Free tier LLM access
- **Mem0** — Persistent memory for AI agents
- **Groq** — Fast vision model inference
- **Open-Meteo / CoinGecko / HackerNews** — Free APIs
- **LangChain** — Tool framework
- **Selenium** — Browser automation

---

> **Boss doesn't just chat. Boss gets things done.**
"""

with open("/mnt/agents/output/README.md", "w", encoding="utf-8") as f:
    f.write(readme_content)

print("README.md created successfully!")
print(f"File size: {len(readme_content)} characters")
