echo "*** Starting system update..."
sudo apt update && sudo apt upgrade -y
echo "*** System update completed."

echo "*** Installing Git..."
sudo apt install -y git
echo "*** Git installation completed."

echo "*** Configuring Git user details..."
git config --global user.name "derekbez"
git config --global user.email "derek@be-easy.com"
echo "*** Git configuration completed."

echo "*** Installing Python 3.11+ and essential build tools..."
sudo apt install -y python3 python3-pip python3-venv python3-dev build-essential
echo "*** Python and build tools installation completed."

echo "*** Creating and activating a Python virtual environment 'bossenv'..."
python3 -m venv ~/bossenv
echo "source ~/bossenv/bin/activate" >> ~/.bashrc
echo "*** Virtual environment 'bossenv' will now activate automatically on new terminal sessions."
source ~/bossenv/bin/activate
echo "*** Virtual environment 'bossenv' activated for the current session."

cd ~

echo "*** Ensuring pip is installed and updated..."
python -m ensurepip
python -m pip install --upgrade pip
echo "*** Pip is installed and updated."

echo "*** Installing B.O.S.S. Python dependencies..."
pip install gpiozero pigpio rpi-tm1637 pytest Pillow
echo "*** B.O.S.S. Python dependencies installed."

echo "*** Installing pigpio system daemon (required for remote GPIO and some features)..."
sudo apt install -y pigpio
echo "*** pigpio system daemon installed."

echo "*** Cloning the B.O.S.S. repository..."
git clone https://github.com/derekbez/BOSSv2.git boss
cd boss
echo "*** Repository cloned successfully."

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
echo "python -m boss.main"

