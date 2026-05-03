# tools/web_tools.py — Safari AppleScript (Working)
import subprocess
import time
from langchain_core.tools import tool


def _osascript(script: str) -> str:
    try:
        r = subprocess.run(["osascript", "-e", script], capture_output=True, text=True, timeout=15)
        if r.returncode != 0:
            err = r.stderr.strip()
            if "not running" in err or "Can't get" in err:
                subprocess.run(["open", "-a", "Safari"], timeout=5)
                time.sleep(2)
                r = subprocess.run(["osascript", "-e", script], capture_output=True, text=True, timeout=15)
            if r.returncode != 0:
                return f"Error: {r.stderr.strip()[:80]}"
        return r.stdout.strip()
    except Exception as e:
        return f"Error: {str(e)[:80]}"


@tool
def navigate_to_url(url: str) -> str:
    """Navigate Safari to a URL."""
    _osascript('tell application "Safari" to activate')
    time.sleep(0.5)
    _osascript(f'tell application "Safari" to set URL of front document to "{url}"')
    time.sleep(3)
    title = _osascript('tell application "Safari" to return name of front document')
    return f"Safari: {url} | {title}"


@tool
def type_on_page(selector: str, text: str) -> str:
    """Type text into an input field by placeholder or name."""
    safe_text = text.replace('"', '\\"')
    script = f'''
    tell application "Safari" to tell front document to do JavaScript "
        var inputs = document.querySelectorAll('input, textarea');
        var target = null;
        for (var i=0; i<inputs.length; i++) {{
            var nm = inputs[i].name || '';
            var id = inputs[i].id || '';
            var ph = inputs[i].placeholder || '';
            if (nm=='search_query' || id=='search' || ph.toLowerCase().includes('search') || inputs[i].getAttribute('aria-label')?.includes('Search')) {{
                target = inputs[i]; break;
            }}
        }}
        if (!target) target = document.querySelector('input[name=\\\"search_query\\\"]') || document.querySelector('input#search') || document.querySelector('input[placeholder*=\\\"Search\\\"]');
        if (target) {{
            target.focus();
            target.value = '{safe_text}';
            target.dispatchEvent(new Event('input', {{bubbles:true}}));
            // Trigger React onChange
            var tracker = target._valueTracker;
            if (tracker) tracker.setValue('');
            target.dispatchEvent(new Event('change', {{bubbles:true}}));
            return 'Typed: ' + target.value;
        }}
        return 'Field not found';
    "
    '''
    return _osascript(script)


@tool
def press_key(key: str) -> str:
    """Press a key in Safari (Enter, Escape, Space, Tab, etc)."""
    key_lower = key.lower()
    # Use JavaScript keydown for web forms instead of System Events
    if key_lower in ["return", "enter"]:
        script = '''
        tell application "Safari" to tell front document to do JavaScript "
            // YouTube specific
            if (location.hostname.includes('youtube.com')) {
                var btn = document.querySelector('#search-icon-legacy');
                if (btn) {
                    btn.click();
                    return 'Clicked YouTube search button';
                }
            }
            
            var active = document.activeElement;
            if (active) {
                active.dispatchEvent(new KeyboardEvent('keydown', {key:'Enter', keyCode:13, bubbles:true}));
                active.dispatchEvent(new KeyboardEvent('keyup', {key:'Enter', keyCode:13, bubbles:true}));
                var form = active.closest('form');
                if (form) {
                    form.dispatchEvent(new Event('submit', {bubbles:true}));
                    return 'Submitted form';
                }
                return 'Pressed Enter on: ' + (active.name || active.id || 'element');
            }
            document.dispatchEvent(new KeyboardEvent('keydown', {key:'Enter', keyCode:13, bubbles:true}));
            return 'Pressed Enter (global)';
        "
        '''
        r = _osascript(script)
        time.sleep(2)
        return r
    
    # Fallback to System Events for non-Enter keys
    code_map = {"escape": 53, "space": 49, "tab": 48}
    code = code_map.get(key_lower, 36)
    _osascript(f'tell application "Safari" to activate\ntell application "System Events" to key code {code}')
    time.sleep(1)
    return f"Pressed {key}"


@tool
def click_on_page(text: str) -> str:
    """Click element by text. For YouTube, uses video-specific selectors."""
    safe = text.replace('"', '\\"')[:30]
    script = f'''
    tell application "Safari" to tell front document to do JavaScript "
        // YouTube-specific first
        if (location.hostname.includes('youtube.com')) {{
            // Click first video thumbnail
            var thumbs = document.querySelectorAll('ytd-video-renderer a#thumbnail, ytd-grid-video-renderer a#thumbnail, a.ytd-thumbnail');
            if (thumbs.length > 0) {{
                thumbs[0].click();
                return 'YT-Thumb';
            }}
            // Click video title
            var titles = document.querySelectorAll('ytd-video-renderer #video-title, a#video-title');
            if (titles.length > 0) {{
                titles[0].click();
                return 'YT-Title: ' + titles[0].innerText.substring(0,30);
            }}
        }}
        
        // Generic fallback
        var els = document.querySelectorAll('*');
        for (var i=0; i<els.length; i++) {{
            if (els[i].innerText && els[i].innerText.includes('{safe}')) {{
                els[i].click();
                return 'Clicked: ' + els[i].innerText.substring(0,30);
            }}
        }}
        return 'Not found';
    "
    '''
    r = _osascript(script)
    time.sleep(3)
    return r


@tool
def search_google(query: str) -> str:
    """Search Google in Safari."""
    q = query.replace(" ", "+")
    navigate_to_url.invoke({"url": f"https://google.com/search?q={q}"})
    time.sleep(3)
    return f"Searched Google for '{query}'"


@tool
def read_page_text() -> str:
    """Read visible text from the current Safari page."""
    text = _osascript('tell application "Safari" to tell front document to do JavaScript "document.body.innerText"')
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    text = '\n'.join(lines)
    if len(text) > 3000:
        text = text[:3000] + "\n..."
    title = _osascript('tell application "Safari" to return name of front document')
    return f"Safari ({title}):\n{text}"


@tool
def take_browser_screenshot(save_path: str = "~/Desktop/boss_safari.png") -> str:
    """Take a screenshot of the Safari window."""
    import os
    path = os.path.expanduser(save_path)
    subprocess.run(["screencapture", "-w", path], timeout=10)
    return f"Screenshot: {path}"


@tool
def close_browser() -> str:
    """Close the front Safari tab."""
    _osascript('tell application "Safari" to close front document')
    return "Closed tab"

@tool
def get_current_url() -> str:
    """Get the URL of the current Safari tab."""
    return _osascript('tell application "Safari" to return URL of front document')
