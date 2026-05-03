# tools/selenium_tools.py — Safari Browser via AppleScript (Reliable + Uses Your Profile)
import os
import time
import subprocess
from langchain_core.tools import tool


def _run_applescript(script: str) -> str:
    """Run an AppleScript and return output."""
    try:
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            return result.stdout.strip()
        else:
            # Return stderr as context but don't raise
            return f"AS_ERR:{result.stderr.strip()[:200]}"
    except subprocess.TimeoutExpired:
        return "AS_ERR:Timeout"
    except Exception as e:
        return f"AS_ERR:{str(e)[:100]}"


def _safari_open_url(url: str) -> str:
    """Open a URL in Safari (opens Safari if not running)."""
    script = f'''
tell application "Safari"
    activate
    if (count of windows) = 0 then
        make new document with properties {{URL:"{url}"}}
    else
        set URL of current tab of front window to "{url}"
    end if
    delay 3
    return URL of current tab of front window
end tell
'''
    return _run_applescript(script)


def _safari_get_text() -> str:
    """Get visible text from the current Safari page."""
    script = '''
tell application "Safari"
    try
        set pageText to (do JavaScript "document.body.innerText" in current tab of front window)
        return pageText
    on error
        return "Could not read page text"
    end try
end tell
'''
    return _run_applescript(script)


def _safari_get_url() -> str:
    """Get current URL from Safari."""
    script = '''
tell application "Safari"
    return URL of current tab of front window
end tell
'''
    return _run_applescript(script)


def _safari_get_title() -> str:
    """Get page title from Safari."""
    script = '''
tell application "Safari"
    return name of current tab of front window
end tell
'''
    return _run_applescript(script)


# ─── Tool Definitions ──────────────────────────────────

@tool
def browser_go(url: str) -> str:
    """
    Open a URL in Safari (uses your real Safari with logins).
    Args:
        url: Full URL like https://youtube.com
    """
    try:
        result = _safari_open_url(url)
        time.sleep(2)
        title = _safari_get_title()
        return f"Safari: {url} | Title: {title}"
    except Exception as e:
        return f"Safari navigation failed: {str(e)[:100]}"


@tool
def browser_search(query: str, engine: str = "google") -> str:
    """
    Search using Safari browser.
    Args:
        query: Search terms
        engine: google or youtube
    """
    try:
        if engine.lower() == "youtube":
            url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"
        else:
            url = f"https://www.google.com/search?q={query.replace(' ', '+')}"

        _safari_open_url(url)
        time.sleep(3)

        # Extract result titles via JavaScript
        if engine.lower() == "youtube":
            script = '''
tell application "Safari"
    try
        set titles to (do JavaScript "
            var els = document.querySelectorAll('#video-title, ytd-video-renderer #video-title');
            var results = [];
            for (var i = 0; i < Math.min(els.length, 5); i++) {
                if (els[i].innerText.trim()) results.push('• ' + els[i].innerText.trim());
            }
            results.join('\\n');
        " in current tab of front window)
        return titles
    on error
        return ""
    end try
end tell
'''
            result = _run_applescript(script)
            if result and not result.startswith("AS_ERR"):
                return f"YouTube results for '{query}':\n{result}"
            return f"YouTube search loaded for '{query}'"
        else:
            script = '''
tell application "Safari"
    try
        set titles to (do JavaScript "
            var els = document.querySelectorAll('h3');
            var results = [];
            for (var i = 0; i < Math.min(els.length, 5); i++) {
                if (els[i].innerText.trim()) results.push((i+1) + '. ' + els[i].innerText.trim());
            }
            results.join('\\n');
        " in current tab of front window)
        return titles
    on error
        return ""
    end try
end tell
'''
            result = _run_applescript(script)
            if result and not result.startswith("AS_ERR"):
                return f"Google results for '{query}':\n{result}"
            return f"Google search loaded for '{query}'"

    except Exception as e:
        return f"Search failed: {str(e)[:100]}"


