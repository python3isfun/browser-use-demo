#!/usr/bin/env python3
"""Record comparison videos between cloned and original websites."""

import argparse
from pathlib import Path
from playwright.sync_api import sync_playwright


def record_site(url: str, name: str, output_dir: Path, scroll: bool = True, headless: bool = False):
    """Record a video of a website with scrolling."""
    output_dir.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context(
            record_video_dir=str(output_dir),
            record_video_size={'width': 1920, 'height': 1080},
            viewport={'width': 1920, 'height': 1080}
        )
        page = context.new_page()

        print(f'Recording {name} from {url}...')
        page.goto(url, wait_until='networkidle', timeout=30000)
        page.wait_for_timeout(2000)

        if scroll:
            # Scroll through the page smoothly
            scroll_height = page.evaluate('document.body.scrollHeight')
            viewport_height = 1080
            scroll_position = 0

            while scroll_position < scroll_height:
                page.mouse.wheel(0, 400)
                scroll_position += 400
                page.wait_for_timeout(500)

            # Pause at bottom
            page.wait_for_timeout(1000)

            # Scroll back to top
            page.evaluate('window.scrollTo({top: 0, behavior: "smooth"})')
            page.wait_for_timeout(1500)

        # Take full-page screenshot
        screenshot_path = output_dir / f'{name}.png'
        page.screenshot(path=str(screenshot_path), full_page=True)
        print(f'  Screenshot saved: {screenshot_path}')

        # Close to finalize video
        context.close()
        browser.close()

        # Rename video file
        video_files = list(output_dir.glob('*.webm'))
        for vf in video_files:
            if vf.name != f'{name}.webm':
                new_path = output_dir / f'{name}.webm'
                if new_path.exists():
                    new_path.unlink()
                vf.rename(new_path)
                print(f'  Video saved: {new_path}')
                break

        print(f'Done recording {name}')


def main():
    parser = argparse.ArgumentParser(description='Record comparison videos of websites')
    parser.add_argument('--clone-url', default='http://localhost:5173',
                        help='URL of the cloned site (default: http://localhost:5173)')
    parser.add_argument('--original-url', default='https://www.apple.com',
                        help='URL of the original site (default: https://www.apple.com)')
    parser.add_argument('--output', '-o', default='./videos/comparison',
                        help='Output directory for videos (default: ./videos/comparison)')
    parser.add_argument('--headless', action='store_true',
                        help='Run browser in headless mode')
    parser.add_argument('--no-scroll', action='store_true',
                        help='Disable scrolling during recording')
    parser.add_argument('--clone-only', action='store_true',
                        help='Only record the cloned site')
    parser.add_argument('--original-only', action='store_true',
                        help='Only record the original site')

    args = parser.parse_args()
    output_dir = Path(args.output).resolve()
    scroll = not args.no_scroll

    print(f'Output directory: {output_dir}')
    print()

    if not args.original_only:
        record_site(args.clone_url, 'cloned-site', output_dir, scroll=scroll, headless=args.headless)
        print()

    if not args.clone_only:
        record_site(args.original_url, 'original-site', output_dir, scroll=scroll, headless=args.headless)
        print()

    print('=' * 50)
    print('Comparison recording complete!')
    print('=' * 50)
    print(f'\nFiles saved to: {output_dir}')
    print('\nTo view:')
    print(f'  open {output_dir}')


if __name__ == '__main__':
    main()
