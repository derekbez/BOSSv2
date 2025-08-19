# SSH Authentication Setup for B.O.S.S. Remote Development

This guide covers setting up SSH key authentication between your Windows development machine and the Raspberry Pi for passwordless, secure remote access.

## Overview

SSH key authentication is required for:
- **Remote Management Script**: Control BOSS service from Windows
- **Passwordless Access**: No typing passwords for every command
- **Security**: More secure than password authentication
- **Automation**: Enables scripted deployment and monitoring

## Prerequisites

- Windows machine with SSH client (Windows 10/11 has built-in SSH)
- Raspberry Pi with SSH enabled
- Network connectivity between Windows and Pi
- Know the Pi's IP address or hostname

## Step-by-Step Setup

### 1. **Find Your Pi's Network Address**

On the Raspberry Pi, find its IP address:
```bash
# Method 1: Check IP address
ip addr show wlan0 | grep inet

# Method 2: Use hostname
hostname -I

# Method 3: Check with ifconfig
ifconfig wlan0
```

Example output: `192.168.1.100`

### 2. **Test Basic SSH Connection**

From Windows Command Prompt or PowerShell:
```bash
# Test SSH connection (will ask for password)
ssh rpi@192.168.1.100

# Or if using hostname
ssh rpi@rpiboss.local
```

If this fails, SSH might not be enabled on the Pi:
```bash
# On the Pi, enable SSH
sudo systemctl enable ssh
sudo systemctl start ssh
```

### 3. **Generate SSH Key Pair (Windows)**

On Windows PowerShell or Command Prompt:
```bash
# Check if you already have SSH keys
dir ~/.ssh
# Look for id_rsa and id_rsa.pub files

# If no keys exist, generate new ones
ssh-keygen -t rsa -b 4096 -C "your-email@example.com"

# When prompted:
# - File location: Press Enter (use default ~/.ssh/id_rsa)
# - Passphrase: Press Enter (no passphrase for automation)
# - Confirm passphrase: Press Enter
```

This creates:
- `~/.ssh/id_rsa` (private key - keep secret)
- `~/.ssh/id_rsa.pub` (public key - safe to share)

### 4. **Copy Public Key to Raspberry Pi**

#### **Method 1: Windows One-liner (Recommended for Windows)**
```bash
# Copy key using Windows PowerShell/Command Prompt
type ~/.ssh/id_rsa.pub | ssh rpi@192.168.1.143 "mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys"

# Enter the Pi's password when prompted
# This automatically sets up the authorized_keys file
```

#### **Method 2: Using ssh-copy-id (if available)**
```bash
# Copy your public key to the Pi (Linux/Mac or Windows with ssh-copy-id)
ssh-copy-id rpi@192.168.1.143

# Enter the Pi's password when prompted
# Note: ssh-copy-id may not be available on all Windows systems
```

#### **Method 3: Manual Copy (if automated methods fail)**
```bash
# Display your public key
type ~/.ssh/id_rsa.pub

# Copy the entire output, then SSH to Pi
ssh rpi@192.168.1.143

# On the Pi, create SSH directory and add key
mkdir -p ~/.ssh
chmod 700 ~/.ssh
nano ~/.ssh/authorized_keys
# Paste your public key on a single line
# Save and exit (Ctrl+X, Y, Enter)
chmod 600 ~/.ssh/authorized_keys
exit
```

### 5. **Test Passwordless Authentication**

```bash
# Test SSH connection (should NOT ask for password)
ssh rpi@192.168.1.143

# If successful, you'll connect without entering a password
# Exit the SSH session
exit
```

### 6. **Update Remote Manager Configuration**

Edit `scripts/boss_remote_manager.py` and update the `RPI_HOST` variable:
```python
# Update this line with your Pi's address
RPI_HOST = "rpi@192.168.1.143"  # Use your Pi's actual IP or hostname
```

### 7. **Test Remote Manager**

```bash
# Test the remote manager
python scripts/boss_remote_manager.py ssh-setup

# Should show "SSH authentication is already working!"
```

## Troubleshooting

### **Common Issues and Solutions**

#### **1. "Permission denied (publickey)"**
```bash
# Check if public key was copied correctly
ssh rpi@192.168.1.143 "cat ~/.ssh/authorized_keys"

# Should show your public key content
# If empty or missing, repeat the copy process
```

#### **2. "Host key verification failed"**
```bash
# Remove old host key and try again
ssh-keygen -R 192.168.1.143
ssh rpi@192.168.1.143
# Type "yes" when prompted to accept new host key
```

#### **3. "Connection refused"**
```bash
# SSH service might not be running on Pi
ssh rpi@192.168.1.143 "sudo systemctl start ssh"
ssh rpi@192.168.1.143 "sudo systemctl enable ssh"
```

