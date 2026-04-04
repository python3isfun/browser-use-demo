"""CSS extraction and processing."""
import re
from pathlib import Path
from urllib.parse import urljoin, urlparse
import requests


class CSSExtractor:
    """Extract and process CSS from a webpage."""

    def __init__(self, base_url: str, assets_dir: Path):
        self.base_url = base_url
        self.assets_dir = assets_dir
        self.fonts_dir = assets_dir / 'fonts'
        self.url_mapping = {}

    def extract_stylesheets(self, page) -> list[dict]:
        """Extract all stylesheets from the page."""
        stylesheets = []

        # Get linked stylesheets
        links = page.evaluate('''() => {
            const links = [];
            document.querySelectorAll('link[rel="stylesheet"]').forEach(link => {
                if (link.href) {
                    links.push(link.href);
                }
            });
            return links;
        }''')

        for url in links:
            css_content = self._fetch_stylesheet(url)
            if css_content:
                stylesheets.append({
                    'type': 'link',
                    'url': url,
                    'content': css_content
                })

        # Get inline styles
        inline_styles = page.evaluate('''() => {
            const styles = [];
            document.querySelectorAll('style').forEach(style => {
                if (style.textContent) {
                    styles.push(style.textContent);
                }
            });
            return styles;
        }''')

        for content in inline_styles:
            stylesheets.append({
                'type': 'inline',
                'content': content
            })

        return stylesheets

    def _fetch_stylesheet(self, url: str) -> str | None:
        """Fetch a stylesheet from URL."""
        try:
            full_url = urljoin(self.base_url, url)
            response = requests.get(full_url, timeout=15, headers={
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            })
            response.raise_for_status()
            return response.text
        except Exception as e:
            print(f"  Warning: Failed to fetch stylesheet {url}: {e}")
            return None

    def combine_and_process(self, stylesheets: list[dict]) -> str:
        """Combine all stylesheets and process URLs."""
        combined = []

        for sheet in stylesheets:
            content = sheet['content']
            base = sheet.get('url', self.base_url)

            # Process URLs in this stylesheet
            processed = self._process_css_urls(content, base)
            combined.append(f"/* Source: {sheet.get('url', 'inline')} */\n{processed}")

        return '\n\n'.join(combined)

    def _process_css_urls(self, css: str, base_url: str) -> str:
        """Rewrite url() references in CSS to local paths."""
        def replace_url(match):
            url = match.group(1).strip('\'"')

            # Skip data URLs
            if url.startswith('data:'):
                return match.group(0)

            # Download and get local path
            local_path = self._download_css_asset(url, base_url)
            if local_path:
                return f'url("{local_path}")'
            return match.group(0)

        # Match url(...) patterns
        pattern = r'url\(([^)]+)\)'
        return re.sub(pattern, replace_url, css)

    def _download_css_asset(self, url: str, base_url: str) -> str | None:
        """Download a CSS-referenced asset (font, image)."""
        try:
            full_url = urljoin(base_url, url)

            # Check if already downloaded
            if full_url in self.url_mapping:
                return self.url_mapping[full_url]

            response = requests.get(full_url, timeout=15, headers={
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            })
            response.raise_for_status()

            # Determine asset type and directory
            parsed = urlparse(url)
            filename = Path(parsed.path).name or f'asset_{hash(url) % 10000}'

            # Use fonts dir for font files
            ext = Path(filename).suffix.lower()
            if ext in ('.woff', '.woff2', '.ttf', '.otf', '.eot'):
                self.fonts_dir.mkdir(parents=True, exist_ok=True)
                target_dir = self.fonts_dir
                local_prefix = '/assets/fonts'
            else:
                self.assets_dir.mkdir(parents=True, exist_ok=True)
                target_dir = self.assets_dir
                local_prefix = '/assets'

            # Ensure unique filename
            filepath = target_dir / filename
            counter = 1
            while filepath.exists():
                stem = Path(filename).stem
                suffix = Path(filename).suffix
                filepath = target_dir / f"{stem}_{counter}{suffix}"
                counter += 1

            filepath.write_bytes(response.content)
            local_path = f'{local_prefix}/{filepath.name}'
            self.url_mapping[full_url] = local_path
            return local_path

        except Exception as e:
            print(f"  Warning: Failed to download CSS asset {url}: {e}")
            return None

    def get_url_mapping(self) -> dict:
        """Return the URL to local path mapping."""
        return self.url_mapping
