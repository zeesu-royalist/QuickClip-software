import os
import sys
import platform
from pathlib import Path

# ── Ensure UTF-8 console output (needed for emoji on Windows) ──────────────────
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

# ── Project directories ────────────────────────────────────────────────────────
SAVE_DIR        = Path.home() / "QuickClip_Notes"
CLIPS_FILE      = SAVE_DIR / "clips.json"
SHOTS_FILE      = SAVE_DIR / "screenshots.json"   # screenshot metadata store
SHOTS_DIR       = SAVE_DIR / "screenshots"         # local copies of screenshots
CONFIG_FILE     = SAVE_DIR / "config.json"

SAVE_DIR.mkdir(exist_ok=True)
SHOTS_DIR.mkdir(exist_ok=True)

# ── Webhook Configuration ──────────────────────────────────────────────────────
WEBHOOK_URL = ""
if CONFIG_FILE.exists():
    import json
    try:
        _conf = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        WEBHOOK_URL = _conf.get("WEBHOOK_URL", "")
    except Exception:
        pass

OS = platform.system()   # "Windows" | "Linux" | "Darwin"

# ── Screenshot watch folders (per OS) ─────────────────────────────────────────
# These are the default locations where each OS saves screenshots.
def _screenshot_watch_dirs() -> list[Path]:
    """Return OS-appropriate directories to watch for new screenshot files."""
    home = Path.home()
    if OS == "Windows":
        # Check registry for My Pictures (handles OneDrive and other folder redirections)
        pictures_dir = None
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders") as key:
                val, _ = winreg.QueryValueEx(key, "My Pictures")
                pictures_dir = Path(os.path.expandvars(val))
        except Exception:
            pass

        dirs = []
        if pictures_dir:
            dirs.extend([pictures_dir / "Screenshots", pictures_dir])
        
        # Fallback/alternative standard locations
        dirs.extend([
            home / "Pictures" / "Screenshots", 
            home / "Pictures",
            home / "OneDrive" / "Pictures" / "Screenshots",
            home / "OneDrive" / "Pictures"
        ])
        return dirs
    elif OS == "Darwin":
        # macOS default: Desktop (Cmd+Shift+3/4) and Downloads
        return [home / "Desktop", home / "Downloads"]
    else:  # Linux
        return [home / "Pictures", home / "Desktop", home / "Downloads"]

# Resolve to unique existing directories to watch
SCREENSHOT_WATCH_DIRS = []
for d in _screenshot_watch_dirs():
    if d.exists() and d not in SCREENSHOT_WATCH_DIRS:
        SCREENSHOT_WATCH_DIRS.append(d)

# Image file extensions we consider as screenshots
SCREENSHOT_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff"}
