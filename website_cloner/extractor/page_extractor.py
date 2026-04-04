"""Page extraction using Playwright."""
from pathlib import Path
from urllib.parse import urljoin, urlparse
import requests
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

from .css_extractor import CSSExtractor


class ExtractionError(Exception):
    """Raised when page extraction fails."""
    pass


class PageExtractor:
    """Extract page content, styles, and assets using Playwright."""

    def __init__(self, url: str, output_dir: Path, mode: str = 'full'):
        self.url = url
        self.output_dir = output_dir
        self.assets_dir = output_dir / 'public' / 'assets'
        self.mode = mode  # 'full' or 'shallow'

    def extract(self) -> dict:
        """
        Extract page content and return structured data.

        Returns:
            dict with keys: html, computed_styles, assets, title

        Raises:
            ExtractionError: If page cannot be loaded or parsed
        """
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                viewport={'width': 1920, 'height': 1080}
            )
            page = context.new_page()

            print(f"Loading {self.url}...")
            try:
                response = page.goto(self.url, wait_until='networkidle', timeout=30000)
                if response and response.status >= 400:
                    raise ExtractionError(f"HTTP {response.status}: Failed to load {self.url}")
                page.wait_for_load_state('networkidle', timeout=30000)

                # Scroll through page to trigger lazy loading
                print("Triggering lazy-loaded images...")
                self._scroll_page(page)
                page.wait_for_load_state('networkidle', timeout=10000)
            except PlaywrightTimeout:
                context.close()
                browser.close()
                raise ExtractionError(f"Timeout loading {self.url}")
            except Exception as e:
                context.close()
                browser.close()
                raise ExtractionError(f"Failed to load {self.url}: {e}")

            # Extract title
            title = page.title()

            if self.mode == 'full':
                # Full mode: Extract actual CSS files
                print("Extracting stylesheets...")
                css_extractor = CSSExtractor(self.url, self.assets_dir)
                stylesheets = css_extractor.extract_stylesheets(page)
                css_content = css_extractor.combine_and_process(stylesheets)
                assets = css_extractor.get_url_mapping()

                # Get HTML without modifying it
                html = page.content()

                # Download remaining images
                print("Downloading images...")
                image_assets = self._extract_and_download_assets(page)
                assets.update(image_assets)

                context.close()
                browser.close()

                return {
                    'html': html,
                    'css': css_content,
                    'assets': assets,
                    'title': title,
                    'url': self.url,
                    'mode': 'full'
                }
            else:
                # Shallow mode: Extract computed styles (original behavior)
                print("Extracting computed styles...")
                styles = self._extract_computed_styles(page)

                # Get modified HTML (with data-clone-id attributes)
                html = page.content()

                # Extract and download assets
                print("Downloading assets...")
                assets = self._extract_and_download_assets(page)

                context.close()
                browser.close()

                return {
                    'html': html,
                    'computed_styles': styles,
                    'assets': assets,
                    'title': title,
                    'url': self.url,
                    'mode': 'shallow'
                }

    def _scroll_page(self, page):
        """Scroll through the page to trigger lazy loading."""
        page.evaluate('''async () => {
            const delay = ms => new Promise(resolve => setTimeout(resolve, ms));
            const scrollHeight = document.body.scrollHeight;
            const viewportHeight = window.innerHeight;

            // Scroll down in increments
            for (let y = 0; y < scrollHeight; y += viewportHeight * 0.8) {
                window.scrollTo(0, y);
                await delay(100);
            }

            // Scroll to bottom
            window.scrollTo(0, scrollHeight);
            await delay(300);

            // Scroll back to top
            window.scrollTo(0, 0);
            await delay(100);
        }''')

    def _extract_computed_styles(self, page) -> dict:
        """Extract computed styles for all visible elements."""
        return page.evaluate('''() => {
            const allElements = document.body.querySelectorAll('*');
            const stylesMap = {};
            const relevantProps = [
                'display', 'position', 'width', 'height', 'max-width', 'max-height',
                'min-width', 'min-height', 'margin', 'margin-top', 'margin-right',
                'margin-bottom', 'margin-left', 'padding', 'padding-top',
                'padding-right', 'padding-bottom', 'padding-left',
                'background', 'background-color', 'background-image',
                'color', 'font-family', 'font-size', 'font-weight', 'line-height',
                'text-align', 'text-decoration', 'letter-spacing',
                'border', 'border-width', 'border-style', 'border-color',
                'border-radius', 'box-shadow', 'opacity',
                'flex', 'flex-direction', 'flex-wrap', 'justify-content',
                'align-items', 'align-content', 'gap',
                'grid-template-columns', 'grid-template-rows', 'grid-gap',
                'overflow', 'z-index', 'cursor'
            ];

            const defaultValues = {
                'display': 'block',
                'position': 'static',
                'background-color': 'rgba(0, 0, 0, 0)',
                'color': 'rgb(0, 0, 0)',
                'opacity': '1'
            };

            allElements.forEach((el, index) => {
                // Skip script, style, and invisible elements
                if (el.tagName === 'SCRIPT' || el.tagName === 'STYLE' ||
                    el.tagName === 'NOSCRIPT' || el.tagName === 'HEAD') {
                    return;
                }

                const rect = el.getBoundingClientRect();
                if (rect.width === 0 && rect.height === 0) {
                    return;
                }

                el.setAttribute('data-clone-id', `el-${index}`);

                const computed = window.getComputedStyle(el);
                const styles = {};

                relevantProps.forEach(prop => {
                    const value = computed.getPropertyValue(prop);
                    const defaultVal = defaultValues[prop];

                    if (value && value !== 'none' && value !== 'normal' &&
                        value !== 'auto' && value !== '0px' && value !== defaultVal) {
                        styles[prop] = value;
                    }
                });

                if (Object.keys(styles).length > 0) {
                    stylesMap[`el-${index}`] = styles;
                }
            });

            return stylesMap;
        }''')

    def _extract_and_download_assets(self, page) -> dict:
        """Extract and download images and other assets."""
        self.assets_dir.mkdir(parents=True, exist_ok=True)
        url_mapping = {}

        # Extract image sources (src, srcset, data-src)
        images = page.evaluate('''() => {
            const images = [];

            // Helper to parse srcset and extract URLs
            function parseSrcset(srcset) {
                if (!srcset) return [];
                return srcset.split(',').map(entry => {
                    const parts = entry.trim().split(/\\s+/);
                    return parts[0]; // URL is always first
                }).filter(url => url && !url.startsWith('data:'));
            }

            // Get img src and srcset
            document.querySelectorAll('img').forEach(img => {
                if (img.src && !img.src.startsWith('data:')) {
                    images.push(img.src);
                }
                // srcset contains multiple URLs with size descriptors
                if (img.srcset) {
                    parseSrcset(img.srcset).forEach(url => images.push(url));
                }
                // Lazy loading attributes
                if (img.dataset.src && !img.dataset.src.startsWith('data:')) {
                    images.push(img.dataset.src);
                }
                if (img.dataset.srcset) {
                    parseSrcset(img.dataset.srcset).forEach(url => images.push(url));
                }
            });

            // Get source elements (inside picture/video)
            document.querySelectorAll('source').forEach(source => {
                if (source.src && !source.src.startsWith('data:')) {
                    images.push(source.src);
                }
                if (source.srcset) {
                    parseSrcset(source.srcset).forEach(url => images.push(url));
                }
                // Lazy loading data attributes on source elements
                if (source.dataset.srcset) {
                    parseSrcset(source.dataset.srcset).forEach(url => images.push(url));
                }
            });

            // Check for any element with common lazy-loading data attributes
            document.querySelectorAll('[data-lazy-src], [data-original], [data-bg]').forEach(el => {
                const lazySrc = el.dataset.lazySrc || el.dataset.original || el.dataset.bg;
                if (lazySrc && !lazySrc.startsWith('data:')) {
                    images.push(lazySrc);
                }
            });

            // Get video poster images
            document.querySelectorAll('video').forEach(video => {
                if (video.poster && !video.poster.startsWith('data:')) {
                    images.push(video.poster);
                }
            });

            return images;
        }''')

        # Extract background images
        bg_images = page.evaluate('''() => {
            const images = [];
            document.querySelectorAll('*').forEach(el => {
                const bg = window.getComputedStyle(el).backgroundImage;
                if (bg && bg !== 'none') {
                    const matches = bg.match(/url\\(["']?([^"')]+)["']?\\)/g);
                    if (matches) {
                        matches.forEach(match => {
                            const url = match.replace(/url\\(["']?|["']?\\)/g, '');
                            if (!url.startsWith('data:')) {
                                images.push(url);
                            }
                        });
                    }
                }
            });
            return images;
        }''')

        all_assets = list(set(images + bg_images))

        for asset_url in all_assets:
            local_path = self._download_asset(asset_url)
            if local_path:
                url_mapping[asset_url] = local_path

        return url_mapping

    def _download_asset(self, url: str) -> str | None:
        """Download an asset and return its local path."""
        try:
            full_url = urljoin(self.url, url)
            response = requests.get(full_url, timeout=10, headers={
                'User-Agent': 'Mozilla/5.0 (compatible; WebsiteCloner/1.0)'
            })
            response.raise_for_status()

            # Generate safe filename
            parsed = urlparse(url)
            filename = Path(parsed.path).name or 'asset'
            if not filename or filename == '/':
                filename = f'asset_{hash(url) % 10000}'

            # Ensure unique filename
            filepath = self.assets_dir / filename
            counter = 1
            while filepath.exists():
                name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
                filepath = self.assets_dir / f"{name}_{counter}.{ext}" if ext else self.assets_dir / f"{name}_{counter}"
                counter += 1

            filepath.write_bytes(response.content)
            return f'/assets/{filepath.name}'

        except Exception as e:
            print(f"  Warning: Failed to download {url}: {e}")
            return None
