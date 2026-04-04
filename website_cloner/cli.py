"""Command-line interface for website cloner."""
import sys
import click
from pathlib import Path
from urllib.parse import urlparse

from .extractor import PageExtractor
from .extractor.page_extractor import ExtractionError
from .transformer import HTMLToJSXConverter
from .generator import ReactGenerator


def validate_url(url: str) -> bool:
    """Validate that URL has proper scheme and netloc."""
    parsed = urlparse(url)
    return parsed.scheme in ('http', 'https') and bool(parsed.netloc)


@click.command()
@click.argument('url')
@click.option('--output', '-o', default='./output',
              help='Output directory for the React project')
@click.option('--name', '-n', default=None,
              help='Name of the generated project (defaults to domain name)')
@click.option('--mode', '-m', type=click.Choice(['full', 'shallow']), default='full',
              help='Clone mode: full (extract CSS) or shallow (computed styles)')
@click.option('--download-assets/--no-download-assets', default=True,
              help='Download images and fonts locally')
def clone(url: str, output: str, name: str, mode: str, download_assets: bool):
    """
    Clone a website and generate a React application.

    URL: The website URL to clone (e.g., https://example.com)

    Examples:
        python -m website_cloner https://example.com
        python -m website_cloner https://example.com --mode full
        python -m website_cloner https://example.com --mode shallow -o ./output
    """
    # Validate URL
    if not validate_url(url):
        click.echo(f"Error: Invalid URL '{url}'. Must start with http:// or https://", err=True)
        sys.exit(1)

    output_dir = Path(output).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate project name from domain if not specified
    if not name:
        parsed = urlparse(url)
        name = parsed.netloc.replace('.', '-').replace(':', '-') or 'cloned-site'

    click.echo(f"Cloning {url}...")
    click.echo(f"Mode: {mode}")
    click.echo(f"Output: {output_dir / name}")
    click.echo()

    # Phase 1: Extract
    click.echo("[1/3] Extracting page content...")
    try:
        extractor = PageExtractor(url, output_dir / name, mode=mode)
        page_data = extractor.extract()
    except ExtractionError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

    click.echo(f"  - Title: {page_data['title']}")
    if mode == 'full':
        css_size = len(page_data.get('css', '')) / 1024
        click.echo(f"  - CSS extracted: {css_size:.1f} KB")
    else:
        click.echo(f"  - Styles extracted for {len(page_data.get('computed_styles', {}))} elements")
    click.echo(f"  - Downloaded {len(page_data['assets'])} assets")

    # Phase 2: Transform
    click.echo("[2/3] Converting to JSX...")
    converter = HTMLToJSXConverter(mode=mode)
    if mode == 'full':
        jsx_content = converter.convert(
            page_data['html'],
            assets_map=page_data['assets'] if download_assets else {}
        )
    else:
        jsx_content = converter.convert(
            page_data['html'],
            page_data['computed_styles'],
            page_data['assets'] if download_assets else {}
        )
    click.echo("  - JSX conversion complete")

    # Phase 3: Generate
    click.echo("[3/3] Generating React project...")
    generator = ReactGenerator(name, output_dir)
    assets_dir = output_dir / name / 'public' / 'assets'
    project_path = generator.generate(
        jsx_content,
        page_data['title'],
        assets_dir if download_assets else None,
        css_content=page_data.get('css'),
        mode=mode
    )

    click.echo()
    click.echo("=" * 50)
    click.echo("Done! Your cloned site is ready.")
    click.echo("=" * 50)
    click.echo()
    click.echo("To run the cloned site:")
    click.echo(f"  cd {project_path}")
    click.echo("  npm install")
    click.echo("  npm run dev")
    click.echo()
    click.echo("Then open http://localhost:5173 in your browser.")


if __name__ == '__main__':
    clone()
