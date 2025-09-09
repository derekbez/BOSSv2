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
                /* Slightly smaller text to better match the physical screen */
                body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; font-size: 14px; -webkit-user-select: text; -moz-user-select: text; user-select: text; }
                /* Make the central container scroll when viewport is small */
                .container { max-width: 800px; max-height: 80vh; overflow: auto; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                h1 { color: #333; text-align: center; margin-bottom: 20px; font-size: 1.4em; }
                .section { margin: 16px 0; }
                .section h2 { color: #555; border-bottom: 2px solid #ddd; padding-bottom: 8px; }
                ul { list-style-type: none; padding: 0; }
                li { margin: 8px 0; }
                a { text-decoration: none; color: #0066cc; padding: 10px; display: block; border: 1px solid #ddd; border-radius: 4px; transition: all 0.2s; }
                a:hover { background-color: #f0f8ff; border-color: #0066cc; }
                .icon { font-size: 1.1em; margin-right: 8px; }
                .status { background: #e8f5e8; padding: 12px; border-radius: 4px; margin: 12px 0; }
                /* Make link/button text selectable for copy */
                a, .status, .section { -webkit-user-select: text; -moz-user-select: text; user-select: text; }
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
                    api_ref.log_error(f"Admin apps endpoint error: {e}")
                
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
                    api_ref.log_error(f"Admin mappings endpoint error: {e}")
                
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
                    api_ref.log_error(f"Admin unassigned endpoint error: {e}")
                
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
                    api_ref.log_error(f"Admin status endpoint error: {e}")
                
        elif self.path == '/logs':
            # Render logs as an HTML page with preformatted selectable text and scrolling
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            try:
                log_path = Path(__file__).parent.parent.parent / 'logs' / 'boss.log'
                if log_path.exists():
                    with open(log_path, 'r') as f:
                        lines = f.readlines()
                    recent_lines = lines[-100:] if len(lines) > 100 else lines
                    logs_html = '<html><head><title>BOSS Logs</title><style>body{font-family:monospace;padding:16px} pre{white-space:pre-wrap;word-break:break-word;}</style></head><body>'
                    logs_html += '<h2>Recent Logs</h2>'
                    logs_html += '<pre>' + '\n'.join([l.rstrip() for l in recent_lines]) + '</pre>'
                    logs_html += '</body></html>'
                    self.wfile.write(logs_html.encode('utf-8'))
                else:
                    self.wfile.write(b'<html><body><p>Log file not found</p></body></html>')
            except Exception as e:
                self.wfile.write(f'<html><body><p>Error reading logs: {e}</p></body></html>'.encode('utf-8'))
                if api_ref:
                    api_ref.log_error(f"Admin logs endpoint error: {e}")
                
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
                    api_ref.log_info(f"Git pull executed via admin interface, return code: {result.returncode}")
            except Exception as e:
                error_msg = f'Update error: {e}'
                self.wfile.write(error_msg.encode('utf-8'))
                if api_ref:
                    api_ref.log_error(f"Admin update endpoint error: {e}")
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
    admin_screen_text = f"""BOSS Admin Panel

Web Interface:
http://{ip}:{WEB_PORT}

Press any button to exit"""
    
    api.screen.clear_screen()
    api.screen.display_text(admin_screen_text, font_size=18, align="left")
    
    # Light up all LEDs to indicate any button can be pressed to exit
    api.hardware.set_led('red', True)
    api.hardware.set_led('yellow', True) 
    api.hardware.set_led('green', True)
    api.hardware.set_led('blue', True)
    
    api.log_info(f"Starting BOSS Admin web interface on port {WEB_PORT}")
    
    # Add button handler for exit
    def on_button_press(event_type, event):
        if event_type == 'button_pressed':
            # Any button press should exit
            button = event.get('button_id') or event.get('button')
            api.log_info(f"Admin panel exit requested via {button} button")
            stop_event.set()
    
    # Subscribe to button events
    button_sub_id = api.event_bus.subscribe('button_pressed', on_button_press)
    
    # Start HTTP server
    server = HTTPServer(("0.0.0.0", WEB_PORT), AdminHandler)
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    
    try:
        # Main loop - wait for stop event
        while not stop_event.is_set():
            stop_event.wait(0.1)
    except Exception as e:
        api.log_error(f"Admin app error: {e}")
    finally:
        # Cleanup
        server.shutdown()
        api.screen.clear_screen()
        api.screen.display_text("Admin panel stopped", font_size=20, align="center")
        # Turn off all LEDs
        api.hardware.set_led('red', False)
        api.hardware.set_led('yellow', False)
        api.hardware.set_led('green', False)
        api.hardware.set_led('blue', False)
        # Unsubscribe from button events
        api.event_bus.unsubscribe(button_sub_id)
        api.log_info("BOSS Admin web interface stopped")
        
        # Clear global reference
        api_ref = None
