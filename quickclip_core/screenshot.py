import time
import threading
import hashlib
from pathlib import Path
from datetime import datetime
from quickclip_core.config import OS, SCREENSHOT_EXTENSIONS, SCREENSHOT_WATCH_DIRS, SHOTS_DIR
from quickclip_core.storage import add_screenshot, sync_shots_dir
from quickclip_core.viewer import generate_viewer

def _handle_new_file(path: Path):
    """Called whenever a new file appears in a watched directory."""
    if path.suffix.lower() not in SCREENSHOT_EXTENSIONS:
        return

    if add_screenshot(path):
        generate_viewer()
        print(f"  📸 Screenshot saved: {path.name}")

def start_screenshot_monitor_watchdog():
    """
    Use the `watchdog` library to efficiently watch filesystem events.
    This avoids polling and keeps CPU usage very low.
    """
    try:
        from watchdog.observers import Observer
        from watchdog.events import FileSystemEventHandler

        class _ScreenshotHandler(FileSystemEventHandler):
            def on_created(self, event):
                if not event.is_directory:
                    _handle_new_file(Path(event.src_path))

            def on_moved(self, event):
                # Some tools write to a temp file then rename (move) it
                if not event.is_directory:
                    _handle_new_file(Path(event.dest_path))

        observer = Observer()
        for watch_dir in SCREENSHOT_WATCH_DIRS:
            observer.schedule(_ScreenshotHandler(), str(watch_dir), recursive=False)
            print(f"  👁️  Watching: {watch_dir}")

        observer.start()
        return observer   # caller keeps reference so it isn't GC'd

    except ImportError:
        print("  ⚠️ watchdog not installed — falling back to polling screenshot monitor.")
        print("     Install with: pip3 install watchdog --break-system-packages")
        return None

def start_screenshot_monitor_polling():
    """
    Fallback: scan watched directories every 2 s for new image files.
    Slightly higher CPU cost than watchdog but requires no extra library.
    """
    known: set[str] = set()

    # Seed with files already present so we don't re-import old screenshots
    for d in SCREENSHOT_WATCH_DIRS:
        for f in d.iterdir():
            if f.suffix.lower() in SCREENSHOT_EXTENSIONS:
                known.add(str(f))

    def _poll():
        while True:
            time.sleep(2)
            for d in SCREENSHOT_WATCH_DIRS:
                try:
                    for f in d.iterdir():
                        key = str(f)
                        if key not in known and f.suffix.lower() in SCREENSHOT_EXTENSIONS:
                            known.add(key)
                            _handle_new_file(f)
                except Exception:
                    pass

    t = threading.Thread(target=_poll, daemon=True)
    t.start()
    return t

def screenshot_monitor():
    """
    Start screenshot monitoring using watchdog if available, else polling.
    macOS/Linux may also get screenshots via clipboard image polling (Pillow needed).
    """
    # On startup: import any screenshots already in SHOTS_DIR that aren't in the JSON yet
    if sync_shots_dir() > 0:
        generate_viewer()

    observer = start_screenshot_monitor_watchdog()

    # On macOS and Linux, some screenshot tools (e.g. Flameshot, macOS Cmd+Ctrl+Shift+4)
    # put the image directly onto the clipboard without saving a file.
    # We handle that by polling the clipboard for image data.
    if OS in ("Darwin", "Linux"):
        _start_clipboard_image_monitor()

    if observer is None:
        # watchdog unavailable — use polling thread
        start_screenshot_monitor_polling()
    # else watchdog is running in its own thread

# Module-level variables to track the last checked clipboard image hash
_last_image_hash = ""
_last_image_lock = threading.Lock()

def check_now():
    """Immediately check system clipboard for image content and save if new."""
    global _last_image_hash
    if OS not in ("Darwin", "Linux"):
        return
    try:
        from PIL import ImageGrab
        img = ImageGrab.grabclipboard()
        if img is None:
            return
        # Convert to bytes to hash
        import io
        buf = io.BytesIO()
        img.convert("RGB").save(buf, format="PNG")
        raw = buf.getvalue()
        h = hashlib.md5(raw).hexdigest()
        
        with _last_image_lock:
            if h == _last_image_hash:
                return
            _last_image_hash = h
            
        # Save to screenshots dir
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        dest = SHOTS_DIR / f"clipboard_{ts}.png"
        dest.write_bytes(raw)
        if add_screenshot(dest):
            generate_viewer()
            print(f"  📸 Clipboard image saved: {dest.name}")
    except ImportError:
        pass
    except Exception:
        pass

def _start_clipboard_image_monitor():
    """
    Poll the clipboard for image data (macOS / Linux).
    If an image is found, save it as a PNG into SHOTS_DIR.
    Requires Pillow (PIL) to grab the image.
    """
    def _poll():
        poll_interval = 5.0 if OS == "Linux" else 1.0
        while True:
            time.sleep(poll_interval)
            try:
                check_now()
            except ImportError:
                break   # Pillow not installed — silently stop
            except Exception:
                pass

    t = threading.Thread(target=_poll, daemon=True)
    t.start()
