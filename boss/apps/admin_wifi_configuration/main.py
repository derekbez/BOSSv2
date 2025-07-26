"""
Mini-app: Admin Wi-Fi Configuration
Provides UI and web server for Wi-Fi setup via AP mode.
Entry point: run(stop_event, api)
"""
import os
import subprocess
import threading
from threading import Event
from typing import Any
from http.server import BaseHTTPRequestHandler, HTTPServer
import urllib.parse

AP_SSID = "PiSetup"
AP_PASSWORD = "raspberry"
AP_INTERFACE = "wlan0"
WEB_PORT = 80

# Global reference to API for handler access
api_ref = None

class WifiConfigHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        html = """
        <html><head><title>BOSS Wi-Fi Setup</title></head><body>
        <h2>Configure Wi-Fi Connection</h2>
        <form method='POST' action='/connect'>
            SSID: <input name='ssid' type='text' required><br><br>
            Password: <input name='password' type='password'><br><br>
            <input type='submit' value='Connect to Wi-Fi'>
        </form>
        <p><i>After connecting, the device will exit AP mode and connect to your Wi-Fi network.</i></p>
        </body></html>
        """
        self.wfile.write(html.encode('utf-8'))

    def do_POST(self):
        if self.path == '/connect':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            params = urllib.parse.parse_qs(post_data.decode('utf-8'))
            ssid = params.get('ssid', [''])[0]
            password = params.get('password', [''])[0]
            
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b'<html><body><h2>Connecting to Wi-Fi...</h2><p>Please wait and check the device screen for status.</p></body></html>')
            
            # Run connection in background
            threading.Thread(target=connect_wifi, args=(ssid, password), daemon=True).start()

    def log_message(self, format, *args):
        # Suppress default HTTP server logging
        pass


def start_ap():
    """Start access point mode."""
    try:
        # Remove any existing hotspot connection
        subprocess.run(["nmcli", "connection", "delete", "setup-hotspot"], 
                      check=False, capture_output=True)
        
        # Create new hotspot connection
        subprocess.run([
            "nmcli", "connection", "add",
            "type", "wifi",
            "ifname", AP_INTERFACE,
            "con-name", "setup-hotspot",
            "autoconnect", "yes",
            "ssid", AP_SSID
        ], check=True, capture_output=True)
        
        # Configure hotspot settings
        subprocess.run([
            "nmcli", "connection", "modify", "setup-hotspot",
            "802-11-wireless.mode", "ap",
            "ipv4.method", "shared",
            "wifi-sec.key-mgmt", "wpa-psk",
            "wifi-sec.psk", AP_PASSWORD
        ], check=True, capture_output=True)
        
        # Activate hotspot
        subprocess.run(["nmcli", "connection", "up", "setup-hotspot"], 
                      check=True, capture_output=True)
        
        if api_ref:
            api_ref.log_info("Access point started successfully")
        return True
        
    except subprocess.CalledProcessError as e:
        if api_ref:
            api_ref.log_error(f"Failed to start access point: {e}")
        return False


def stop_ap():
    """Stop access point mode."""
    try:
        subprocess.run(["nmcli", "connection", "down", "setup-hotspot"], 
                      check=False, capture_output=True)
        subprocess.run(["nmcli", "connection", "delete", "setup-hotspot"], 
                      check=False, capture_output=True)
        if api_ref:
            api_ref.log_info("Access point stopped")
    except Exception as e:
        if api_ref:
            api_ref.log_error(f"Error stopping access point: {e}")


