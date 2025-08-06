"""
B.O.S.S. Remote Management Script for Windows Development
Run from VSCode terminal to manage BOSS service on Raspberry Pi
"""

import subprocess
import sys
import time
import json
from pathlib import Path
from typing import Optional, Dict, Any

# Configuration - Update these for your setup
RPI_HOST = "rpi@rpiboss.local"  # SSH connection string (update to your Pi's hostname/IP)
SERVICE_NAME = "boss"
BOSS_ROOT = "/home/rpi/boss"

# SSH connection test
def test_ssh_connection():
    """Test SSH connection to Raspberry Pi"""
    try:
        result = run_ssh_command("echo 'SSH connection successful'")
        if result.returncode == 0:
            return True, "Connection successful"
        else:
            return False, f"SSH failed: {result.stderr}"
    except Exception as e:
        return False, f"SSH error: {e}"

class Colors:
    """ANSI color codes for terminal output"""
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    END = '\033[0m'

def run_ssh_command(command: str, capture_output: bool = True) -> subprocess.CompletedProcess:
    """Run command on Raspberry Pi via SSH"""
    ssh_cmd = ["ssh", RPI_HOST, command]
    
    if capture_output:
        result = subprocess.run(ssh_cmd, capture_output=True, text=True)
    else:
        result = subprocess.run(ssh_cmd, text=True)
    
    return result

def print_status(message: str, status: str = "INFO"):
    """Print colored status message"""
    colors = {
        "INFO": Colors.BLUE,
        "SUCCESS": Colors.GREEN,
        "WARNING": Colors.YELLOW,
        "ERROR": Colors.RED
    }
    color = colors.get(status, Colors.WHITE)
    print(f"{color}[{status}]{Colors.END} {message}")

def get_service_status() -> Dict[str, Any]:
    """Get detailed service status"""
    print_status("Checking service status...")
    
    # Get systemctl status
    status_result = run_ssh_command(f"sudo systemctl is-active {SERVICE_NAME}")
    is_active = status_result.stdout.strip() == "active"
    
    # Get detailed status
    detail_result = run_ssh_command(f"sudo systemctl status {SERVICE_NAME} --no-pager")
    
    # Get recent logs
    log_result = run_ssh_command(f"sudo journalctl -u {SERVICE_NAME} --since '5 minutes ago' --no-pager -n 10")
    
    return {
        "is_active": is_active,
        "status_output": detail_result.stdout,
        "recent_logs": log_result.stdout
    }

def start_service():
    """Start the BOSS service"""
    print_status("Starting BOSS service...")
    
    result = run_ssh_command(f"sudo systemctl start {SERVICE_NAME}")
    
    if result.returncode == 0:
        print_status("Service start command sent successfully", "SUCCESS")
        
        # Wait a moment and check status
        time.sleep(2)
        status = get_service_status()
        
        if status["is_active"]:
            print_status("Service is now running", "SUCCESS")
        else:
            print_status("Service failed to start", "ERROR")
            print(status["recent_logs"])
    else:
        print_status(f"Failed to start service: {result.stderr}", "ERROR")

def stop_service():
    """Stop the BOSS service"""
    print_status("Stopping BOSS service...")
    
    result = run_ssh_command(f"sudo systemctl stop {SERVICE_NAME}")
    
    if result.returncode == 0:
        print_status("Service stopped successfully", "SUCCESS")
    else:
        print_status(f"Failed to stop service: {result.stderr}", "ERROR")

def restart_service():
    """Restart the BOSS service"""
    print_status("Restarting BOSS service...")
    
    result = run_ssh_command(f"sudo systemctl restart {SERVICE_NAME}")
    
    if result.returncode == 0:
        print_status("Service restart command sent successfully", "SUCCESS")
        
        # Wait a moment and check status
        time.sleep(3)
        status = get_service_status()
        
        if status["is_active"]:
            print_status("Service restarted and running", "SUCCESS")
        else:
            print_status("Service failed to restart", "ERROR")
            print(status["recent_logs"])
    else:
        print_status(f"Failed to restart service: {result.stderr}", "ERROR")

def show_logs(follow: bool = False):
    """Show service logs"""
    if follow:
        print_status("Following live logs (Ctrl+C to stop)...")
        run_ssh_command(f"sudo journalctl -u {SERVICE_NAME} -f", capture_output=False)
    else:
        print_status("Showing recent logs...")
        result = run_ssh_command(f"sudo journalctl -u {SERVICE_NAME} --since '1 hour ago' --no-pager")
        print(result.stdout)

def show_status():
    """Show detailed service status"""
    status = get_service_status()
    
    print(f"\n{Colors.BOLD}=== BOSS Service Status ==={Colors.END}")
    
    if status["is_active"]:
        print_status("Service is RUNNING", "SUCCESS")
    else:
        print_status("Service is STOPPED", "WARNING")
    
    print(f"\n{Colors.BOLD}Status Details:{Colors.END}")
    print(status["status_output"])
    
    print(f"\n{Colors.BOLD}Recent Logs:{Colors.END}")
    print(status["recent_logs"])

def deploy_code():
    """Deploy code changes to Pi (if using git)"""
    print_status("Deploying latest code...")
    
    # Pull latest code
    result = run_ssh_command(f"cd {BOSS_ROOT} && git pull")
    if result.returncode != 0:
        print_status(f"Git pull failed: {result.stderr}", "ERROR")
        return
    
    print_status("Code updated, restarting service...", "SUCCESS")
    restart_service()

