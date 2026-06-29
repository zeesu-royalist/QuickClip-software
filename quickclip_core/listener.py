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

def _is_ubuntu() -> bool:
    if OS != "Linux":
        return False
    try:
        with open("/etc/os-release", "r", encoding="utf-8") as f:
            return "ubuntu" in f.read().lower()
    except Exception:
        return False


def _get_ubuntu_active_window_geometry():
    try:
        from Xlib import X, display
        d = display.Display()
        root = d.screen().root
        NET_ACTIVE_WINDOW = d.intern_atom('_NET_ACTIVE_WINDOW')
        active = root.get_full_property(NET_ACTIVE_WINDOW, X.AnyPropertyType)
        if not active or not active.value:
            return None

        window_id = active.value[0]
        win = d.create_resource_object('window', window_id)
        trans = win.translate_coords(root, 0, 0)
        left, top = trans.dest_x, trans.dest_y if hasattr(trans, 'dest_x') else trans[0], trans[1]
        geom = win.get_geometry()
        return (left, top, left + geom.width, top + geom.height)
    except Exception:
        pass

    try:
        import re
        import subprocess
        output = subprocess.check_output(['xprop', '-root', '_NET_ACTIVE_WINDOW'], text=True)
        match = re.search(r'window id # (0x[0-9a-fA-F]+)', output)
        if not match:
            return None
        window_id = match.group(1)
        xwininfo = subprocess.check_output(['xwininfo', '-id', window_id], text=True)
        left = top = width = height = None
        for line in xwininfo.splitlines():
            if 'Absolute upper-left X:' in line:
                left = int(line.split(':')[1].strip().split()[0])
            elif 'Absolute upper-left Y:' in line:
                top = int(line.split(':')[1].strip().split()[0])
            elif 'Width:' in line:
                width = int(line.split(':')[1].strip())
            elif 'Height:' in line:
                height = int(line.split(':')[1].strip())
        if None in (left, top, width, height):
            return None
        return (left, top, left + width, top + height)
    except Exception:
        return None


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

            elif _is_ubuntu():
                coords = _get_ubuntu_active_window_geometry()
                if not coords:
                    print("No active window found")
                    return

                try:
                    from PIL import ImageGrab
                    img = ImageGrab.grab(bbox=coords)
                except Exception:
                    import pyautogui
                    img = pyautogui.screenshot(region=(coords[0], coords[1], coords[2] - coords[0], coords[3] - coords[1]))

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
                char_key = key.char.lower() if hasattr(key, 'char') and key.char else ""
            except:
                char_key = ""

            q_pressed = char_key == "q"

            if ctrl and alt and q_pressed:
                take_screenshot()
            elif ctrl and char_key in ("c", "x"):
                import time
                def _trigger():
                    time.sleep(0.15)
                    from quickclip_core.clipboard import check_now as check_text
                    from quickclip_core.screenshot import check_now as check_image
                    check_text()
                    check_image()
                threading.Thread(target=_trigger, daemon=True).start()

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
