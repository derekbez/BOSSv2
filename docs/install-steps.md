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

echo "*** Installing B.O.S.S. Python dependencies from centralized requirement files..."
pip install -r requirements/base.txt -r requirements/dev.txt
echo "*** B.O.S.S. Python dependencies installed."

echo "*** Installing lgpio backend for GPIOZero (recommended for modern Pi OS)..."
sudo apt install -y python3-lgpio
echo "*** lgpio backend installation completed."

echo "*** (Optional) Installing pigpio system daemon (only if you need pigpio-specific features)..."
echo "*** You can skip this if using lgpio as the default pin factory."
sudo apt install -y pigpio || true
echo "*** pigpio system daemon step completed (optional)."

echo "*** Installing  fontconfig..."
sudo apt install fontconfig
echo "*** fontconfig installation completed."

echo "*** Configuring GPIO settings for power button and indicator light (if needed)..."
echo "dtoverlay=gpio-shutdown,gpio_pin=3" | sudo tee -a /boot/firmware/config.txt
echo "gpio=14=op,pd,dh" | sudo tee -a /boot/firmware/config.txt
echo "*** Updated /boot/firmware/config.txt:"
cat /boot/firmware/config.txt
echo "*** GPIO configuration completed."

# If you choose pigpio backend, start the pigpio daemon (optional):
# sudo systemctl start pigpiod
# sudo systemctl enable pigpiod

# If you choose lgpio backend (recommended), configure the pin factory via systemd env:
# Example in boss-dev.service or environment: GPIOZERO_PIN_FACTORY=lgpio

echo "*** B.O.S.S. installation complete. Activate your virtual environment and run the app with:"
echo "source ~/boss/boss-venv/bin/activate"
echo "cd ~/boss"
echo "python3 -m boss.main"


On Windows, for the WebUi debugging app install:
pip install -r requirements/base.txt -r requirements/dev.txt

If you still see a WebSocket warning when running the WebUI, verify these are installed in your active environment:

Windows CMD (no venv activation required):
	.\.venv\Scripts\python.exe -c "import websockets, uvicorn; print('websockets', websockets.__version__, 'uvicorn', uvicorn.__version__)"
If that fails, install explicitly into the venv:
	.\.venv\Scripts\python.exe -m pip install "uvicorn[standard]" websockets

Default screen backend is "rich". To change to Pillow, set in boss/config/boss_config.json:
{
	"hardware": { "screen_backend": "pillow" }
}

On Windows CMD, activate venv before running:
	.\.venv\Scripts\activate
Then run:
	.\.venv\Scripts\python.exe -m boss.main --hardware webui