def show_hardware_test():
    """Run hardware test"""
    print_status("Running hardware test...")
    
    result = run_ssh_command(f"cd {BOSS_ROOT} && python3 scripts/test_tm1637_display.py")
    print(result.stdout)
    if result.stderr:
        print_status(f"Test errors: {result.stderr}", "WARNING")

def check_groups():
    """Check user groups and permissions"""
    print_status("Checking user groups and permissions...")
    
    # Check groups
    result = run_ssh_command("groups")
    print(f"User groups: {result.stdout.strip()}")
    
    # Check framebuffer access
    result = run_ssh_command("ls -la /dev/fb0")
    print(f"Framebuffer: {result.stdout.strip()}")
    
    # Check GPIO access
    result = run_ssh_command("ls -la /dev/gpiomem")
    print(f"GPIO: {result.stdout.strip()}")

def setup_ssh_auth():
    """Guide user through SSH authentication setup"""
    print_status("SSH Authentication Setup Guide", "INFO")
    print(f"\n{Colors.BOLD}Current SSH target:{Colors.END} {RPI_HOST}")
    
    # Test current connection
    success, message = test_ssh_connection()
    if success:
        print_status("SSH authentication is already working!", "SUCCESS")
        return
    
    print_status(f"SSH connection failed: {message}", "ERROR")
    print(f"\n{Colors.BOLD}To fix SSH authentication:{Colors.END}")
    print("1. Generate SSH key (if you don't have one):")
    print(f"   {Colors.CYAN}ssh-keygen -t rsa -b 4096{Colors.END}")
    print("\n2. Copy SSH key to Raspberry Pi:")
    print(f"   {Colors.CYAN}type ~/.ssh/id_rsa.pub | ssh {RPI_HOST} \"mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys\"{Colors.END}")
    print("   (Enter Pi password when prompted)")
    print("\n   Alternative methods if above fails:")
    print(f"   {Colors.CYAN}ssh-copy-id {RPI_HOST}{Colors.END} (if available)")
    print("   OR copy manually via SSH session")
    print("\n3. Test connection:")
    print(f"   {Colors.CYAN}ssh {RPI_HOST}{Colors.END}")
    print("\n4. Update RPI_HOST in this script if needed")
    print(f"\n{Colors.YELLOW}Press Enter after setting up SSH authentication...{Colors.END}")
    input()
    
    # Test again
    success, message = test_ssh_connection()
    if success:
        print_status("SSH authentication is now working!", "SUCCESS")
    else:
        print_status(f"SSH still not working: {message}", "ERROR")

def main():
    """Main interactive menu"""
    print(f"{Colors.BOLD}{Colors.CYAN}")
    print("=" * 50)
    print("   B.O.S.S. Remote Management Console")
    print("=" * 50)
    print(f"{Colors.END}")
    
    # Test SSH connection on startup
    success, message = test_ssh_connection()
    if not success:
        print_status(f"SSH connection failed: {message}", "ERROR")
        print_status("Run SSH setup to fix authentication issues", "WARNING")
    
    while True:
        print(f"\n{Colors.BOLD}Available Commands:{Colors.END}")
        print("1. 📊 Show Status")
        print("2. ▶️  Start Service")
        print("3. ⏹️  Stop Service")
        print("4. 🔄 Restart Service")
        print("5. 📋 Show Logs")
        print("6. 📡 Follow Live Logs")
        print("7. 🚀 Deploy & Restart")
        print("8. 🔧 Hardware Test")
        print("9. 👥 Check Groups & Permissions")
        print("10. 🔌 SSH to Pi")
        print("11. 🔑 Setup SSH Authentication")
        print("0. ❌ Exit")
        
        try:
            choice = input(f"\n{Colors.YELLOW}Enter choice (0-11): {Colors.END}").strip()
            
            if choice == "1":
                show_status()
            elif choice == "2":
                start_service()
            elif choice == "3":
                stop_service()
            elif choice == "4":
                restart_service()
            elif choice == "5":
                show_logs(follow=False)
            elif choice == "6":
                show_logs(follow=True)
            elif choice == "7":
                deploy_code()
            elif choice == "8":
                show_hardware_test()
            elif choice == "9":
                check_groups()
            elif choice == "10":
                print_status("Opening SSH session...")
                subprocess.run(["ssh", RPI_HOST])
            elif choice == "11":
                setup_ssh_auth()
            elif choice == "0":
                print_status("Goodbye!", "SUCCESS")
                break
            else:
                print_status("Invalid choice", "ERROR")
                
        except KeyboardInterrupt:
            print(f"\n{Colors.YELLOW}Interrupted. Returning to menu...{Colors.END}")
        except Exception as e:
            print_status(f"Error: {e}", "ERROR")

if __name__ == "__main__":
    # Quick command line options
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        if command == "start":
            start_service()
        elif command == "stop":
            stop_service()
        elif command == "restart":
            restart_service()
        elif command == "status":
            show_status()
        elif command == "logs":
            show_logs(follow=True)
        elif command == "test":
            show_hardware_test()
        elif command == "groups":
            check_groups()
        elif command == "ssh-setup":
            setup_ssh_auth()
        else:
            print_status(f"Unknown command: {command}", "ERROR")
            print("Available: start, stop, restart, status, logs, test, groups, ssh-setup")
    else:
        main()
