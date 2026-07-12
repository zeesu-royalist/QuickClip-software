# 📋 QuickClip

QuickClip watches your clipboard and screenshots, then shows them in a live HTML dashboard.

## Features
- Auto-saves copied text
- Auto-saves screenshots (from screenshot folder or clipboard)
- Hotkey for instant window screenshot: `Ctrl+Alt+Q` (Win/Linux) or `Cmd+I` (Mac)
- Dashboard with search, copy button, and image zoom
- Optional sync to Google Sheets + Drive

## Setup

**1. Install system tools (Linux only)**
```bash
sudo apt install -y xclip wl-clipboard xdotool x11-utils python3-tk
```
*(Use an X11/Xorg session, not Wayland, for hotkeys to work)*

**macOS**: allow Terminal under System Settings → Privacy & Security → Accessibility & Screen Recording.

**Windows**: no extra setup needed.

**2. Create & activate a virtual environment**
```bash
python -m venv venv
# Windows: venv\Scripts\activate
# Mac/Linux: source venv/bin/activate
```

**3. Install dependencies**
```bash
pip install -r requirements.txt
```

**4. Run it**
```bash
python quickclip.py
```

## Where things are saved
Everything goes to `~/QuickClip_Notes/`:
- `clips.json` – copied text
- `screenshots.json` + `screenshots/` – screenshots
- `viewer.html` – the dashboard (open this in a browser)
- `config.json` – add your webhook URL here (optional)

## Controls
| Action | Shortcut |
|---|---|
| Screenshot active window | `Ctrl+Alt+Q` / `Cmd+I` |
| Stop QuickClip | `Ctrl+C` |

## Optional: Google Sheets sync
1. In Google Sheets, go to **Extensions → Apps Script**, paste in a `doPost` script that saves rows to the sheet and uploads images to Drive.
2. Deploy it as a **Web App** (execute as Me, access: Anyone), copy the URL.
3. Put it in `~/QuickClip_Notes/config.json`:
```json
{ "WEBHOOK_URL": "your-script-url-here" }
```
4. Restart QuickClip.
