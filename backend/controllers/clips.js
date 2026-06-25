const fs = require('fs');
const path = require('path');
const os = require('os');

const SAVE_DIR = path.join(os.homedir(), 'QuickClip_Notes');
const CLIPS_FILE = path.join(SAVE_DIR, 'clips.json');

// Helper to ensure clips directory exists
if (!fs.existsSync(SAVE_DIR)) {
    fs.mkdirSync(SAVE_DIR, { recursive: true });
}

function loadClips() {
    if (fs.existsSync(CLIPS_FILE)) {
        try {
            const data = fs.readFileSync(CLIPS_FILE, 'utf8');
            return JSON.parse(data);
        } catch (e) {
            return [];
        }
    }
    return [];
}

function saveClips(clips) {
    fs.writeFileSync(CLIPS_FILE, JSON.stringify(clips, null, 2), 'utf8');
}

function getClips(req, res) {
    try {
        const clips = loadClips();
        return res.json(clips);
    } catch (error) {
        return res.status(500).json({ error: 'Failed to read clips.' });
    }
}

function addClip(req, res) {
    try {
        let { text } = req.body;
        if (!text || typeof text !== 'string') {
            return res.status(400).json({ error: 'Text content is required.' });
        }
        
        text = text.trim();
        if (!text) {
            return res.status(400).json({ error: 'Text content cannot be empty.' });
        }

        const clips = loadClips();

        // Exact duplicate at top — skip
        if (clips.length > 0 && clips[0].text === text) {
            return res.json({ success: false, message: 'Duplicate clip ignored.' });
        }

        // Format: Day Month Year, Hour:Minute AM/PM
        const date = new Date();
        const options = { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit', hour12: true };
        // Output format check e.g., "24 Jun 2026, 10:48 AM"
        const formattedTime = date.toLocaleDateString('en-GB', options).replace(/,/g, '');

        clips.unshift({
            text,
            time: formattedTime
        });

        // Limit to 500 clips
        saveClips(clips.slice(0, 500));

        return res.status(201).json({ success: true, clip: clips[0] });
    } catch (error) {
        return res.status(500).json({ error: 'Failed to save clip.' });
    }
}

module.exports = {
    getClips,
    addClip
};