def connect_wifi(ssid: str, password: str):
    """Connect to WiFi network."""
    try:
        if api_ref:
            api_ref.screen.clear_screen()
            api_ref.screen.display_text(f"Connecting to:\n{ssid}", font_size=16, align="center")
            api_ref.log_info(f"Attempting to connect to WiFi: {ssid}")
        
        # Stop AP mode first
        stop_ap()
        
        # Connect to WiFi
        if password:
            result = subprocess.run([
                "nmcli", "device", "wifi", "connect", ssid, "password", password
            ], capture_output=True, text=True, timeout=30)
        else:
            result = subprocess.run([
                "nmcli", "device", "wifi", "connect", ssid
            ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            if api_ref:
                api_ref.screen.clear_screen()
                api_ref.screen.display_text(f"Connected to:\n{ssid}", font_size=16, align="center")
                api_ref.log_info(f"Successfully connected to WiFi: {ssid}")
        else:
            if api_ref:
                api_ref.screen.clear_screen()
                api_ref.screen.display_text(f"Failed to connect to:\n{ssid}\nError: {result.stderr[:50]}", font_size=14, align="center")
                api_ref.log_error(f"Failed to connect to WiFi {ssid}: {result.stderr}")
                
    except subprocess.TimeoutExpired:
        if api_ref:
            api_ref.screen.clear_screen()
            api_ref.screen.display_text(f"Connection timeout:\n{ssid}", font_size=16, align="center")
            api_ref.log_error(f"WiFi connection timeout: {ssid}")
    except Exception as e:
        if api_ref:
            api_ref.screen.clear_screen()
            api_ref.screen.display_text(f"Connection error:\n{str(e)[:50]}", font_size=14, align="center")
            api_ref.log_error(f"WiFi connection error: {e}")


def run(stop_event: Event, api: Any) -> None:
    """
    Starts AP mode, web server, and handles Wi-Fi credential collection.
    Args:
        stop_event (Event): Event to signal app termination.
        api (AppAPI): Provided API for hardware/display access.
    """
    global api_ref
    api_ref = api
    
    api.log_info("Starting WiFi configuration mode")
    
    # Turn off all LEDs since no button input is expected (web-based interface)
    api.hardware.set_led('red', False)
    api.hardware.set_led('yellow', False)
    api.hardware.set_led('green', False)
    api.hardware.set_led('blue', False)
    
    api.screen.clear_screen()
    api.screen.display_text("Starting Wi-Fi setup mode...", font_size=16, align="center")
    
    # Start access point
    if not start_ap():
        api.screen.clear_screen()
        api.screen.display_text("Failed to start\nAP mode", font_size=16, align="center")
        return
    
    # Get AP IP address
    try:
        ip_result = subprocess.run([
            "ip", "addr", "show", AP_INTERFACE
        ], capture_output=True, text=True, timeout=5)
        
        # Extract IP from output
        import re
        ip_match = re.search(r'inet (\d+\.\d+\.\d+\.\d+)', ip_result.stdout)
        ip = ip_match.group(1) if ip_match else "192.168.4.1"
    except:
        ip = "192.168.4.1"  # Default AP IP
    
    # Display connection info
    wifi_setup_text = f"""WiFi Setup Mode

1. Connect to WiFi:
   SSID: {AP_SSID}
   Pass: {AP_PASSWORD}

2. Open browser:
   http://{ip}"""
   
    api.screen.clear_screen()
    api.screen.display_text(wifi_setup_text, font_size=14, align="left")
    
    # Start web server
    server = None
    try:
        server = HTTPServer(("0.0.0.0", WEB_PORT), WifiConfigHandler)
        server_thread = threading.Thread(target=server.serve_forever, daemon=True)
        server_thread.start()
        
        api.log_info(f"WiFi config web server started at http://{ip}:{WEB_PORT}")
        
        # Wait for stop event
        while not stop_event.is_set():
            stop_event.wait(1.0)
            
    except Exception as e:
        api.log_error(f"Error in WiFi configuration: {e}")
        api.screen.clear_screen()
        api.screen.display_text(f"Error: {str(e)[:50]}", font_size=16, align="center")
        
    finally:
        # Cleanup
        if server:
            server.shutdown()
        stop_ap()
        api.screen.clear_screen()
        api.screen.display_text("WiFi setup complete", font_size=16, align="center")
        api.log_info("WiFi configuration mode ended")
