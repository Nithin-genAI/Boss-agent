# tools/system_tools.py — Powerful System Tools for Boss
import os
import subprocess
import glob
import platform
from datetime import datetime
from langchain_core.tools import tool


# ─── Context Tools ─────────────────────────────────────

@tool
def get_system_info() -> str:
    """Get system context: OS, current user, home directory, working directory."""
    return f"""OS: {platform.system()} {platform.release()}
User: {os.getenv('USER', 'unknown')}
Home: {os.path.expanduser('~')}
CWD: {os.getcwd()}
Python: {platform.python_version()}"""


@tool
def get_current_time() -> str:
    """Get the current date and time."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# ─── File Discovery Tools ──────────────────────────────

@tool
def find_file(filename: str, search_path: str = ".") -> str:
    """
    Search for a file by name across the system. Use this when you don't know the exact path.
    Args:
        filename: Name of file to find (e.g., main.py, README.md). Supports wildcards like *.py
        search_path: Where to start searching (default: current dir '.'). Use '~' for home directory.
    """
    try:
        search_path = os.path.expanduser(search_path)
        if not os.path.exists(search_path):
            return f"Search path not found: {search_path}"
        
        matches = []
        for root, dirs, files in os.walk(search_path):
            # Skip hidden dirs and node_modules to keep it fast
            dirs[:] = [d for d in dirs if not d.startswith('.') and d != 'node_modules']
            
            for f in files:
                if glob.fnmatch.fnmatch(f, filename):
                    matches.append(os.path.join(root, f))
            
            if len(matches) >= 20:
                break
        
        if not matches:
            return f"No files matching '{filename}' found in {search_path}"
        
        result = [f"Found {len(matches)} match(es):"] + matches[:20]
        if len(matches) > 20:
            result.append(f"... and {len(matches) - 20} more")
        return "\n".join(result)
        
    except PermissionError:
        return f"Permission denied searching {search_path}"
    except Exception as e:
        return f"Error searching: {str(e)}"


@tool
def search_file_content(query: str, file_path: str) -> str:
    """
    Search for text inside a specific file. Like grep.
    Args:
        query: Text to search for
        file_path: Absolute path to the file
    """
    try:
        file_path = os.path.expanduser(file_path)
        if not os.path.exists(file_path):
            return f"File not found: {file_path}"
        
        matches = []
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            for i, line in enumerate(f, 1):
                if query.lower() in line.lower():
                    matches.append(f"Line {i}: {line.strip()}")
                    if len(matches) >= 10:
                        matches.append("... (truncated)")
                        break
        
        if not matches:
            return f"'{query}' not found in {os.path.basename(file_path)}"
        
        return f"Matches in {file_path}:\n" + "\n".join(matches)
        
    except Exception as e:
        return f"Error: {str(e)}"


# ─── File Operation Tools ──────────────────────────────

@tool
def read_file(file_path: str) -> str:
    """
    Read the contents of a file. If path is relative, resolves against CWD and home.
    Args:
        file_path: Path to file (e.g., main.py, ~/Desktop/file.txt, /absolute/path)
    """
    try:
        # Try multiple path resolutions
        candidates = [
            file_path,
            os.path.expanduser(file_path),
            os.path.join(os.getcwd(), file_path),
            os.path.join(os.path.expanduser("~"), file_path),
        ]
        
        resolved = None
        for c in candidates:
            if os.path.exists(c) and os.path.isfile(c):
                resolved = c
                break
        
        if not resolved:
            # Try finding it
            home = os.path.expanduser("~")
            for root, dirs, files in os.walk(home):
                dirs[:] = [d for d in dirs if not d.startswith('.') and d != 'node_modules']
                if os.path.basename(file_path) in files:
                    resolved = os.path.join(root, os.path.basename(file_path))
                    break
                if len(root) > len(home) + 100:  # Limit depth
                    break
            
            if not resolved:
                return f"File not found: {file_path} (tried CWD, home, and quick search)"
        
        # Safety block
        blocked = ["/etc/passwd", "/etc/shadow", ".ssh/id_rsa", ".env"]
        if any(b in resolved for b in blocked):
            return "Access denied: sensitive path."
        
        with open(resolved, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        
        # Truncate very large files
        if len(content) > 15000:
            content = content[:15000] + f"\n\n... [truncated, file is {len(content)} chars]"
        
        return f"File: {resolved}\n\n{content}"
        
    except PermissionError:
        return f"Permission denied: {file_path}. Grant access in System Settings."
    except Exception as e:
        return f"Error reading file: {str(e)}"


@tool
def list_directory(dir_path: str = ".") -> str:
    """
    List files and folders. Resolves relative paths against CWD and home.
    Args:
        dir_path: Directory path. Use '.' for current, '~' for home.
    """
    try:
        candidates = [
            dir_path,
            os.path.expanduser(dir_path),
            os.path.join(os.getcwd(), dir_path),
            os.path.join(os.path.expanduser("~"), dir_path),
        ]
        
        resolved = None
        for c in candidates:
            if os.path.exists(c) and os.path.isdir(c):
                resolved = c
                break
        
        if not resolved:
            return f"Directory not found: {dir_path} (tried CWD and home)"
        
        items = os.listdir(resolved)
        result = []
        for item in sorted(items):
            full = os.path.join(resolved, item)
            item_type = "📁" if os.path.isdir(full) else "📄"
            size = ""
            if os.path.isfile(full):
                size_bytes = os.path.getsize(full)
                size = f" ({size_bytes:,} bytes)"
            result.append(f"{item_type} {item}{size}")
        
        header = f"Contents of {resolved} ({len(items)} items):"
        body = "\n".join(result) if result else "(empty directory)"
        return f"{header}\n{body}"
        
    except PermissionError:
        return f"Permission denied: {dir_path}"
    except Exception as e:
        return f"Error: {str(e)}"


@tool
def summarize_directory(dir_path: str, file_pattern: str = "*") -> str:
    """
    Read and summarize all matching files in a directory.
    Args:
        dir_path: Path to directory
        file_pattern: Pattern like *.py, *.md, *.txt
    """
    try:
        candidates = [
            dir_path,
            os.path.expanduser(dir_path),
            os.path.join(os.getcwd(), dir_path),
            os.path.join(os.path.expanduser("~"), dir_path),
        ]
        
        resolved = None
        for c in candidates:
            if os.path.exists(c) and os.path.isdir(c):
                resolved = c
                break
        
        if not resolved:
            return f"Directory not found: {dir_path}"
        
        files = glob.glob(os.path.join(resolved, file_pattern))
        files = [f for f in files if os.path.isfile(f)]
        
        if not files:
            return f"No files matching '{file_pattern}' in {resolved}"
        
        summary = []
        for f in sorted(files)[:15]:
            try:
                with open(f, "r", encoding="utf-8", errors="ignore") as file:
                    content = file.read(1500)
                filename = os.path.basename(f)
                summary.append(f"--- {filename} ---\n{content[:500]}...")
            except Exception as e:
                summary.append(f"--- {os.path.basename(f)} ---\nError: {str(e)}")
        
        return f"Directory: {resolved}\nFiles: {len(files)}\n\n" + "\n\n".join(summary)
        
    except Exception as e:
        return f"Error: {str(e)}"


# ─── Shell Tool (Safer but Useful) ─────────────────────

@tool
def run_shell_command(command: str) -> str:
    """
    Run a shell command.
    Args:
        command: The command string
    """
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=15,
            cwd=os.getcwd()
        )
        output = result.stdout.strip()
        error = result.stderr.strip()
        
        if result.returncode != 0:
            return f"Exit code {result.returncode}:\n{error[:500]}"
        
        if not output:
            return "Done (no output)."
        
        # Truncate very long output
        if len(output) > 8000:
            output = output[:8000] + f"\n... [truncated, {len(output)} chars total]"
        
        return output
        
    except subprocess.TimeoutExpired:
        return "Command timed out after 15 seconds."
    except Exception as e:
        return f"Error: {str(e)}"
