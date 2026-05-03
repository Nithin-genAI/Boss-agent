# tools/visual_tools.py — Visual & App Control for Boss
import os
import subprocess
import platform
from langchain_core.tools import tool


@tool
def take_screenshot(save_path: str = "~/Desktop/boss_screenshot.png") -> str:
    """
    Capture the screen and save it. Returns the file path.
    Use this to 'see' what's currently on screen.
    Args:
        save_path: Where to save the screenshot
    """
    try:
        save_path = os.path.expanduser(save_path)
        
        if platform.system() == "Darwin":  # macOS
            subprocess.run(["screencapture", save_path], check=True, timeout=10)
        elif platform.system() == "Linux":
            subprocess.run(["gnome-screenshot", "-f", save_path], check=True, timeout=10)
        else:
            return "Screenshot not supported on this OS."
        
        size = os.path.getsize(save_path)
        return f"Screenshot saved: {save_path} ({size:,} bytes). Boss can now 'see' the screen."
    except Exception as e:
        return f"Screenshot failed: {str(e)}"


@tool
def open_application(app_name: str) -> str:
    """
    Open an application by name. Works on macOS.
    Args:
        app_name: App name like 'Safari', 'Visual Studio Code', 'Calculator', 'Notes'
    """
    try:
        if platform.system() == "Darwin":
            subprocess.run(["open", "-a", app_name], check=True, timeout=10)
            return f"Opened {app_name} successfully."
        else:
            return f"Opening apps not yet implemented for {platform.system()}"
    except subprocess.CalledProcessError:
        return f"Could not open '{app_name}'. Check the exact app name (e.g., 'Visual Studio Code' not 'vscode')."
    except Exception as e:
        return f"Error: {str(e)}"


@tool
def open_folder(folder_path: str) -> str:
    """
    Open a folder in Finder/File Explorer.
    Args:
        folder_path: Path like '~/Desktop', '~/Downloads', '/Users/ramesh/Boss-agent'
    """
    try:
        folder_path = os.path.expanduser(folder_path)
        if not os.path.exists(folder_path):
            return f"Folder not found: {folder_path}"
        
        if platform.system() == "Darwin":
            subprocess.run(["open", folder_path], check=True, timeout=10)
            return f"Opened folder: {folder_path}"
        else:
            return f"Folder open not yet implemented for {platform.system()}"
    except Exception as e:
        return f"Error: {str(e)}"
