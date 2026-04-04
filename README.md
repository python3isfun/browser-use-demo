# Browser Use Demo

A Python demo showcasing browser automation and video recording using Playwright.

## Features

- Automated browser navigation with Chromium
- Video recording of browser sessions (1280x720)
- Full-page screenshot capture

## Installation

```bash
pip install -r requirements.txt
playwright install chromium
```

## Usage

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
- `last-page.png` - Screenshot of the final page
