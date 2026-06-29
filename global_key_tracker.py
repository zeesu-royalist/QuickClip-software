#!/usr/bin/env python3
"""Global keyboard tracker that prints pressed keys to the terminal.

Requires pynput, which is already listed in requirements.txt.
Run:
    python3 global_key_tracker.py

Press ESC to exit.
"""

from pynput import keyboard


def on_press(key):
    try:
        print(f"Pressed: {key.char}")
    except AttributeError:
        print(f"Pressed: {key}")


def on_release(key):
    if key == keyboard.Key.esc:
        print("Exiting key tracker.")
        return False


if __name__ == "__main__":
    print("Global keyboard tracker started. Press ESC to stop.")
    with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
        listener.join()
