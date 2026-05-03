# tools/api_tools.py — Real World APIs (Free Tier)
import os
import requests
from langchain_core.tools import tool


# ─── Weather (Open-Meteo, no key) ──────────────────────

@tool
def get_weather(city: str) -> str:
    """
    Get real weather for any city. Uses Open-Meteo API (free, no key needed).
    Args:
        city: City name like Boston, London, Tokyo
    """
    try:
        # Geocode
        geo = requests.get(
            f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1",
            timeout=10
        ).json()
        
        if not geo.get("results"):
            return f"City '{city}' not found. Try a different spelling."
        
        lat = geo["results"][0]["latitude"]
        lon = geo["results"][0]["longitude"]
        city_name = geo["results"][0]["name"]
        country = geo["results"][0].get("country", "")
        
        # Weather
        weather = requests.get(
            f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
            f"&current=temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m"
            f"&daily=temperature_2m_max,temperature_2m_min&timezone=auto",
            timeout=10
        ).json()
        
        current = weather["current"]
        daily = weather["daily"]
        
        # Weather code to emoji/text
        codes = {
            0: "☀️ Clear sky", 1: "🌤️ Mainly clear", 2: "⛅ Partly cloudy",
            3: "☁️ Overcast", 45: "🌫️ Fog", 48: "🌫️ Fog",
            51: "🌧️ Light drizzle", 53: "🌧️ Drizzle", 55: "🌧️ Heavy drizzle",
            61: "🌧️ Light rain", 63: "🌧️ Rain", 65: "🌧️ Heavy rain",
            71: "❄️ Light snow", 73: "❄️ Snow", 75: "❄️ Heavy snow",
            95: "⛈️ Thunderstorm"
        }
        condition = codes.get(current.get("weather_code", 0), "🌡️")
        
        return (
            f"{condition} in {city_name}, {country}\n"
            f"🌡️ Now: {current['temperature_2m']}°C\n"
            f"💧 Humidity: {current['relative_humidity_2m']}%\n"
            f"💨 Wind: {current['wind_speed_10m']} km/h\n"
            f"📈 Today: High {daily['temperature_2m_max'][0]}° / Low {daily['temperature_2m_min'][0]}°"
        )
        
    except Exception as e:
        return f"Weather error: {str(e)[:100]}"


# ─── News (HackerNews, free) ───────────────────────────

@tool
def get_news(topic: str = "technology") -> str:
    """
    Get top news stories. Uses HackerNews API (free, no key).
    Args:
        topic: Filter topic (technology, science, general)
    """
    try:
        # Get top story IDs
        top_ids = requests.get(
            "https://hacker-news.firebaseio.com/v0/topstories.json",
            timeout=10
        ).json()[:5]
        
        stories = []
        for story_id in top_ids:
            story = requests.get(
                f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json",
                timeout=10
            ).json()
            title = story.get("title", "No title")
            score = story.get("score", 0)
            url = story.get("url", f"https://news.ycombinator.com/item?id={story_id}")
            stories.append(f"• {title} ({score}👍)")
        
        return "📰 Hacker News Top Stories:\n" + "\n".join(stories)
        
    except Exception as e:
        return f"News error: {str(e)[:100]}"


# ─── Crypto (CoinGecko, free) ──────────────────────────

@tool
def get_crypto_price(coin: str = "bitcoin") -> str:
    """
    Get cryptocurrency price. Uses CoinGecko (free, no key).
    Args:
        coin: bitcoin, ethereum, solana, cardano, ripple, dogecoin
    """
    try:
        coin = coin.lower().replace(" ", "-")
        data = requests.get(
            f"https://api.coingecko.com/api/v3/simple/price"
            f"?ids={coin}&vs_currencies=usd&include_24hr_change=true",
            timeout=10
        ).json()
        
        if coin not in data:
            return f"Coin '{coin}' not found. Try: bitcoin, ethereum, solana, cardano, dogecoin."
        
        price = data[coin]["usd"]
        change = data[coin].get("usd_24h_change", 0)
        arrow = "📈" if change > 0 else "📉"
        
        return f"💰 {coin.title()}: ${price:,.2f} USD {arrow} {change:+.2f}% (24h)"
        
    except Exception as e:
        return f"Crypto error: {str(e)[:100]}"


# ─── Translation (LibreTranslate, free) ────────────────

@tool
def translate_text(text: str, target_language: str = "Spanish") -> str:
    """
    Translate text to another language. Uses LibreTranslate (free).
    Args:
        text: Text to translate
        target_language: Spanish, French, German, Italian, Portuguese, Chinese, Japanese, Hindi
    """
    try:
        lang_map = {
            "spanish": "es", "french": "fr", "german": "de",
            "italian": "it", "portuguese": "pt", "chinese": "zh",
            "japanese": "ja", "korean": "ko", "hindi": "hi",
            "arabic": "ar", "russian": "ru", "dutch": "nl"
        }
        target = lang_map.get(target_language.lower(), "es")
        
        r = requests.post(
            "https://libretranslate.de/translate",
            data={"q": text, "source": "auto", "target": target, "format": "text"},
            timeout=15
        ).json()
        
        translated = r.get("translatedText", "Translation failed")
        return f"🌐 {target_language}: {translated}"
        
    except Exception as e:
        return f"Translation error: {str(e)[:100]}"


# ─── Joke (free API) ───────────────────────────────────

@tool
def get_joke() -> str:
    """Get a random joke."""
    try:
        r = requests.get("https://official-joke-api.appspot.com/random_joke", timeout=10).json()
        return f"😄 {r['setup']}\n\n{r['punchline']}"
    except:
        return "Why did the programmer quit? Because he didn't get arrays. 😄"


# ─── Mock Actions (Demo placeholders) ──────────────────

@tool
def send_email(to: str, subject: str, body: str) -> str:
    """
    Send an email using your logged-in Gmail via Safari.
    Args:
        to: Email address
        subject: Email subject
        body: Email body
    """
    import urllib.parse
    import subprocess
    
    # URL encode the fields
    safe_to = urllib.parse.quote(to)
    safe_sub = urllib.parse.quote(subject)
    safe_body = urllib.parse.quote(body)
    
    url = f"https://mail.google.com/mail/?view=cm&fs=1&to={safe_to}&su={safe_sub}&body={safe_body}"
    
    script = f'''
tell application "Safari"
    activate
    make new document with properties {{URL:"{url}"}}
    delay 6
    tell application "System Events"
        -- Press Cmd+Return to send
        key code 36 using command down
    end tell
end tell
'''
    try:
        result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True, timeout=15)
        if result.returncode == 0:
            return f"📧 Email composed and sent to {to} via Safari Gmail."
        else:
            return f"❌ Failed to send email: {result.stderr}"
    except Exception as e:
        return f"❌ Email error: {str(e)}"


@tool
def create_reminder(task: str, time: str) -> str:
    """
    Create a reminder (demo mode).
    Args:
        task: What to remind about
        time: When (e.g., "tomorrow 9am", "in 30 minutes")
    """
    return f"⏰ Reminder set: '{task}' at {time}\n(Production: Apple Reminders / Google Calendar API)"


@tool
def book_flight(origin: str, destination: str, date: str) -> str:
    """
    Search flight prices (demo mode).
    Args:
        origin: Departure city
        destination: Arrival city
        date: Travel date
    """
    return (
        f"✈️ Flight Search: {origin} → {destination} on {date}\n"
        f"Estimated: $299-$450\n"
        f"(Production: Amadeus/Skyscanner API)"
    )