#### **4. "No route to host"**
```bash
# Check network connectivity
ping 192.168.1.143

# Check if IP address changed
# On Pi: ip addr show wlan0
```

#### **5. Wrong username or hostname**
```bash
# Common usernames: pi, rpi, ubuntu
ssh pi@192.168.1.143
ssh ubuntu@192.168.1.143

# Check actual username on Pi
ssh rpi@192.168.1.143 "whoami"
```

### **Advanced Troubleshooting**

#### **Enable SSH Debug Output**
```bash
# Verbose SSH connection for debugging
ssh -vvv rpi@192.168.1.143
```

#### **Check SSH Server Configuration**
```bash
# On the Pi, check SSH server status
sudo systemctl status ssh
sudo journalctl -u ssh -n 20
```

#### **Check File Permissions (on Pi)**
```bash
# SSH is picky about file permissions
ls -la ~/.ssh/
# Should show:
# drwx------ (700) for .ssh directory
# -rw------- (600) for authorized_keys file

# Fix permissions if needed
chmod 700 ~/.ssh
chmod 600 ~/.ssh/authorized_keys
```

## Security Best Practices

### **1. Disable Password Authentication (Optional)**
After confirming key auth works, you can disable password auth:
```bash
# On the Pi, edit SSH config
sudo nano /etc/ssh/sshd_config

# Add or modify these lines:
PasswordAuthentication no
PubkeyAuthentication yes
ChallengeResponseAuthentication no

# Restart SSH service
sudo systemctl restart ssh
```

### **2. Use SSH Config File**
Create `~/.ssh/config` on Windows:
```
Host rpiboss
    HostName 192.168.1.100
    User rpi
    IdentityFile ~/.ssh/id_rsa
    Port 22
```

Then use: `ssh rpiboss` instead of full address.

### **3. Regular Key Rotation**
```bash
# Generate new keys periodically
ssh-keygen -t rsa -b 4096 -f ~/.ssh/id_rsa_new
# Copy new key to Pi
# Update scripts to use new key
# Remove old key from authorized_keys
```

## Integration with Remote Manager

### **Automated Setup Check**
The remote manager now includes SSH setup assistance:
```bash
# Interactive SSH setup guide
python scripts/boss_remote_manager.py
# Choose option 11: Setup SSH Authentication

# Command line SSH setup
python scripts/boss_remote_manager.py ssh-setup
```

### **Connection Test**
```bash
# Test SSH connection without running commands
python scripts/boss_remote_manager.py
# Menu will show SSH connection status on startup
```

## Network Configuration

### **Static IP (Recommended)**
To prevent IP address changes, set a static IP on the Pi:
```bash
# Edit network configuration
sudo nano /etc/dhcpcd.conf

# Add at the end (adjust to your network):
interface wlan0
static ip_address=192.168.1.100/24
static routers=192.168.1.1
static domain_name_servers=8.8.8.8 8.8.4.4

# Restart networking
sudo systemctl restart dhcpcd
```

### **Hostname Setup**
Make the Pi accessible by name:
```bash
# On Pi, set hostname
sudo hostnamectl set-hostname rpiboss

# Add to /etc/hosts on Windows (as Administrator)
# C:\Windows\System32\drivers\etc\hosts
192.168.1.100    rpiboss
```

Then use: `ssh rpi@rpiboss`

## VSCode Integration

### **Remote-SSH Extension**
1. Install "Remote - SSH" extension in VSCode
2. Press Ctrl+Shift+P, type "Remote-SSH: Connect to Host"
3. Enter: `rpi@192.168.1.100`
4. VSCode will connect via SSH for full remote development

### **Terminal Integration**
Add to PowerShell profile (`$PROFILE`):
```powershell
# B.O.S.S. SSH shortcuts
function ssh-boss { ssh rpi@192.168.1.100 }
function boss-manager { python scripts/boss_remote_manager.py }
```

## Backup and Recovery

### **Backup SSH Keys**
```bash
# Copy SSH keys to secure location
copy ~/.ssh/id_rsa* "C:\Backup\SSH\"
```

### **Key Recovery**
```bash
# If keys are lost, generate new ones and recopy
ssh-keygen -t rsa -b 4096
ssh-copy-id rpi@192.168.1.100
```

## Multiple Development Machines

### **Same Key on Multiple Machines**
```bash
# Copy private key to another Windows machine
# Place in ~/.ssh/id_rsa
# Set permissions (Windows: right-click, Properties, Security)
```

### **Multiple Keys for Same Pi**
```bash
# Each developer can add their own public key
# Pi's ~/.ssh/authorized_keys can contain multiple public keys
# One key per line
```

This comprehensive SSH setup ensures secure, passwordless remote development for B.O.S.S. with robust troubleshooting and security best practices.
