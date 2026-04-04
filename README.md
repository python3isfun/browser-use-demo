# Browser Use Demo

A Python demo showcasing browser automation, video recording, and website cloning using Playwright.

## Features

- Automated browser navigation with Chromium
- Video recording of browser sessions (1280x720)
- Full-page screenshot capture
- **Website Cloner** - Extract any website and generate a local React replica

## Installation

```bash
pip install -r requirements.txt
playwright install chromium
```

## Usage

### Browser Recording Demo

```bash
python demo_browser.py
```

This will:
1. Launch a visible Chromium browser
2. Navigate to example.com and news.ycombinator.com
3. Capture a screenshot (`last-page.png`)
4. Save the session recording to `videos/`

### Website Cloner

Clone any website into a local React application:

```bash
python -m website_cloner https://example.com -o ./output -n my-clone
```

Options:
- `-o, --output` - Output directory (default: `./output`)
- `-n, --name` - Project name (default: domain name)
- `--no-download-assets` - Skip downloading images/fonts

Then run the cloned site:

```bash
cd output/my-clone
npm install
npm run dev
```

Open http://localhost:5173 to view the replica.

**Features:**
- Extracts HTML structure and computed styles
- Downloads images and assets locally
- Generates a Vite + React project
- Mock interactions (buttons log to console, forms don't submit)

## Output

- `videos/` - Recorded browser session videos
- `last-page.png` - Screenshot of the final page
- `output/` - Generated React projects from website cloner
