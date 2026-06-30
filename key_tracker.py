#!/usr/bin/env python3
"""
Key Tracker for macOS
Tracks global keyboard key presses and displays them in the terminal.
Supports real-time logging, live buffer printing on Enter, and optional log files.

Requires pynput library. If missing, install with:
    pip install pynput

Note: macOS requires Accessibility permissions for the terminal/IDE running this script.
"""

import sys
import os
import time
import platform
import argparse

# ANSI escape codes for beautiful terminal formatting
GREEN = "\033[92m"
CYAN = "\033[96m"
YELLOW = "\033[93m"
MAGENTA = "\033[95m"
RED = "\033[91m"
RESET = "\033[0m"
BOLD = "\033[1m"
UNDERLINE = "\033[4m"

# Map special keys to clean display labels
KEY_MAP = {}

def setup_key_map(keyboard):
    global KEY_MAP
    KEY_MAP = {
        keyboard.Key.space: f"{MAGENTA}[SPACE]{RESET}",
        keyboard.Key.enter: f"{GREEN}[ENTER]{RESET}",
        keyboard.Key.backspace: f"{RED}[BACKSPACE]{RESET}",
        keyboard.Key.tab: f"{YELLOW}[TAB]{RESET}",
        keyboard.Key.shift: f"{YELLOW}[SHIFT]{RESET}",
        keyboard.Key.shift_r: f"{YELLOW}[SHIFT-R]{RESET}",
        keyboard.Key.ctrl: f"{YELLOW}[CTRL]{RESET}",
        keyboard.Key.ctrl_r: f"{YELLOW}[CTRL-R]{RESET}",
        keyboard.Key.alt: f"{YELLOW}[ALT]{RESET}",
        keyboard.Key.alt_r: f"{YELLOW}[ALT-R]{RESET}",
        keyboard.Key.cmd: f"{YELLOW}[CMD]{RESET}",
        keyboard.Key.cmd_r: f"{YELLOW}[CMD-R]{RESET}",
        keyboard.Key.caps_lock: f"{YELLOW}[CAPS LOCK]{RESET}",
        keyboard.Key.esc: f"{RED}[ESC]{RESET}",
        keyboard.Key.up: f"{CYAN}[↑]{RESET}",
        keyboard.Key.down: f"{CYAN}[↓]{RESET}",
        keyboard.Key.left: f"{CYAN}[←]{RESET}",
        keyboard.Key.right: f"{CYAN}[→]{RESET}",
    }

# Running buffer to group typed characters into words/sentences
typed_buffer = []

def check_macos_permissions(keyboard):
    """
    Attempts to start a temporary listener to verify macOS accessibility permissions.
    """
    if platform.system() != "Darwin":
        return True

    try:
        # Create a dummy listener to test permissions
        listener = keyboard.Listener(on_press=lambda k: None)
        listener.start()
        time.sleep(0.1)
        if not listener.running:
            listener.stop()
            return False
        listener.stop()
        return True
    except Exception:
        return False

def print_macos_permission_warning():
    print(f"\n{RED}{BOLD}" + "=" * 65)
    print("🚨 macOS Accessibility Permissions Required 🚨".center(65))
    print("=" * 65 + f"{RESET}")
    print("To capture global keystrokes, macOS requires Accessibility permissions.")
    print("Please grant permission to the terminal or application running this script:\n")
    print(f"  1. Open {BOLD}System Settings{RESET} (or System Preferences).")
    print(f"  2. Go to {BOLD}Privacy & Security{RESET} -> {BOLD}Accessibility{RESET}.")
    print(f"  3. Check if your terminal (e.g., {CYAN}Terminal{RESET}, {CYAN}iTerm2{RESET}) or editor (e.g., {CYAN}VS Code{RESET}) is enabled.")
    print(f"  4. If not, toggle the switch to {GREEN}ON{RESET} (you may need to enter your password).")
    print("  5. Restart the terminal or application and run this script again.")
    print(f"{RED}" + "=" * 65 + f"{RESET}\n")

def get_args():
    parser = argparse.ArgumentParser(description="Global key tracker with beautiful terminal output.")
    parser.add_argument(
        "-o", "--output", 
        type=str, 
        help="Optional file path to log keystrokes to a text file."
    )
    return parser.parse_args()

