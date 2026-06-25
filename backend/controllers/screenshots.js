const fs = require('fs');
const path = require('path');
const os = require('os');
const crypto = require('crypto');
const multer = require('multer');

const SAVE_DIR = path.join(os.homedir(), 'QuickClip_Notes');
const SHOTS_FILE = path.join(SAVE_DIR, 'screenshots.json');
const SHOTS_DIR = path.join(SAVE_DIR, 'screenshots');

// Ensure directories exist
if (!fs.existsSync(SAVE_DIR)) {
    fs.mkdirSync(SAVE_DIR, { recursive: true });
}
if (!fs.existsSync(SHOTS_DIR)) {
    fs.mkdirSync(SHOTS_DIR, { recursive: true });
}

// Multer storage setup
const diskStorage = multer.diskStorage({
    destination: function (req, file, cb) {
        cb(null, SHOTS_DIR);
    },
    filename: function (req, file, cb) {
        const now = new Date();
        const pad = (n) => String(n).padStart(2, '0');
        const dateStr = now.getFullYear() +
            pad(now.getMonth() + 1) +
            pad(now.getDate()) + '_' +
            pad(now.getHours()) +
            pad(now.getMinutes()) +
            pad(now.getSeconds());
        cb(null, `${dateStr}_${file.originalname}`);
    }
});

const upload = multer({ storage: diskStorage });

function loadShots() {
    if (fs.existsSync(SHOTS_FILE)) {
        try {
            const data = fs.readFileSync(SHOTS_FILE, 'utf8');
            return JSON.parse(data);
        } catch (e) {
            return [];
        }
    }
    return [];
}

function saveShots(shots) {
    fs.writeFileSync(SHOTS_FILE, JSON.stringify(shots, null, 2), 'utf8');
}

function _fileHash(filePath) {
    const fileBuffer = fs.readFileSync(filePath);
    const hashSum = crypto.createHash('md5');
    hashSum.update(fileBuffer);
    return hashSum.digest('hex');
}

function getScreenshots(req, res) {
    try {
        const shots = loadShots();
        return res.json(shots);
    } catch (error) {
        return res.status(500).json({ error: 'Failed to read screenshots.' });
    }
}

function addScreenshot(req, res) {
    try {
        if (!req.file) {
            return res.status(400).json({ error: 'No image file uploaded.' });
        }

        const filePath = req.file.path;
        const fileHash = _fileHash(filePath);

        const shots = loadShots();

        // Duplicate check
        if (shots.some(s => s.hash === fileHash)) {
            // Delete the uploaded duplicate file
            fs.unlinkSync(filePath);
            return res.json({ success: false, message: 'Duplicate screenshot ignored.' });
        }

        // Generate base64 thumbnail string (fallback to original base64 as-is)
        const fileData = fs.readFileSync(filePath);
        const ext = path.extname(req.file.originalname).toLowerCase();
        const mimeType = ext === '.png' ? 'image/png' : 'image/jpeg';
        const thumb_b64 = `data:${mimeType};base64,${fileData.toString('base64')}`;

        const date = new Date();
        const options = { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit', hour12: true };
        const formattedTime = date.toLocaleDateString('en-GB', options).replace(/,/g, '');

        shots.unshift({
            filename: req.file.filename,
            original: filePath,
            time: formattedTime,
            hash: fileHash,
            thumb_b64: thumb_b64
        });

        // Limit to 200 screenshots
        saveShots(shots.slice(0, 200));

        return res.status(201).json({ success: true, screenshot: shots[0] });
    } catch (error) {
        // Cleanup file on error
        if (req.file && fs.existsSync(req.file.path)) {
            try { fs.unlinkSync(req.file.path); } catch (e) {}
        }
        return res.status(500).json({ error: 'Failed to save screenshot.' });
    }
}

module.exports = {
    getScreenshots,
    addScreenshot,
    upload
};
