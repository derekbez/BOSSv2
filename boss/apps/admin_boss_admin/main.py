"""
Mini-app: Admin BOSS Admin
Provides a web interface for full administrative control over BOSS.
Entry point: run(stop_event, api)
"""
import os
import threading
from threading import Event
from typing import Any
from http.server import BaseHTTPRequestHandler, HTTPServer
import json

WEB_PORT = 8080

class AdminHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            html = """
            <html><head><title>BOSS Admin</title></head><body>
            <h2>BOSS Admin Panel</h2>
            <ul>
                <li><a href='/apps'>List All Mini-Apps</a></li>
                <li><a href='/assign'>Assign Mini-App to Number</a></li>
                <li><a href='/unassigned'>Show Unassigned Apps</a></li>
                <li><a href='/edit_manifest'>Edit Manifest File</a></li>
                <li><a href='/edit_config'>Edit Config File</a></li>
                <li><a href='/assets'>Browse Assets Directory</a></li>
                <li><a href='/upload'>Upload Asset</a></li>
                <li><a href='/download'>Download Asset</a></li>
                <li><a href='/update'>Software Update (git pull)</a></li>
            </ul>
            </body></html>
            """
            self.wfile.write(html.encode('utf-8'))
        elif self.path == '/apps':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            try:
                with open(os.path.join(os.path.dirname(__file__), '../../config/BOSSsettings.json'), 'r', encoding='utf-8') as f:
                    config = json.load(f)
                self.wfile.write(json.dumps(config.get('app_mappings', {}), indent=2).encode('utf-8'))
            except Exception as e:
                self.wfile.write(json.dumps({'error': str(e)}).encode('utf-8'))
        elif self.path == '/unassigned':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            try:
                apps_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
                with open(os.path.join(os.path.dirname(__file__), '../../config/BOSSsettings.json'), 'r', encoding='utf-8') as f:
                    config = json.load(f)
                assigned = set(config.get('app_mappings', {}).values())
                all_apps = [d for d in os.listdir(apps_dir) if os.path.isdir(os.path.join(apps_dir, d)) and not d.startswith('__')]
                unassigned = [a for a in all_apps if a not in assigned]
                self.wfile.write(json.dumps({'unassigned': unassigned}, indent=2).encode('utf-8'))
            except Exception as e:
                self.wfile.write(json.dumps({'error': str(e)}).encode('utf-8'))
        elif self.path.startswith('/edit_manifest'):
            # Example: /edit_manifest?app=app_name
            from urllib.parse import urlparse, parse_qs
            query = parse_qs(urlparse(self.path).query)
            app = query.get('app', [''])[0]
            manifest_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', app, 'manifest.json'))
            try:
                with open(manifest_path, 'r', encoding='utf-8') as f:
                    manifest = json.load(f)
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(manifest, indent=2).encode('utf-8'))
            except Exception as e:
                self.send_response(404)
                self.end_headers()
                self.wfile.write(json.dumps({'error': str(e)}).encode('utf-8'))
        elif self.path.startswith('/edit_config'):
            # Example: /edit_config?app=app_name
            from urllib.parse import urlparse, parse_qs
            query = parse_qs(urlparse(self.path).query)
            app = query.get('app', [''])[0]
            config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', app, 'config.json'))
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(config, indent=2).encode('utf-8'))
            except Exception as e:
                self.send_response(404)
                self.end_headers()
                self.wfile.write(json.dumps({'error': str(e)}).encode('utf-8'))
        elif self.path.startswith('/assets'):
            # List files in assets directory for an app: /assets?app=app_name
            from urllib.parse import urlparse, parse_qs
            query = parse_qs(urlparse(self.path).query)
            app = query.get('app', [''])[0]
            assets_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', app, 'assets'))
            try:
                files = os.listdir(assets_path)
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'assets': files}, indent=2).encode('utf-8'))
            except Exception as e:
                self.send_response(404)
                self.end_headers()
                self.wfile.write(json.dumps({'error': str(e)}).encode('utf-8'))
        elif self.path.startswith('/download'):
            # Download asset: /download?app=app_name&file=filename
            from urllib.parse import urlparse, parse_qs
            query = parse_qs(urlparse(self.path).query)
            app = query.get('app', [''])[0]
            filename = query.get('file', [''])[0]
            file_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', app, 'assets', filename))
            try:
                with open(file_path, 'rb') as f:
                    data = f.read()
                self.send_response(200)
                self.send_header('Content-Disposition', f'attachment; filename="{filename}"')
                self.end_headers()
                self.wfile.write(data)
            except Exception as e:
                self.send_response(404)
                self.end_headers()
                self.wfile.write(json.dumps({'error': str(e)}).encode('utf-8'))
        elif self.path == '/update':
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            result = os.popen('git pull').read()
            self.wfile.write(result.encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'Not found')

    def do_POST(self):
        from urllib.parse import parse_qs
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        path = self.path
        if path == '/assign':
            # Assign mini-app to number
            data = parse_qs(post_data.decode('utf-8'))
            number = data.get('number', [''])[0]
            app = data.get('app', [''])[0]
            config_path = os.path.join(os.path.dirname(__file__), '../../config/BOSSsettings.json')
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                config['app_mappings'][number] = app
                with open(config_path, 'w', encoding='utf-8') as f:
                    json.dump(config, f, indent=2)
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b'Assigned successfully')
            except Exception as e:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(json.dumps({'error': str(e)}).encode('utf-8'))
        elif path.startswith('/edit_manifest'):
            # Edit manifest file
            data = parse_qs(post_data.decode('utf-8'))
            app = data.get('app', [''])[0]
            content = data.get('content', [''])[0]
            manifest_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', app, 'manifest.json'))
            try:
                with open(manifest_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b'Manifest updated')
            except Exception as e:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(json.dumps({'error': str(e)}).encode('utf-8'))
        elif path.startswith('/edit_config'):
            # Edit config file
            data = parse_qs(post_data.decode('utf-8'))
            app = data.get('app', [''])[0]
            content = data.get('content', [''])[0]
            config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', app, 'config.json'))
            try:
                with open(config_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b'Config updated')
            except Exception as e:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(json.dumps({'error': str(e)}).encode('utf-8'))
        elif path.startswith('/upload'):
            # Upload asset (simple, expects ?app=app_name&file=filename in POST data, file content in body)
            data = parse_qs(post_data.decode('utf-8'))
            app = data.get('app', [''])[0]
            filename = data.get('file', [''])[0]
            file_content = data.get('content', [''])[0].encode('utf-8')
            assets_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', app, 'assets', filename))
            try:
                with open(assets_path, 'wb') as f:
                    f.write(file_content)
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b'Asset uploaded')
            except Exception as e:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(json.dumps({'error': str(e)}).encode('utf-8'))
        else:
            self.send_response(501)
            self.end_headers()
            self.wfile.write(b'Not implemented')


def run(stop_event: Event, api: Any) -> None:
    """
    Starts admin web server and exposes management features.
    Args:
        stop_event (Event): Event to signal app termination.
        api (object): Provided API for hardware/display access.
    """
    ip = os.popen("hostname -I | awk '{print $1}'").read().strip()
    api.display_text(f"BOSS Admin Web UI:\nhttp://{ip}:{WEB_PORT}")
    # Optionally, light up a LED to indicate admin mode
    if hasattr(api, 'led_on'):
        api.led_on('green')
    server = HTTPServer(("0.0.0.0", WEB_PORT), AdminHandler)
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    try:
        while not stop_event.is_set():
            pass
    finally:
        server.shutdown()
        api.display_text("Admin web server stopped.")
        if hasattr(api, 'led_off'):
            api.led_off('green')