def main():
    # Attempt to import pynput
    try:
        from pynput import keyboard
    except ImportError:
        print(f"{RED}{BOLD}Error:{RESET} The '{YELLOW}pynput{RESET}' library is not installed.")
        print(f"Please install it using: {GREEN}pip install pynput{RESET}")
        sys.exit(1)

    setup_key_map(keyboard)
    args = get_args()

    # Clear terminal screen and print dashboard header
    os.system('cls' if os.name == 'nt' else 'clear')
    print(f"{CYAN}{BOLD}" + "═" * 60)
    print(" ⌨️  GLOBAL KEY TRACKER ACTIVE ".center(60, "═"))
    print("═" * 60 + f"{RESET}")
    print(f"Platform:  {BOLD}{platform.system()} ({platform.release()}){RESET}")
    print(f"Exit Key:  {RED}{BOLD}ESC{RESET}")
    if args.output:
        print(f"Logging to: {GREEN}{args.output}{RESET}")
        # Initialize log file
        try:
            with open(args.output, "a", encoding="utf-8") as f:
                f.write(f"\n--- Key Tracker Started at {time.strftime('%Y-%m-%d %H:%M:%S')} ---\n")
        except IOError as e:
            print(f"{RED}Error writing to log file: {e}{RESET}")
            sys.exit(1)
    print(f"{CYAN}" + "─" * 60 + f"{RESET}")
    print("Waiting for keypresses (focus another window to test)...")
    print(f"{CYAN}" + "─" * 60 + f"{RESET}\n")

    # Check for macOS permissions
    if not check_macos_permissions(keyboard):
        print_macos_permission_warning()
        sys.exit(1)

    currently_pressed = set()

    def trigger_screenshot():
        save_dir = os.path.expanduser("~/QuickClip_Screenshots")
        os.makedirs(save_dir, exist_ok=True)
        ts = time.strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(save_dir, f"screenshot_{ts}.png")
        
        print(f"\n{GREEN}{BOLD}[CMD+I Detected]{RESET} Capturing active window...")
        
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
            print(f"📸 {GREEN}{BOLD}Screenshot Saved:{RESET} {output_path}")
            print(f"📂 {CYAN}Directory:{RESET} {save_dir}\n")
        except Exception as e:
            print(f"❌ {RED}Failed to capture screenshot:{RESET} {e}\n")

    def log_to_file(text):
        if args.output:
            try:
                with open(args.output, "a", encoding="utf-8") as f:
                    f.write(text + "\n")
            except IOError:
                pass

    def on_press(key):
        global typed_buffer
        timestamp = time.strftime("%H:%M:%S")
        
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

        key_display = ""
        log_text = ""
        
        # Determine key representation
        try:
            if key.char is not None:
                key_display = f"'{CYAN}{key.char}{RESET}'"
                log_text = key.char
                typed_buffer.append(key.char)
            else:
                raise AttributeError
        except AttributeError:
            if key in KEY_MAP:
                key_display = KEY_MAP[key]
                # Special handling for key logging buffers
                if key == keyboard.Key.space:
                    typed_buffer.append(" ")
                    log_text = " "
                elif key == keyboard.Key.enter:
                    typed_buffer.append("\n")
                    log_text = "[ENTER]"
                elif key == keyboard.Key.backspace:
                    if typed_buffer:
                        typed_buffer.pop()
                    log_text = "[BACKSPACE]"
                else:
                    log_text = f"[{str(key).replace('Key.', '').upper()}]"
            else:
                key_display = f"{YELLOW}{key}{RESET}"
                log_text = f"[{key}]"

        # Print the immediate keypress event
        print(f"[{timestamp}] Key: {key_display}")
        
        # Write to log file if specified
        log_to_file(f"[{timestamp}] {log_text}")

        # When Enter is pressed, dump the line buffer
        if key == keyboard.Key.enter:
            if typed_buffer:
                # Remove the trailing newline character
                if typed_buffer[-1] == "\n":
                    typed_buffer.pop()
                line = "".join(typed_buffer).strip()
                if line:
                    formatted_line = f"{GREEN}➔ Buffer:{RESET} \"{BOLD}{line}{RESET}\""
                    print(formatted_line)
                    log_to_file(f"--- Buffer Typed: \"{line}\" ---")
                typed_buffer.clear()

    def on_release(key):
        currently_pressed.discard(key)
        if key == keyboard.Key.esc:
            print(f"\n{RED}Exiting Key Tracker. Goodbye!{RESET}")
            log_to_file(f"--- Key Tracker Stopped at {time.strftime('%Y-%m-%d %H:%M:%S')} ---")
            return False

    # Start listening to keyboard events
    try:
        with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
            listener.join()
    except KeyboardInterrupt:
        print(f"\n{RED}Key Tracker stopped by Ctrl+C.{RESET}")
    except Exception as e:
        print(f"\n{RED}An error occurred: {e}{RESET}")

if __name__ == "__main__":
    main()