@tool
def browser_click(text: str) -> str:
    """
    Click an element by its visible text using JavaScript in Safari.
    Args:
        text: Visible text to click
    """
    safe_text = text.replace("'", "\\'").replace('"', '\\"')
    script = f'''
tell application "Safari"
    try
        do JavaScript "
            function clickByText(txt) {{
                var elements = document.querySelectorAll('a, button, [role=button], [role=link]');
                for (var el of elements) {{
                    if (el.innerText && el.innerText.toLowerCase().includes(txt.toLowerCase())) {{
                        el.click();
                        return 'clicked: ' + el.innerText.trim().substring(0, 60);
                    }}
                }}
                var all = document.querySelectorAll('*');
                for (var el of all) {{
                    if (el.childElementCount === 0 && el.innerText && el.innerText.toLowerCase().includes(txt.toLowerCase())) {{
                        el.click();
                        return 'clicked: ' + el.innerText.trim().substring(0, 60);
                    }}
                }}
                return 'not_found';
            }}
            clickByText('{safe_text}');
        " in current tab of front window
    on error errMsg
        return "error: " & errMsg
    end try
end tell
'''
    result = _run_applescript(script)
    time.sleep(2)
    title = _safari_get_title()

    if result and "not_found" not in str(result) and not str(result).startswith("AS_ERR"):
        return f"Clicked '{text}'. Now: {title}"
    return f"Could not find '{text}' to click on the page"


@tool
def browser_type(selector: str, text: str) -> str:
    """
    Type text into a form field in Safari.
    Args:
        selector: Field name, placeholder, or ID
        text: Text to type
    """
    safe_text = text.replace("'", "\\'").replace('"', '\\"')
    safe_sel = selector.replace("'", "\\'")
    script = f'''
tell application "Safari"
    try
        do JavaScript "
            var el = document.querySelector('input[name*=\"{safe_sel}\"], input[id*=\"{safe_sel}\"], input[placeholder*=\"{safe_sel}\"], textarea[name*=\"{safe_sel}\"]');
            if (!el) el = document.querySelector('input[name=\"search_query\"], input[type=\"search\"]');
            if (el) {{
                el.focus();
                el.value = '{safe_text}';
                el.dispatchEvent(new Event('input', {{bubbles: true}}));
                el.dispatchEvent(new Event('change', {{bubbles: true}}));
                'typed';
            }} else {{
                'not_found';
            }}
        " in current tab of front window
    on error errMsg
        return "error: " & errMsg
    end try
end tell
'''
    result = _run_applescript(script)
    if result and "not_found" not in str(result) and not str(result).startswith("AS_ERR"):
        return f"Typed '{text}' into '{selector}'"
    return f"Field '{selector}' not found"


@tool
def browser_press(key: str) -> str:
    """
    Press a keyboard key in Safari (uses System Events).
    Args:
        key: Enter, Escape, Tab, Space
    """
    # Key codes for System Events
    key_codes = {"enter": 36, "return": 36, "escape": 53, "tab": 48, "space": 49}
    code = key_codes.get(key.lower(), 36)
    script = f"""tell application "Safari" to activate
delay 0.2
tell application "System Events"
    key code {code}
end tell"""
    _run_applescript(script)
    time.sleep(1)
    return f"Pressed {key}"


@tool
def browser_read() -> str:
    """Read visible text from the current Safari page."""
    try:
        title = _safari_get_title()
        text = _safari_get_text()

        if text.startswith("AS_ERR"):
            return f"Page ({title}): Could not read text"

        lines = [l.strip() for l in text.split('\n') if l.strip()]
        text = '\n'.join(lines)

        if len(text) > 3000:
            text = text[:3000] + "\n..."

        return f"Page ({title}):\n\n{text}"
    except Exception as e:
        return f"Read failed: {str(e)[:100]}"


@tool
def browser_screenshot(path: str = "~/Desktop/boss_safari.png") -> str:
    """Take a screenshot of the current Safari window."""
    try:
        path = os.path.expanduser(path)
        # Use screencapture to capture the Safari window
        script = '''
tell application "Safari" to activate
delay 0.5
'''
        _run_applescript(script)
        subprocess.run(
            ["screencapture", "-l", "$(osascript -e 'tell application \"Safari\" to id of front window')", path],
            shell=False, capture_output=True
        )
        # Simpler: capture whole screen
        subprocess.run(["screencapture", "-x", path], capture_output=True, timeout=10)
        if os.path.exists(path):
            return f"Screenshot: {path}"
        return "Screenshot failed"
    except Exception as e:
        return f"Screenshot failed: {str(e)[:100]}"


@tool
def browser_close() -> str:
    """Close Safari browser."""
    script = 'tell application "Safari" to quit'
    _run_applescript(script)
    return "Safari closed"


@tool
def browser_get_url() -> str:
    """Get the current URL from Safari."""
    url = _safari_get_url()
    if url.startswith("AS_ERR"):
        return "Safari not open or no URL"
    return url
