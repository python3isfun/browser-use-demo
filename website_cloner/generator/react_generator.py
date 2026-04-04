"""React/Vite project generator."""
import json
import re
import shutil
from pathlib import Path


class ReactGenerator:
    """Generate a Vite React project from extracted content."""

    def __init__(self, project_name: str, output_dir: Path):
        self.project_name = self._sanitize_project_name(project_name)
        self.project_path = output_dir / self.project_name

    @staticmethod
    def _sanitize_project_name(name: str) -> str:
        """Sanitize project name for npm compatibility."""
        # npm package names must be lowercase, no spaces, limited special chars
        name = name.lower()
        name = re.sub(r'[^a-z0-9\-_]', '-', name)
        name = re.sub(r'-+', '-', name)  # collapse multiple dashes
        name = name.strip('-')
        return name or 'cloned-site'

    @staticmethod
    def _escape_html(text: str) -> str:
        """Escape HTML special characters."""
        return (text
                .replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('"', '&quot;'))

    def generate(self, jsx_content: str, title: str, assets_dir: Path = None) -> Path:
        """Generate the complete Vite React project."""
        print(f"Generating React project: {self.project_name}")

        # Create project structure
        self.project_path.mkdir(parents=True, exist_ok=True)
        src_dir = self.project_path / 'src'
        src_dir.mkdir(exist_ok=True)
        public_dir = self.project_path / 'public'
        public_dir.mkdir(exist_ok=True)

        # Generate files
        self._write_package_json()
        self._write_vite_config()
        self._write_index_html(title)
        self._write_main_jsx()
        self._write_cloned_page(jsx_content)
        self._write_app_css()

        # Copy assets if provided
        if assets_dir and assets_dir.exists():
            self._copy_assets(assets_dir, public_dir)

        print(f"Project generated at: {self.project_path}")
        return self.project_path

    def _write_package_json(self):
        """Write package.json file."""
        package = {
            "name": self.project_name,
            "private": True,
            "version": "0.0.1",
            "type": "module",
            "scripts": {
                "dev": "vite",
                "build": "vite build",
                "preview": "vite preview"
            },
            "dependencies": {
                "react": "^18.2.0",
                "react-dom": "^18.2.0"
            },
            "devDependencies": {
                "@vitejs/plugin-react": "^4.2.0",
                "vite": "^5.0.0"
            }
        }
        (self.project_path / 'package.json').write_text(
            json.dumps(package, indent=2)
        )

    def _write_vite_config(self):
        """Write vite.config.js file."""
        config = '''import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
})
'''
        (self.project_path / 'vite.config.js').write_text(config)

    def _write_index_html(self, title: str):
        """Write index.html file."""
        safe_title = self._escape_html(title)
        html = f'''<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>{safe_title} (Clone)</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.jsx"></script>
  </body>
</html>
'''
        (self.project_path / 'index.html').write_text(html)

    def _write_main_jsx(self):
        """Write src/main.jsx entry point."""
        main = '''import React from 'react'
import ReactDOM from 'react-dom/client'
import ClonedPage from './ClonedPage.jsx'
import './App.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <ClonedPage />
  </React.StrictMode>,
)
'''
        (self.project_path / 'src' / 'main.jsx').write_text(main)

    def _write_cloned_page(self, jsx_content: str):
        """Write src/ClonedPage.jsx component."""
        component = f'''import React from 'react';

function ClonedPage() {{
  return (
    <div className="cloned-page">
      {jsx_content}
    </div>
  );
}}

export default ClonedPage;
'''
        (self.project_path / 'src' / 'ClonedPage.jsx').write_text(component)

    def _write_app_css(self):
        """Write src/App.css with base reset styles."""
        css = '''/* Base reset for cloned page */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  line-height: 1.5;
}

.cloned-page {
  width: 100%;
  min-height: 100vh;
}

/* Mock interaction styles */
button:active {
  transform: scale(0.98);
  opacity: 0.9;
}

a {
  cursor: pointer;
}

input:focus, textarea:focus {
  outline: 2px solid #0066cc;
  outline-offset: 2px;
}
'''
        (self.project_path / 'src' / 'App.css').write_text(css)

    def _copy_assets(self, source_dir: Path, dest_dir: Path):
        """Copy downloaded assets to public folder."""
        assets_dest = dest_dir / 'assets'

        # Check if source actually has files
        if not source_dir.exists():
            return

        files = list(source_dir.iterdir()) if source_dir.is_dir() else []
        if not files:
            return

        # If source and dest are the same, no need to copy
        if source_dir.resolve() == assets_dest.resolve():
            print(f"Assets already in place at {assets_dest}")
            return

        if assets_dest.exists():
            shutil.rmtree(assets_dest)
        shutil.copytree(source_dir, assets_dest)
        print(f"Copied {len(files)} assets to {assets_dest}")
