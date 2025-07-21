#!/usr/bin/env python3
"""
Utility script to check WebUI status and manage the server.
"""

import socket
import subprocess
import sys
from typing import Optional

def is_port_in_use(port: int, host: str = "127.0.0.1") -> bool:
    """Check if a port is already in use."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        try:
            sock.bind((host, port))
            return False
        except OSError:
            return True

def get_process_on_port(port: int) -> Optional[str]:
    """Get the process information for a given port (Windows)."""
    try:
        # Use netstat to find the PID
        result = subprocess.run(
            ["netstat", "-ano"], 
            capture_output=True, 
            text=True, 
            check=True
        )
        
        for line in result.stdout.splitlines():
            if f":{port}" in line and "LISTENING" in line:
                parts = line.split()
                if len(parts) >= 5:
                    pid = parts[-1]
                    
                    # Get process name using tasklist
                    tasklist_result = subprocess.run(
                        ["tasklist", "/FI", f"PID eq {pid}"], 
                        capture_output=True, 
                        text=True
                    )
                    
                    for task_line in tasklist_result.stdout.splitlines():
                        if pid in task_line:
                            return f"PID {pid}: {task_line.split()[0]}"
        
        return None
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "Unable to determine process"

def test_webui_response(port: int = 8070) -> bool:
    """Test if WebUI is responding to HTTP requests."""
    try:
        import urllib.request
        from urllib.error import URLError
        
        url = f"http://localhost:{port}/api/system/info"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=3) as response:
            return response.status == 200
    except (URLError, ConnectionError, OSError):
        return False

def kill_process_on_port(port: int) -> bool:
    """Kill the process using the specified port (Windows)."""
    try:
        # Get PID using netstat
        result = subprocess.run(
            ["netstat", "-ano"], 
            capture_output=True, 
            text=True, 
            check=True
        )
        
        for line in result.stdout.splitlines():
            if f":{port}" in line and "LISTENING" in line:
                parts = line.split()
                if len(parts) >= 5:
                    pid = parts[-1]
                    print(f"Killing process PID {pid}...")
                    subprocess.run(["taskkill", "/F", "/PID", pid], check=True)
                    return True
        
        print(f"No process found listening on port {port}")
        return False
    except subprocess.CalledProcessError as e:
        print(f"Error killing process: {e}")
        return False

def main():
    """Main function to check WebUI status."""
    port = 8070
    
    print(f"BOSS WebUI Status Check - Port {port}")
    print("=" * 50)
    
    # Check if port is in use
    if is_port_in_use(port):
        print(f"✅ Port {port} is IN USE")
        
        # Get process info
        process_info = get_process_on_port(port)
        if process_info:
            print(f"📋 Process: {process_info}")
        
        # Test if it's actually the WebUI responding
        if test_webui_response(port):
            print(f"🌐 WebUI is RESPONDING at http://localhost:{port}")
            print(f"💡 You can access the WebUI in your browser")
        else:
            print(f"❌ Port is in use but NOT responding as WebUI")
            print(f"💡 Another service might be using port {port}")
            
    else:
        print(f"⭕ Port {port} is AVAILABLE")
        print(f"💡 WebUI is not currently running")
    
    print("\nCommands:")
    print(f"  • Start BOSS with WebUI: python -m boss.main --hardware webui")
    print(f"  • Kill process on port {port}: python scripts/check_webui.py --kill")
    print(f"  • Open WebUI: http://localhost:{port}")
    
    # Handle kill argument
    if len(sys.argv) > 1 and sys.argv[1] == "--kill":
        if is_port_in_use(port):
            print(f"\n🔄 Attempting to kill process on port {port}...")
            if kill_process_on_port(port):
                print("✅ Process killed successfully")
            else:
                print("❌ Failed to kill process")
        else:
            print(f"\n💡 No process to kill - port {port} is already free")

if __name__ == "__main__":
    main()
