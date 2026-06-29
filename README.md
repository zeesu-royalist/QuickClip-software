# 📋 QuickClip — Clipboard & Screenshot Monitor

QuickClip is a lightweight, cross-platform tool that monitors your clipboard text history and system screenshots, dynamically compiling them into a beautiful, live-updating HTML dashboard. 

It handles background text polling, automatically tracks screenshot directories, and supports active window capture via a global keyboard shortcut.

---

## ✨ Features

- **📝 Clipboard Text Monitoring**: Automatically listens for newly copied text snippets in the background, adding them to your history and highlighting code snippets.
- **📸 Screenshot Watching**: Watches default OS screenshot folders using `watchdog` (relying on low CPU usage event listeners) with a fallback to polling if the package is missing.
- **🖼️ Clipboard Image Monitor**: (macOS/Linux) Captures screenshots directly from clipboard-based tools (like Flameshot or native hotkeys) and saves them locally.
- **⌨️ Active Window Capture Hotkey**: Press **`Ctrl + Alt + Q`** to instantly snap a high-resolution, cropped screenshot of your active window.
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

### 1. Virtual Environment & Installation

Ensure you have Python 3.8+ installed.

#### Step 1: Create a Virtual Environment
```bash
# Create the environment named 'venv'
python -m venv venv
```

#### Step 2: Activate the Virtual Environment
```bash
venv\Scripts\Activate
```

#### Step 3: Install Dependencies
Install the required packages from `requirements.txt`:
```bash
pip install -r requirements.txt
```


### 2. Running QuickClip

To start the monitors, run the root wrapper script:

```bash
python quickclip.py
```

Upon launching, the script prints a dashboard status banner showing:
- Active screenshot directories being monitored.
- Saved files directory path.
- The path to the live HTML dashboard file.

### 3. Usage Controls

- **Automatic Logging**: Any plain text you copy or screenshot you take (via standard print-screen tools) is automatically logged.
- **Active Window Capture**: Press **`Ctrl + Alt + Q`** to capture only the active window.
- **Accessing Dashboard**: Open the generated `viewer.html` located in your system's home directory under `~/QuickClip_Notes/viewer.html` in any web browser.
- **Termination**: Press `Ctrl + C` in the console window to safely exit the monitor.

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
