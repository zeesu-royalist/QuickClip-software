import threading
import requests
import json
import os
from quickclip_core.config import WEBHOOK_URL

def get_username() -> str:
    try:
        return os.getlogin()
    except Exception:
        import getpass
        try:
            return getpass.getuser()
        except Exception:
            return "Unknown User"

def send_to_webhook(data_type: str, content: str, timestamp: str, filename: str = ""):
    """
    Sends data to the configured Google Apps Script Webhook asynchronously.
    `data_type`: "text" or "image"
    `content`: For text, the text. For image, base64 encoded image data.
    `filename`: The original filename for images (optional).
    """
    if not WEBHOOK_URL:
        return
        
    def _send():
        payload = {
            "username": get_username(),
            "type": data_type,
            "content": content,
            "timestamp": timestamp,
            "filename": filename
        }
        try:
            # We use a short timeout so we don't hold resources forever
            res = requests.post(WEBHOOK_URL, json=payload, timeout=10)
            print(f"  🌐 Webhook Response: {res.status_code} {res.text}")
        except Exception as e:
            print(f"⚠️ Webhook Error: {e}")

    t = threading.Thread(target=_send, daemon=True)
    t.start()
