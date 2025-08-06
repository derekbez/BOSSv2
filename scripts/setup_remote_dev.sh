#!/bin/bash
# B.O.S.S. Remote Development Setup Script
# Run this once to configure optimal SSH development environment

echo "🔧 Setting up B.O.S.S. for remote SSH development..."

# Add user to gpio group
echo "Adding $USER to gpio group..."
sudo usermod -a -G gpio $USER

# Install lgpio for better GPIO access
echo "Installing lgpio..."
source boss-venv/bin/activate
pip install lgpio

# Set up systemd service (optional)
echo "Setting up development systemd service..."
sudo cp scripts/boss-dev.service /etc/systemd/system/
sudo systemctl daemon-reload

# Enable GPIO and other interfaces
echo "Enabling GPIO interface..."
sudo raspi-config nonint do_spi 0      # Enable SPI
sudo raspi-config nonint do_i2c 0      # Enable I2C  
sudo raspi-config nonint do_ssh 0      # Ensure SSH is enabled

# Create development aliases
echo "Creating development aliases..."
cat >> ~/.bashrc << 'EOF'

# B.O.S.S. Development Aliases
alias boss-check='python3 scripts/remote_debug.py check'
alias boss-test='python3 scripts/remote_debug.py test'
alias boss-run='python3 scripts/remote_debug.py run'
alias boss-service-start='sudo systemctl start boss-dev'
alias boss-service-stop='sudo systemctl stop boss-dev'
alias boss-service-logs='sudo journalctl -u boss-dev -f'
alias boss-logs='tail -f boss/logs/boss.log'
EOF

echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Logout and login (or run 'newgrp gpio')"
echo "2. Test hardware: boss-check"
echo "3. Run component tests: boss-test"
echo "4. Run with enhanced logging: boss-run"
echo ""
echo "For service mode:"
echo "  sudo systemctl enable boss-dev  # Enable auto-start"
echo "  boss-service-start              # Start service"
echo "  boss-service-logs               # View live logs"