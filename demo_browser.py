# save as record_browser_session.py
from pathlib import Path
from playwright.sync_api import sync_playwright

VIDEO_DIR = Path("videos")
VIDEO_DIR.mkdir(exist_ok=True)

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)

        # Enable video recording for everything in this browser context
        context = browser.new_context(
            record_video_dir=str(VIDEO_DIR),
            record_video_size={"width": 1280, "height": 720},
        )

        page = context.new_page()

        # Example automated steps
        page.goto("https://example.com")
        page.wait_for_timeout(2000)

        page.goto("https://news.ycombinator.com")
        page.wait_for_timeout(3000)

        # Optional screenshot too
        page.screenshot(path="last-page.png", full_page=True)

        # Important: close context so Playwright actually writes the video file
        context.close()
        browser.close()

        print(f"Done. Check video files in: {VIDEO_DIR.resolve()}")

if __name__ == "__main__":
    main()
