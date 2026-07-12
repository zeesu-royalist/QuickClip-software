# 📋 QuickClip — Clipboard & Screenshot Monitor

QuickClip is a lightweight, cross-platform tool that monitors your clipboard text history and system screenshots, dynamically compiling them into a beautiful, live-updating HTML dashboard. 

It handles background text polling, automatically tracks screenshot directories, and supports active window capture via a global keyboard shortcut.

---

## ✨ Features

- **📝 Clipboard Text Monitoring**: Automatically listens for newly copied text snippets in the background, adding them to your history and highlighting code snippets.
- **📸 Screenshot Watching**: Watches default OS screenshot folders using `watchdog` (relying on low CPU usage event listeners) with a fallback to polling if the package is missing.
- **🖼️ Clipboard Image Monitor**: (macOS/Linux) Captures screenshots directly from clipboard-based tools (like Flameshot or native hotkeys) and saves them locally.
- **⌨️ Active Window Capture Hotkey**: Press **`Ctrl + Alt + Q`** (Windows/Linux) or **`Cmd + I`** (macOS) to instantly snap a high-resolution, cropped screenshot of your active window.
- **🖥️ Windows DPI-Awareness**: Prevents coordinate misalignment on high-DPI/display-scaled screens, ensuring active window screenshots fit window bounds perfectly.
- **🌐 Responsive HTML Dashboard**: A beautiful, premium glassmorphism dark dashboard (`viewer.html`) with:
  - Full-text search and filtering.
  - One-click copy for text clips.
  - Persistent scroll position and search queries across reloads.
  - Image lightbox zoom view for screenshots.
  - Focus-triggered and timed auto-reloading.
- **☁️ Google Sheets & Drive Sync (Webhook)**: Automatically syncs copied text and captured screenshots to a Google Sheet via a Google Apps Script Webhook. Screenshots are uploaded directly to Google Drive and linked in the sheet.

---

## 📁 Folder Structure

The project is split into a modular format for high readability and maintainability:

```text
e:\py
├── README.md                  # Project documentation
├── quickclip.py               # Root entry point wrapper
└── quickclip_core/            # Package directory
    ├── __init__.py            # Package initialization
    ├── config.py              # Constants, OS settings, and watch directory resolution
    ├── storage.py             # File reading, writing, and base64 thumbnail rendering
    ├── viewer.py              # HTML dashboard template and file compiler
    ├── clipboard.py           # Clipboard text listener daemon thread
    ├── screenshot.py          # Watchdog and clipboard image listeners
    └── listener.py            # Main runner, banner printing, and hotkey listeners
```

---

## 🚀 Getting Started

QuickClip is cross-platform but requires specific system utilities and permissions depending on your OS.

### 📋 Prerequisites & System Dependencies

Choose your operating system below to install any system-level dependencies before installing Python packages:

