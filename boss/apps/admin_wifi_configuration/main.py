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

class WifiConfigHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        html = """
        <html><head><title>Wi-Fi Setup</title></head><body>
        <h2>Configure Wi-Fi</h2>
        <form method='POST' action='/connect.php'>
            SSID: <input name='ssid' type='text' required><br>
            Password: <input name='password' type='password'><br>
            <input type='submit' value='Connect'>
        </form>
        </body></html>
        """
        self.wfile.write(html.encode('utf-8'))

    def do_POST(self):
        if self.path == '/connect.php':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            params = urllib.parse.parse_qs(post_data.decode('utf-8'))
            ssid = params.get('ssid', [''])[0]
            password = params.get('password', [''])[0]
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b'<html><body>Connecting... Please wait and check the device screen.</body></html>')
            # Run nmcli to connect
            threading.Thread(target=connect_wifi, args=(ssid, password)).start()


def start_ap():
    subprocess.run([
        "nmcli", "connection", "add",
        "type", "wifi",
        "ifname", AP_INTERFACE,
        "con-name", "setup-hotspot",
        "autoconnect", "yes",
        "ssid", AP_SSID
    ], check=False)
    subprocess.run([
        "nmcli", "connection", "modify", "setup-hotspot",
        "802-11-wireless.mode", "ap",
        "ipv4.method", "shared",
        "wifi-sec.key-mgmt", "wpa-psk",
        "wifi-sec.psk", AP_PASSWORD
    ], check=False)
    subprocess.run(["nmcli", "connection", "up", "setup-hotspot"], check=False)


def stop_ap():
    subprocess.run(["nmcli", "connection", "down", "setup-hotspot"], check=False)
    subprocess.run(["nmcli", "connection", "delete", "setup-hotspot"], check=False)


def connect_wifi(ssid: str, password: str):
    stop_ap()
    subprocess.run(["nmcli", "device", "wifi", "connect", ssid, "password", password], check=False)
    # Optionally verify connection


def run(stop_event: Event, api: Any) -> None:
    """
    Starts AP mode, web server, and handles Wi-Fi credential collection.
    Args:
        stop_event (Event): Event to signal app termination.
        api (object): Provided API for hardware/display access.
    """
    api.display_text("Starting Wi-Fi AP mode...\nSSID: PiSetup\nPassword: raspberry")
    start_ap()
    ip = os.popen(f"ip addr show {AP_INTERFACE} | grep 'inet ' | awk '{{print $2}}' | cut -d/ -f1").read().strip()
    api.display_text(f"Connect to Wi-Fi:\nSSID: PiSetup\nPassword: raspberry\nThen visit: http://{ip or 'DEVICE_IP'}")
    server = HTTPServer(("0.0.0.0", WEB_PORT), WifiConfigHandler)
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    try:
        while not stop_event.is_set():
            pass
    finally:
        server.shutdown()
        stop_ap()
        api.display_text("Wi-Fi config finished. You may now reconnect.")
