import time
import subprocess
import threading
from quickclip_core.config import OS
from quickclip_core.storage import add_clip
from quickclip_core.viewer import generate_viewer

# Cache the working Linux command to avoid repeated shell execution failures
_linux_clipboard_cmd = None

def get_clipboard_text() -> str:
    """Read plain-text from the system clipboard, cross-platform."""
    global _linux_clipboard_cmd
    if OS == "Windows":
        try:
            import pyperclip
            return pyperclip.paste() or ""
        except Exception:
            pass

    if OS == "Linux":
        if _linux_clipboard_cmd is not None:
            try:
                res = subprocess.run(_linux_clipboard_cmd, capture_output=True, text=True, check=True)
                return res.stdout or ""
            except subprocess.SubprocessError:
                return ""

        for cmd in (
            ["wl-paste", "-n"],
            ["xclip", "-selection", "clipboard", "-o"],
            ["xsel", "--clipboard", "--output"],
        ):
            try:
                res = subprocess.run(cmd, capture_output=True, text=True, check=True)
                _linux_clipboard_cmd = cmd
                return res.stdout or ""
            except (subprocess.SubprocessError, FileNotFoundError):
                pass

    # Generic / macOS fallback
    try:
        import pyperclip
        return pyperclip.paste() or ""
    except Exception as e:
        print(f"⚠️ Clipboard read error: {e}")
        if OS == "Linux":
            print("💡 Install xclip or wl-clipboard:")
            print("   Debian/Ubuntu: sudo apt install xclip wl-clipboard")
        return ""

# Module-level tracking for the last checked clipboard text
_last_text = ""
_last_text_lock = threading.Lock()

def check_now():
    """Immediately check system clipboard for text content and save if new."""
    global _last_text
    try:
        current = get_clipboard_text()
        if current and current.strip():
            with _last_text_lock:
                if current != _last_text:
                    _last_text = current
                    if add_clip(current):
                        generate_viewer()
                        print(f"  ✅ Clipboard: {current[:60].replace(chr(10),' ')}...")
    except Exception:
        pass

def clipboard_monitor():
    """Background thread: polls clipboard for text periodically (5s on Linux fallback, 0.5s on Windows)."""
    global _last_text
    try:
        _last_text = get_clipboard_text()
    except Exception:
        _last_text = ""

    poll_interval = 5.0 if OS == "Linux" else 0.5

    while True:
        try:
            time.sleep(poll_interval)
            check_now()
        except Exception:
            pass
