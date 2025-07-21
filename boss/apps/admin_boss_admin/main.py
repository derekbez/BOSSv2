"""
Mini-app: Admin BOSS Admin
Provides a web interface for full administrative control over BOSS.
Entry point: run(stop_event, api)
"""
import json
import subprocess
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from threading import Event
from typing import Any

WEB_PORT = 8080

# Global reference to API for handler access
api_ref = None


class AdminHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            html = """
            <!DOCTYPE html>
            <html><head><title>BOSS Admin Panel</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; background-color: #f5f5f5; }
                .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                h1 { color: #333; text-align: center; margin-bottom: 30px; }
                .section { margin: 20px 0; }
                .section h2 { color: #555; border-bottom: 2px solid #ddd; padding-bottom: 10px; }
                ul { list-style-type: none; padding: 0; }
                li { margin: 10px 0; }
                a { text-decoration: none; color: #0066cc; padding: 12px; display: block; border: 1px solid #ddd; border-radius: 4px; transition: all 0.3s; }
                a:hover { background-color: #f0f8ff; border-color: #0066cc; }
                .icon { font-size: 1.2em; margin-right: 8px; }
                .status { background: #e8f5e8; padding: 15px; border-radius: 4px; margin: 15px 0; }
            </style>
            </head><body>
            <div class="container">
                <h1>🔧 BOSS Administrative Control Panel</h1>
                
                <div class="section">
                    <h2>📊 System Information</h2>
                    <ul>
                        <li><a href='/status'><span class="icon">📈</span>System Status & Health</a></li>
                        <li><a href='/logs'><span class="icon">📝</span>View System Logs</a></li>
                    </ul>
                </div>
                
                <div class="section">
                    <h2>📱 Application Management</h2>
                    <ul>
                        <li><a href='/apps'><span class="icon">📱</span>List All Mini-Apps</a></li>
                        <li><a href='/mappings'><span class="icon">🔗</span>View App Number Mappings</a></li>
                        <li><a href='/unassigned'><span class="icon">📋</span>Show Unassigned Apps</a></li>
                    </ul>
                </div>
                
                <div class="section">
                    <h2>� System Maintenance</h2>
                    <ul>
                        <li><a href='/update'><span class="icon">⬇️</span>Software Update (git pull)</a></li>
                    </ul>
                </div>
                
                <div class="status">
                    <strong>⚠️ Administrative Interface</strong><br>
                    Use with caution. Changes made here affect the entire BOSS system.
                </div>
            </div>
            </body></html>
            """
            self.wfile.write(html.encode('utf-8'))
            
        elif self.path == '/apps':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            try:
                # Get apps directory relative to this file
                apps_dir = Path(__file__).parent.parent
                all_apps = []
                
                for app_dir in apps_dir.iterdir():
                    if app_dir.is_dir() and not app_dir.name.startswith('__'):
                        manifest_file = app_dir / 'manifest.json'
                        app_info = {'name': app_dir.name, 'path': str(app_dir)}
                        
                        if manifest_file.exists():
                            try:
                                with open(manifest_file, 'r') as f:
                                    manifest = json.load(f)
                                app_info['manifest'] = manifest
                            except Exception as e:
                                app_info['manifest_error'] = str(e)
                        else:
                            app_info['manifest_error'] = 'No manifest found'
                            
                        all_apps.append(app_info)
                
                self.wfile.write(json.dumps({'apps': all_apps}, indent=2).encode('utf-8'))
            except Exception as e:
                self.wfile.write(json.dumps({'error': str(e)}).encode('utf-8'))
                if api_ref:
                    api_ref.logger.error(f"Admin apps endpoint error: {e}")
                
        elif self.path == '/mappings':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            try:
                # Look for app_mappings.json in config directory
                config_path = Path(__file__).parent.parent.parent.parent / 'config' / 'app_mappings.json'
                if config_path.exists():
                    with open(config_path, 'r') as f:
                        mappings = json.load(f)
                    self.wfile.write(json.dumps({'mappings': mappings}, indent=2).encode('utf-8'))
                else:
                    self.wfile.write(json.dumps({'error': 'app_mappings.json not found'}).encode('utf-8'))
            except Exception as e:
                self.wfile.write(json.dumps({'error': str(e)}).encode('utf-8'))
                if api_ref:
                    api_ref.logger.error(f"Admin mappings endpoint error: {e}")
                
        elif self.path == '/unassigned':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            try:
                apps_dir = Path(__file__).parent.parent
                config_path = Path(__file__).parent.parent.parent.parent / 'config' / 'app_mappings.json'
                
                if config_path.exists():
                    with open(config_path, 'r') as f:
                        mappings = json.load(f)
                    assigned = set(mappings.values())
                else:
                    assigned = set()
                
                all_apps = [d.name for d in apps_dir.iterdir() if d.is_dir() and not d.name.startswith('__')]
                unassigned = [a for a in all_apps if a not in assigned]
                
                self.wfile.write(json.dumps({'unassigned': unassigned}, indent=2).encode('utf-8'))
            except Exception as e:
                self.wfile.write(json.dumps({'error': str(e)}).encode('utf-8'))
                if api_ref:
                    api_ref.logger.error(f"Admin unassigned endpoint error: {e}")
                
        elif self.path == '/status':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            try:
                status = {
                    'boss_running': True,
                    'api_available': api_ref is not None,
                    'current_app': 'admin_boss_admin',
                    'timestamp': time.time(),
                    'web_port': WEB_PORT
                }
                self.wfile.write(json.dumps(status, indent=2).encode('utf-8'))
            except Exception as e:
                self.wfile.write(json.dumps({'error': str(e)}).encode('utf-8'))
                if api_ref:
                    api_ref.logger.error(f"Admin status endpoint error: {e}")
                
        elif self.path == '/logs':
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            try:
                # Try to read recent log entries
                log_path = Path(__file__).parent.parent.parent / 'logs' / 'boss.log'
                if log_path.exists():
                    # Read last 100 lines
                    with open(log_path, 'r') as f:
                        lines = f.readlines()
                    recent_lines = lines[-100:] if len(lines) > 100 else lines
                    self.wfile.write(''.join(recent_lines).encode('utf-8'))
                else:
                    self.wfile.write(b'Log file not found')
            except Exception as e:
                self.wfile.write(f'Error reading logs: {e}'.encode('utf-8'))
                if api_ref:
                    api_ref.logger.error(f"Admin logs endpoint error: {e}")
                
        elif self.path == '/update':
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            try:
                # Change to project root directory
                project_root = Path(__file__).parent.parent.parent.parent
                result = subprocess.run(['git', 'pull'], 
                                      cwd=project_root, 
                                      capture_output=True, 
                                      text=True, 
                                      timeout=30)
                
                output = f"Git Pull Results:\n"
                output += f"Return Code: {result.returncode}\n"
                output += f"STDOUT:\n{result.stdout}\n"
                if result.stderr:
                    output += f"STDERR:\n{result.stderr}\n"
                
                self.wfile.write(output.encode('utf-8'))
                if api_ref:
                    api_ref.logger.info(f"Git pull executed via admin interface, return code: {result.returncode}")
            except Exception as e:
                error_msg = f'Update error: {e}'
                self.wfile.write(error_msg.encode('utf-8'))
                if api_ref:
                    api_ref.logger.error(f"Admin update endpoint error: {e}")
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'404 - Not Found')

    def log_message(self, format, *args):
        # Suppress default HTTP server logging to avoid spam
        pass

