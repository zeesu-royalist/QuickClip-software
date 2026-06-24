import threading
from datetime import datetime
from quickclip_core.config import OS, SCREENSHOT_WATCH_DIRS, SAVE_DIR, SHOTS_DIR
from quickclip_core.storage import add_screenshot
from quickclip_core.viewer import generate_viewer
from quickclip_core.clipboard import clipboard_monitor
from quickclip_core.screenshot import screenshot_monitor

# Make the process DPI-aware on Windows to resolve coordinate mismatches with ImageGrab
if OS == "Windows":
    import ctypes
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1) # System DPI Aware
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass

def start_listener():
    """Start all background monitors and the optional keyboard shortcut listener."""

    # 1. Clipboard text monitor
    threading.Thread(target=clipboard_monitor, daemon=True).start()

    # 2. Screenshot monitor (watchdog or polling + optional clipboard-image poll)
    screenshot_monitor()

    # 3. Keyboard shortcut listener (Ctrl+Alt+Q)
    def take_screenshot():
        try:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            temp_file = SHOTS_DIR / f"hotkey_{ts}.png"

            if OS == "Windows":
                
                # pyrefly: ignore [missing-import]
                import pygetwindow as gw
                from PIL import ImageGrab

                win = gw.getActiveWindow()

                if not win:
                    print("No active window found")
                    return

                bbox = (
                    win.left,
                    win.top,
                    win.right,
                    win.bottom
                )

                img = ImageGrab.grab(bbox=bbox)
                img.save(str(temp_file))

            if add_screenshot(temp_file):
                generate_viewer()
                print(f"📸 Screenshot captured: {temp_file.name}")

        except Exception as e:
            print("Error:", e)
            
    _print_banner()

    if OS == "Windows":
        import keyboard as win_keyboard

        win_keyboard.add_hotkey("ctrl+alt+q", take_screenshot)
        print("⌨️ Windows hotkey registered: Ctrl+Alt+Q")

        win_keyboard.wait()
    else:
        from pynput import keyboard as pynput_keyboard

        current_keys = set()

        def on_press(key):
            current_keys.add(key)

            ctrl = (
                pynput_keyboard.Key.ctrl_l in current_keys or
                pynput_keyboard.Key.ctrl_r in current_keys
            )

            alt = (
                pynput_keyboard.Key.alt_l in current_keys or
                pynput_keyboard.Key.alt_r in current_keys
            )

            try:
                q_pressed = key.char.lower() == "q"
            except:
                q_pressed = False

            if ctrl and alt and q_pressed:
                take_screenshot()

        def on_release(key):
            current_keys.discard(key)

        print("⌨️ Linux/macOS hotkey registered: Ctrl+Alt+Q")

        listener = pynput_keyboard.Listener(
            on_press=on_press,
            on_release=on_release
        )

        listener.start()
        listener.join()

def _print_banner(no_hotkey: bool = False):
    print("=" * 56)
    print("   📋 QuickClip is running :")
    print("   ✅ Clipboard text: auto-monitor active")
    if SCREENSHOT_WATCH_DIRS:
        print(f"   📸 Screenshots: watching {len(SCREENSHOT_WATCH_DIRS)} folder(s)")
    else:
        print("   ⚠️  No screenshot watch folders found")
    if no_hotkey:
        print("   ⚠️  Keyboard shortcut disabled (pynput not available)")
    else:
        print("   ⌨️  Shortcut: Ctrl + Alt + Q")
    print(f"   📁 Save dir : {SAVE_DIR}")
    print(f"   🌐 Viewer  : {SAVE_DIR}/viewer.html")
    print("   To Stop: Ctrl+C")
    print("=" * 56)
