"""Serve the compiled application and explain an incomplete local setup."""
from pathlib import Path
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException


class FrontendFiles(StaticFiles):
    def __init__(self, directory: Path):
        self.build_directory = directory
        super().__init__(directory=str(directory), html=True, check_dir=False)

    async def check_config(self):
        # A missing build is handled with actionable HTML, rather than a server error.
        pass

    async def get_response(self, path, scope):
        clean = path.replace('\\', '/').lstrip('/')
        if clean == 'api' or clean.startswith('api/'):
            return JSONResponse({'detail': 'Not Found'}, status_code=404)
        index = self.build_directory / 'index.html'
        if not index.is_file():
            if clean in ('', '.', 'index.html') or not Path(clean).suffix:
                return HTMLResponse('''<!doctype html><html><head><meta charset="utf-8"><title>CivicFlux setup needed</title></head>
<body style="font:18px system-ui;max-width:800px;margin:80px auto;padding:24px">
<h1>CivicFlux is running. The website needs to be built.</h1>
<p>Stop this server with Ctrl+C. From the extracted project folder:</p>
<p><b>Windows:</b> double-click <code>START-CIVICFLUX.cmd</code>.<br>
<b>macOS:</b> run <code>bash scripts/start_mac.sh</code>.</p>
<p>The launcher installs dependencies and builds the website. Open the address printed by that launcher.</p>
<p>For development, start both documented servers and open <code>http://127.0.0.1:5173/</code>.</p>
</body></html>''', status_code=503)
            return JSONResponse({'detail': 'Not Found'}, status_code=404)
        try:
            return await super().get_response(path, scope)
        except HTTPException as exc:
            # Client-side navigation can be opened directly; missing asset/API paths stay 404.
            if exc.status_code == 404 and not Path(clean).suffix and not clean.startswith('assets/') and '..' not in Path(clean).parts:
                return FileResponse(index)
            raise
