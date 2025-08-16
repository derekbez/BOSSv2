#!/bin/bash

# B.O.S.S. Systemd Service Setup Script
set -e

BOSS_ROOT="/home/rpi/boss"
SERVICE_NAME="boss"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
USER="rpi"

echo "Setting up B.O.S.S. systemd service..."

# Ensure user is in required groups
echo "Adding user to required groups..."
sudo usermod -a -G gpio,video,audio $USER

# Ensure virtual environment exists and has runtime deps installed
if [ ! -d "$BOSS_ROOT/.venv" ]; then
	echo "Creating Python virtual environment with system site packages (to access apt-installed GPIO libs)..."
	python3 -m venv --system-site-packages "$BOSS_ROOT/.venv"
fi

echo "Upgrading pip and installing runtime requirements..."
"$BOSS_ROOT/.venv/bin/python" -m pip install --upgrade pip
if [ -f "$BOSS_ROOT/requirements/base.txt" ]; then
	"$BOSS_ROOT/.venv/bin/python" -m pip install -r "$BOSS_ROOT/requirements/base.txt"
elif [ -f "$BOSS_ROOT/requirements.txt" ]; then
	"$BOSS_ROOT/.venv/bin/python" -m pip install -r "$BOSS_ROOT/requirements.txt"
fi

# Create the systemd service file
echo "Creating systemd service file at $SERVICE_FILE..."
sudo tee $SERVICE_FILE > /dev/null <<EOF
[Unit]
Description=B.O.S.S. (Buttons, Operations, Switches & Screen)
Documentation=https://github.com/derekbez/BOSSv2
After=network.target sound.target
Wants=network.target

[Service]
Type=simple
User=$USER
Group=gpio
SupplementaryGroups=video audio

# Working directory and environment
WorkingDirectory=$BOSS_ROOT
Environment=PYTHONPATH=$BOSS_ROOT
Environment=BOSS_LOG_LEVEL=INFO
Environment=BOSS_CONFIG_PATH=$BOSS_ROOT/boss/config/boss_config.json
# Ensure dev/test modes are disabled in production
Environment=BOSS_DEV_MODE=0
Environment=BOSS_TEST_MODE=0

# Virtual environment and execution
ExecStart=$BOSS_ROOT/.venv/bin/python -m boss.main
ExecReload=/bin/kill -HUP \$MAINPID

# Restart policy
Restart=always
RestartSec=10
StartLimitInterval=60
StartLimitBurst=3

# Resource limits
MemoryMax=512M
CPUQuota=80%

# Security hardening
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ReadWritePaths=$BOSS_ROOT/boss/logs $BOSS_ROOT/boss/config

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=boss

[Install]
WantedBy=multi-user.target
EOF

# Create logs directory if it doesn't exist
mkdir -p $BOSS_ROOT/boss/logs
chown $USER:$USER $BOSS_ROOT/boss/logs

# Reload systemd and enable service
echo "Reloading systemd and enabling service..."
sudo systemctl daemon-reload
sudo systemctl enable $SERVICE_NAME

echo "B.O.S.S. systemd service setup complete!"
echo ""
echo "Available commands:"
echo "  sudo systemctl start $SERVICE_NAME     # Start the service"
echo "  sudo systemctl stop $SERVICE_NAME      # Stop the service"
echo "  sudo systemctl restart $SERVICE_NAME   # Restart the service"
echo "  sudo systemctl status $SERVICE_NAME    # Check status"
echo "  sudo journalctl -u $SERVICE_NAME -f    # View live logs"
echo "  sudo systemctl disable $SERVICE_NAME   # Disable auto-start"
echo ""
echo "The service is now enabled and will start automatically on boot."
echo "To start it now, run: sudo systemctl start $SERVICE_NAME"