#### 🐧 Linux (Ubuntu / Debian / Linux Mint)
To read the clipboard and capture active windows, you must install the following tools:
```bash
sudo apt update
sudo apt install -y xclip wl-clipboard xdotool x11-utils python3-tk
```
> [!IMPORTANT]
> **Wayland Support**: Many modern Linux distributions use Wayland by default. Global hotkeys (`pynput`) and window screenshot utilities might fail or capture black screens under Wayland. For full feature support, select **Ubuntu on Xorg** (or your desktop environment's X11 session) from the login screen options.

#### 🍏 macOS (Darwin)
No additional system packages are required, but macOS's strict sandbox security requires you to grant system permissions.
> [!IMPORTANT]
> **System Permissions**: When you run the script, macOS will prompt you to grant the following:
> 1. **Accessibility**: Required for the `pynput` listener to capture global keyboard shortcuts (`Cmd + I`).
> 2. **Screen Recording**: Required for the script to grab active window screenshot boundaries.
> 
> You can manually add and enable your Terminal (e.g., Terminal.app, iTerm2, or VS Code) under:
> *System Settings > Privacy & Security > Accessibility / Screen Recording*.

#### 🪟 Windows
No special system utilities are needed.
> [!TIP]
> **Elevated Windows**: If you are active on a window running with Administrator privileges (e.g., cmd/PowerShell opened as Admin), the global hotkey `Ctrl + Alt + Q` might not trigger unless the terminal running QuickClip is also running as Administrator.

---

### 💻 Installation & Setup

#### Step 1: Create a Virtual Environment
Navigate to the project root and create a clean environment:
```bash
# Windows
python -m venv venv

# macOS / Linux
python3 -m venv venv
```

#### Step 2: Activate the Virtual Environment
```bash
# Windows (Command Prompt)
venv\Scripts\activate.bat

# Windows (PowerShell)
venv\Scripts\Activate.ps1

# macOS / Linux (bash/zsh)
source venv/bin/activate
```

#### Step 3: Install Dependencies
Run the command below. The `requirements.txt` file uses PEP 508 environment markers to automatically detect your OS and install only the appropriate packages:
```bash
pip install -r requirements.txt
```

---

### 🏃 Running QuickClip

Ensure your virtual environment is active, then run:

```bash
python quickclip.py
```

Upon launching, the script prints a dashboard status banner showing:
- 👁️ Active screenshot directories being monitored.
- 📁 Saved files directory path (`~/QuickClip_Notes`).
- 🌐 Local path to your live-updating glassmorphism HTML dashboard.

---

### ⌨️ Usage Controls

| Action | Windows | Linux (Ubuntu) | macOS |
| :--- | :--- | :--- | :--- |
| **Active Window Screenshot** | `Ctrl + Alt + Q` | `Ctrl + Alt + Q` | `Cmd + I` |
| **Clipboard Text History** | Automatically logged on copy | Automatically logged on copy | Automatically logged on copy |
| **Clipboard Image Capture** | N/A (Uses file watch folders) | Automatically logged on copy | Automatically logged on copy |
| **Access Dashboard** | Open `~/QuickClip_Notes/viewer.html` | Open `~/QuickClip_Notes/viewer.html` | Open `~/QuickClip_Notes/viewer.html` |
| **Stop Monitor** | `Ctrl + C` | `Ctrl + C` | `Ctrl + C` |

---

## ⚙️ Configuration & Data Storage

All logged data is saved inside your user home directory:

- **Directory Path**: `~/QuickClip_Notes/` (e.g., `C:\Users\Username\QuickClip_Notes` on Windows)
- **`clips.json`**: Stores the raw history of copied text (up to 500 clips).
- **`screenshots.json`**: Stores screenshot metadata and inline base64 thumbnails (up to 200 screenshots).
- **`screenshots/`**: Stores local copy images of captured/detected screenshots.
- **`viewer.html`**: The HTML UI dashboard.
- **`config.json`**: Add your `WEBHOOK_URL` here to enable Google Sheets integration.

---

## ☁️ Google Sheets & Drive Integration

QuickClip can automatically log your clipboard text and upload screenshots to Google Drive, displaying them beautifully inside a Google Sheet.

### Setup Instructions

1. **Create a Google Apps Script Webhook**:
   - Open your Google Sheet, go to **Extensions > Apps Script**.
   - Paste the following code (replace `YOUR_DRIVE_FOLDER_ID_HERE` with your Drive folder ID):

   ```javascript
   const FOLDER_ID = "YOUR_DRIVE_FOLDER_ID_HERE"; 

   function doPost(e) {
     try {
       const data = JSON.parse(e.postData.contents);
       const sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
       
       let savedContent = data.content;
       
       if (data.type === "image") {
         const split = data.content.split('base64,');
         if (split.length === 2) {
           const mime = split[0].split(':')[1].split(';')[0];
           const bytes = Utilities.base64Decode(split[1]);
           const blob = Utilities.newBlob(bytes, mime, data.filename || "screenshot.png");
           
           const folder = DriveApp.getFolderById(FOLDER_ID);
           const file = folder.createFile(blob);
           file.setSharing(DriveApp.Access.ANYONE_WITH_LINK, DriveApp.Permission.VIEW);
           
           const fileId = file.getId();
           savedContent = `=IMAGE("https://drive.google.com/uc?export=view&id=${fileId}")`;
         }
       }
       
       sheet.appendRow([data.timestamp, data.username, data.type, savedContent]);
       if (data.type === "image") sheet.setRowHeights(sheet.getLastRow(), 1, 200);
       
       return ContentService.createTextOutput(JSON.stringify({ "status": "success" })).setMimeType(ContentService.MimeType.JSON);
     } catch (error) {
       return ContentService.createTextOutput(JSON.stringify({ "status": "error", "message": error.toString() })).setMimeType(ContentService.MimeType.JSON);
     }
   }
   ```
   - Click **Deploy > New deployment**, select **Web app**.
   - Set "Execute as" to **Me**, and "Who has access" to **Anyone**.
   - Deploy and copy the Web App URL.

2. **Configure QuickClip**:
   - In your `~/QuickClip_Notes` directory, create a `config.json` file.
   - Add your Webhook URL:
   ```json
   {
     "WEBHOOK_URL": "https://script.google.com/macros/s/YOUR_URL_HERE/exec"
   }
   ```
   - Restart QuickClip! Your Google Sheet should have 4 columns: `Timestamp`, `Username`, `Type`, and `Content`.
