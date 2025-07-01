echo "*** Starting system update..."
sudo apt update && sudo apt upgrade -y
echo "*** System update completed."

echo "*** Installing Python 3.11+ and essential build tools..."
sudo apt install -y python3 python3-pip python3-venv python3-dev build-essential
echo "*** Python and build tools installation completed."

echo "*** Installing Git..."
sudo apt install -y git
echo "*** Git installation completed."

echo "*** Configuring Git user details..."
git config --global user.name "derekbez"
git config --global user.email "derek@be-easy.com"
echo "*** Git configuration completed."

echo "*** Cloning the B.O.S.S. repository..."
git clone https://github.com/derekbez/BOSSv2.git boss
echo "*** Repository cloned successfully."

echo "*** Creating and activating a Python virtual environment 'boss-venv' inside the project directory..."
python3 -m venv boss-venv
source boss-venv/bin/activate
echo 'if [ -d "$HOME/boss-venv" ]; then source "$HOME/boss-venv/bin/activate"; fi' >> ~/.bashrc
echo "*** Virtual environment 'boss-venv' will now activate automatically on new terminal sessions."
echo "*** Virtual environment 'boss-venv' activated for the current session."

echo "*** Ensuring pip is installed and updated..."
python -m ensurepip
python -m pip install --upgrade pip
echo "*** Pip is installed and updated."

echo "*** Installing B.O.S.S. Python dependencies..."
pip install gpiozero pigpio python-tm1637 pytest Pillow numpy
echo "*** B.O.S.S. Python dependencies installed."

echo "*** Installing pigpio system daemon (required for remote GPIO and some features)..."
sudo apt install -y pigpio
echo "*** pigpio system daemon installed."

echo "*** Installing lgpio backend for GPIOZero (recommended for modern Pi OS)..."
sudo apt install -y python3-lgpio
echo "*** lgpio backend installation completed."

echo "*** Installing  fontconfig..."
sudo apt install fontconfig
echo "*** fontconfig installation completed."

echo "*** Configuring GPIO settings for power button and indicator light (if needed)..."
echo "dtoverlay=gpio-shutdown,gpio_pin=3" | sudo tee -a /boot/firmware/config.txt
echo "gpio=14=op,pd,dh" | sudo tee -a /boot/firmware/config.txt
echo "*** Updated /boot/firmware/config.txt:"
cat /boot/firmware/config.txt
echo "*** GPIO configuration completed."

# To start the pigpio daemon (required for gpiozero with pigpio backend):
sudo systemctl start pigpiod
sudo systemctl enable pigpiod

echo "*** B.O.S.S. installation complete. Activate your virtual environment and run the app with:"
echo "source ~/boss/boss-venv/bin/activate"
echo "cd ~/boss"
echo "python3 -m boss.main"