def run(stop_event: Event, api: Any) -> None:
    """
    Starts admin web server and exposes management features.
    Args:
        stop_event (Event): Event to signal app termination.
        api (object): Provided API for hardware/display access.
    """
    global api_ref
    api_ref = api
    
    try:
        # Get IP address for display
        result = subprocess.run(['hostname', '-I'], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            ip = result.stdout.strip().split()[0]
        else:
            ip = "localhost"
    except:
        ip = "localhost"
    
    # Display connection info
    api.screen.clear()
    api.screen.add_text("BOSS Admin Panel", x=10, y=50, size=24, color="white")
    api.screen.add_text(f"Web Interface:", x=10, y=100, size=18, color="yellow")
    api.screen.add_text(f"http://{ip}:{WEB_PORT}", x=10, y=130, size=16, color="cyan")
    api.screen.add_text("Press any button to exit", x=10, y=200, size=14, color="gray")
    api.screen.refresh()
    
    # Light up green LED to indicate admin mode
    api.set_leds(green=True)
    
    api.logger.info(f"Starting BOSS Admin web interface on port {WEB_PORT}")
    
    # Start HTTP server
    server = HTTPServer(("0.0.0.0", WEB_PORT), AdminHandler)
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    
    try:
        # Main loop - wait for stop event
        while not stop_event.is_set():
            stop_event.wait(0.1)
    except Exception as e:
        api.logger.error(f"Admin app error: {e}")
    finally:
        # Cleanup
        server.shutdown()
        api.screen.clear()
        api.screen.add_text("Admin panel stopped", x=10, y=100, size=20, color="white")
        api.screen.refresh()
        api.set_leds()  # Turn off all LEDs
        api.logger.info("BOSS Admin web interface stopped")
        
        # Clear global reference
        api_ref = None
