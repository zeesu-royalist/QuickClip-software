#!/usr/bin/env python3
"""Global keyboard tracker that prints pressed keys to the terminal.

Requires pynput, which is already listed in requirements.txt.
Run:
    python3 global_key_tracker.py

Press ESC to exit.
"""

import os
import time
from pynput import keyboard

currently_pressed = set()

def trigger_screenshot():
    save_dir = os.path.expanduser("~/QuickClip_Screenshots")
    os.makedirs(save_dir, exist_ok=True)
    ts = time.strftime("%Y%m%d_%H%M%S")
    output_path = os.path.join(save_dir, f"screenshot_{ts}.png")
    
    print("\n[CMD+I Detected] Capturing active window...")
    
    bounds = None
    try:
        from AppKit import NSWorkspace
        from Quartz import CGWindowListCopyWindowInfo, kCGWindowListOptionOnScreenOnly, kCGNullWindowID
        
        active_app = NSWorkspace.sharedWorkspace().frontmostApplication()
        if active_app:
            app_pid = active_app.processIdentifier()
            options = kCGWindowListOptionOnScreenOnly
            window_list = CGWindowListCopyWindowInfo(options, kCGNullWindowID)
            for window in window_list:
                if window.get('kCGWindowOwnerPID') == app_pid:
                    if window.get('kCGWindowLayer', 0) == 0:
                        b = window.get('kCGWindowBounds')
                        if b:
                            x = int(b.get('X', 0))
                            y = int(b.get('Y', 0))
                            w = int(b.get('Width', 0))
                            h = int(b.get('Height', 0))
                            bounds = (x, y, x + w, y + h)
                            break
    except Exception:
        pass
        
    try:
        from PIL import ImageGrab
        if bounds:
            img = ImageGrab.grab(bbox=bounds)
        else:
            img = ImageGrab.grab()
        img.save(output_path)
        print(f"📸 Screenshot Saved: {output_path}")
        print(f"📂 Directory: {save_dir}\n")
    except Exception as e:
        print(f"❌ Failed to capture screenshot: {e}\n")


def on_press(key):
    currently_pressed.add(key)
    
    # Check for Cmd + I
    cmd_pressed = (
        keyboard.Key.cmd in currently_pressed or
        keyboard.Key.cmd_l in currently_pressed or
        keyboard.Key.cmd_r in currently_pressed
    )
    try:
        char_key = key.char.lower() if hasattr(key, 'char') and key.char else ""
    except Exception:
        char_key = ""
        
    if cmd_pressed and char_key == "i":
        currently_pressed.discard(key)
        import threading
        threading.Thread(target=trigger_screenshot, daemon=True).start()
        return

    try:
        print(f"Pressed: {key.char}")
    except AttributeError:
        print(f"Pressed: {key}")


def on_release(key):
    currently_pressed.discard(key)
    if key == keyboard.Key.esc:
        print("Exiting key tracker.")
        return False


if __name__ == "__main__":
    print("Global keyboard tracker started. Press ESC to stop.")
    with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
        listener.join()
