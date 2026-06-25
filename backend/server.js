const express = require('express');
const cors = require('cors');
const path = require('path');
const os = require('os');

const clipsController = require('./controllers/clips');
const screenshotsController = require('./controllers/screenshots');

const app = express();
const PORT = process.env.PORT || 3000;

// Resolve QuickClip notes path
const SAVE_DIR = path.join(os.homedir(), 'QuickClip_Notes');
const SHOTS_DIR = path.join(SAVE_DIR, 'screenshots');

// Middlewares
app.use(cors());
app.use(express.json());

// Static serving for screenshot images
app.use('/api/screenshots/image', express.static(SHOTS_DIR));

// API Routes

// 1. Clips APIs
app.get('/api/clips', clipsController.getClips);
app.post('/api/clips', clipsController.addClip);

// 2. Screenshots APIs
app.get('/api/screenshots', screenshotsController.getScreenshots);
app.post('/api/screenshots', screenshotsController.upload.single('file'), screenshotsController.addScreenshot);

// Base info route
app.get('/', (req, res) => {
    res.json({
        name: 'QuickClip Backend API',
        status: 'running',
        endpoints: {
            clips: {
                get: '/api/clips',
                post: '/api/clips (body: { text: string })'
            },
            screenshots: {
                get: '/api/screenshots',
                post: '/api/screenshots (form-data: file)',
                images: '/api/screenshots/image/:filename'
            }
        }
    });
});

// Start Server
app.listen(PORT, () => {
    console.log(`=================================================`);
    console.log(` 📋 QuickClip Node.js API is running!`);
    console.log(` 🌐 Server: http://localhost:${PORT}`);
    console.log(` 📁 Notes directory: ${SAVE_DIR}`);
    console.log(`=================================================`);
});
