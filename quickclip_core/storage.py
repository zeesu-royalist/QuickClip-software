import json
import hashlib
import shutil
import base64
import time
from datetime import datetime
from pathlib import Path
from quickclip_core.config import CLIPS_FILE, SHOTS_FILE, SHOTS_DIR, SCREENSHOT_EXTENSIONS

# ── Clipboard Text Operations ──────────────────────────────────────────────────

def load_clips() -> list:
    if CLIPS_FILE.exists():
        try:
            return json.loads(CLIPS_FILE.read_text(encoding="utf-8"))
        except Exception:
            return []
    return []

def save_clips(clips: list):
    CLIPS_FILE.write_text(json.dumps(clips, ensure_ascii=False, indent=2), encoding="utf-8")

def add_clip(text: str) -> bool:
    text = text.strip()
    if not text:
        return False
    clips = load_clips()
    if clips and clips[0]["text"] == text:
        return False   # exact duplicate at top — skip
    clips.insert(0, {"text": text, "time": datetime.now().strftime("%d %b %Y, %I:%M %p")})
    save_clips(clips[:500])
    
    # Send to webhook asynchronously
    try:
        from quickclip_core.webhook import send_to_webhook
        send_to_webhook("text", text, datetime.now().strftime("%d %b %Y, %I:%M %p"))
    except Exception:
        pass
        
    return True

# ── Screenshot Storage Operations ──────────────────────────────────────────────

def load_shots() -> list:
    """Load screenshot metadata list from JSON."""
    if SHOTS_FILE.exists():
        try:
            return json.loads(SHOTS_FILE.read_text(encoding="utf-8"))
        except Exception:
            return []
    return []

def save_shots(shots: list):
    SHOTS_FILE.write_text(json.dumps(shots, ensure_ascii=False, indent=2), encoding="utf-8")

def _file_hash(path: Path) -> str:
    """Return an MD5 hex digest of a file (for duplicate detection)."""
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()

def sync_shots_dir() -> int:
    """
    Scan SHOTS_DIR for image files not yet in the JSON and import them.
    Returns the number of newly added entries.
    Useful on startup to pick up screenshots that were saved while the app
    was not running, or that were there before the JSON existed.
    """
    shots = load_shots()
    known_files = {s["filename"] for s in shots}
    added = 0

    # Sort oldest-first so the JSON ends up newest-first after inserting
    existing = sorted(
        [f for f in SHOTS_DIR.iterdir() if f.suffix.lower() in SCREENSHOT_EXTENSIONS],
        key=lambda f: f.stat().st_mtime,
    )

    for img_path in existing:
        if img_path.name in known_files:
            continue  # already tracked
        try:
            file_hash = _file_hash(img_path)
        except Exception:
            continue
        if any(s.get("hash") == file_hash for s in shots):
            continue  # duplicate content

        thumb_b64 = _make_thumbnail_b64(img_path)
        try:
            mtime = img_path.stat().st_mtime
            from datetime import datetime as _dt
            ts = _dt.fromtimestamp(mtime)
        except Exception:
            from datetime import datetime as _dt
            ts = _dt.now()

        shots.insert(0, {
            "filename": img_path.name,
            "original": str(img_path),
            "time": ts.strftime("%d %b %Y, %I:%M %p"),
            "hash": file_hash,
            "thumb_b64": thumb_b64,
        })
        known_files.add(img_path.name)
        added += 1

    if added:
        save_shots(shots[:200])
        print(f"  📂 Synced {added} existing screenshot(s) from folder.")

    return added


def add_screenshot(src_path: Path) -> bool:
    """
    Copy a new screenshot into SHOTS_DIR, record metadata, return True if saved.
    Skips duplicates based on file hash.
    """
    src_path = Path(src_path)
    if not src_path.exists() or src_path.suffix.lower() not in SCREENSHOT_EXTENSIONS:
        return False

    # Wait briefly so the OS finishes writing the file before we read it
    time.sleep(0.4)

    try:
        file_hash = _file_hash(src_path)
    except Exception:
        return False

    shots = load_shots()

    # Duplicate check: same hash already recorded?
    if any(s.get("hash") == file_hash for s in shots):
        return False

    # Copy file to our managed screenshots folder
    timestamp = datetime.now()
    dest_name = f"{timestamp.strftime('%Y%m%d_%H%M%S')}_{src_path.name}"
    dest_path = SHOTS_DIR / dest_name
    try:
        shutil.copy2(src_path, dest_path)
    except Exception as e:
        print(f"  ⚠️ Screenshot copy failed: {e}")
        return False

    # Build a small base64 thumbnail (max 300 px wide) for the HTML preview
    thumb_b64 = _make_thumbnail_b64(dest_path)

    shots.insert(0, {
        "filename": dest_name,
        "original": str(src_path),
        "time": timestamp.strftime("%d %b %Y, %I:%M %p"),
        "hash": file_hash,
        "thumb_b64": thumb_b64,   # inline data-URI thumbnail
    })
    save_shots(shots[:200])   # keep at most 200 screenshots
    
    # Send to webhook asynchronously with full image
    try:
        with open(dest_path, "rb") as f:
            img_data = f.read()
        mime = "image/png" if dest_path.suffix.lower() == ".png" else "image/jpeg"
        full_b64 = f"data:{mime};base64," + base64.b64encode(img_data).decode()
        from quickclip_core.webhook import send_to_webhook
        send_to_webhook("image", full_b64, timestamp.strftime("%d %b %Y, %I:%M %p"), dest_name)
    except Exception:
        pass
        
    return True

def _make_thumbnail_b64(img_path: Path, max_width: int = 300) -> str:
    """
    Return a base64 PNG data-URI for a resized thumbnail, or "" on failure.
    Uses Pillow if available, otherwise falls back to raw base64 of the original.
    """
    try:
        from PIL import Image
        with Image.open(img_path) as im:
            # Convert to RGB so we can always save as JPEG (handles RGBA PNGs)
            im = im.convert("RGB")
            ratio = max_width / max(im.width, 1)
            if ratio < 1:
                new_size = (int(im.width * ratio), int(im.height * ratio))
                im = im.resize(new_size, Image.LANCZOS)
            import io
            buf = io.BytesIO()
            im.save(buf, format="JPEG", quality=75)
            return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()
    except ImportError:
        # Pillow not installed — embed the raw file as-is (larger but works)
        try:
            raw = img_path.read_bytes()
            mime = "image/png" if img_path.suffix.lower() == ".png" else "image/jpeg"
            return f"data:{mime};base64," + base64.b64encode(raw).decode()
        except Exception:
            return ""
    except Exception:
        return ""
