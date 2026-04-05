# Browser Use Demo

A Python demo showcasing browser automation, video recording, and website cloning using Playwright.

## Features

- Automated browser navigation with Chromium
- Video recording of browser sessions
- Full-page screenshot capture
- **Website Cloner** - Extract any website and generate a high-fidelity React replica
- **Comparison Videos** - Record side-by-side videos of cloned vs original sites

## Installation

```bash
pip install -r requirements.txt
playwright install chromium
```

## Usage

### Website Cloner

Clone any website into a local React application:

```bash
python -m website_cloner https://example.com
```

**Options:**
- `-o, --output` - Output directory (default: `./output`)
- `-n, --name` - Project name (default: domain name)
- `-m, --mode` - Clone mode: `full` or `shallow` (default: `full`)
- `--no-download-assets` - Skip downloading images/fonts

**Clone Modes:**
- `full` - Extracts actual CSS files, preserves media queries, hover states, and animations
- `shallow` - Extracts computed styles (faster but loses responsive design)

**Example:**
```bash
# High-fidelity clone (recommended)
python -m website_cloner https://www.apple.com --mode full

# Quick clone with computed styles
python -m website_cloner https://www.apple.com --mode shallow
```

Then run the cloned site:

```bash
cd output/www-apple-com
npm install
npm run dev
```

Open http://localhost:5173 to view the replica.

**What it clones:**
- HTML structure with proper JSX conversion
- CSS stylesheets (media queries, hover states, animations)
- Images and fonts (downloaded locally)
- srcset responsive images
- Mock interactions (buttons log to console, forms show alerts)

### Comparison Video Recording

Record videos comparing cloned and original sites:

```bash
python compare_sites.py
```

**Options:**
- `--clone-url URL` - URL of cloned site (default: http://localhost:5173)
- `--original-url URL` - URL of original site (default: https://www.apple.com)
- `-o, --output DIR` - Output directory (default: ./videos/comparison)
- `--headless` - Run browser in headless mode
- `--no-scroll` - Disable scrolling during recording
- `--clone-only` - Only record the cloned site
- `--original-only` - Only record the original site

**Example:**
```bash
# Record both sites
python compare_sites.py

# Custom URLs
python compare_sites.py --clone-url http://localhost:5175 --original-url https://www.apple.com

# Headless mode
python compare_sites.py --headless
```

**Output:**
- `cloned-site.webm` - Video with scrolling
- `cloned-site.png` - Full-page screenshot
- `original-site.webm` - Video with scrolling
- `original-site.png` - Full-page screenshot

### Browser Recording Demo

```bash
python demo_browser.py
```

This will:
1. Launch a visible Chromium browser
2. Navigate to example.com and news.ycombinator.com
3. Capture a screenshot (`last-page.png`)
4. Save the session recording to `videos/`

## Output

- `videos/` - Recorded browser session videos
- `videos/comparison/` - Comparison videos (cloned vs original)
- `output/` - Generated React projects from website cloner

## Project Structure

```
browser-use-demo/
├── website_cloner/          # Website cloning module
│   ├── extractor/           # Page and CSS extraction
│   ├── transformer/         # HTML to JSX conversion
│   └── generator/           # React project generation
├── compare_sites.py         # Comparison video recorder
├── demo_browser.py          # Browser recording demo
└── output/                  # Generated cloned sites
```
