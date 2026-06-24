#!/usr/bin/env python3
# run: python3 ~/Downloads/QuickClip/quickclip.py
# run: python3 ~/Downloads/quickclip.py
# python %USERPROFILE%\Downloads\quickclip.py
# http://localhost:8080/viewer.html

# QuickClip — Clipboard + Screenshot Monitor
# Monitors clipboard text AND system screenshots, saves both to a live HTML dashboard.

import sys
from quickclip_core.viewer import generate_viewer
from quickclip_core.listener import start_listener

# ── Ensure UTF-8 console output (needed for emoji on Windows) ──────────────────
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

if __name__ == "__main__":
    generate_viewer()
    try:
        start_listener()
    except KeyboardInterrupt:
        print("\n 👋")
    except ImportError:
        print("ERROR: pip install -r requirements.txt")