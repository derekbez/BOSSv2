
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

echo "*** Creating and activating a Python virtual environment 'repo'..."
python3 -m venv ~/repo
echo "source ~/repo/bin/activate" >> ~/.bashrc
echo "*** Virtual environment 'repo' will now activate automatically on new terminal sessions."
source ~/repo/bin/activate
cd repo
echo "*** Virtual environment 'repo' activated for the current session."

echo "*** Installing Python and essential packages..."
sudo apt install -y python3 python3-pip
sudo apt install -y python3-dev build-essential
sudo apt install -y python3-rpi-lgpio
sudo apt install -y python3-debugpy
echo "*** Python and essential packages installation completed."

echo "*** Ensuring pip is installed and updated..."
python -m ensurepip
python -m pip install --upgrade pip
echo "*** Pip is installed and updated."

echo "*** Installing GPIO and NFC-related packages..."
pip install RPi.GPIO
pip install nfcpy
sudo apt-get install -y libusb-1.0-0-dev libnfc-bin libnfc-dev libpcsclite-dev
echo "*** NFC-related packages installation completed."

echo "*** Installing MPD and related tools..."
sudo apt-get install -y mpd
pip install python-mpd2
echo "*** MPD and related tools installation completed."

echo "*** Removing unnecessary packages..."
sudo apt autoremove -y
echo "*** Clean-up completed."

echo "*** Cloning the bookplayer repository..."
git clone https://github.com/derekbez/bookplayer.git bookplayer
echo "*** Repository cloned successfully."

echo "*** Setting up books folder and configuring fstab..."
sudo mkdir -p ~/books
sudo cp /etc/fstab /etc/fstab.bak
echo "*** Backup of /etc/fstab created."

echo "*** Adding mount point to fstab..."
echo "*** LABEL=BOOKS /home/rpi/books auto defaults,nofail 0 0" | sudo tee -a /etc/fstab
echo "*** Updated fstab file:"
cat /etc/fstab
echo "*** Mount point configuration completed."

echo "*** Configuring GPIO settings for power button and indicator light..."
echo "dtoverlay=gpio-shutdown,gpio_pin=3" | sudo tee -a /boot/firmware/config.txt
echo "gpio=14=op,pd,dh" | sudo tee -a /boot/firmware/config.txt
echo "*** Updated /boot/firmware/config.txt:"
cat /boot/firmware/config.txt
echo "*** GPIO configuration completed."

echo "*** Setting up crontab for application startup..."
sudo crontab -l > crontab_backup.txt
(sudo crontab -l; echo "@reboot /home/rpi/repo/bookplayer/online_light.py &") | sudo crontab -
sudo crontab -l
chmod +x /home/rpi/repo/bookplayer/online_light.py
echo "*** Crontab setup completed."

echo "*** Final step: Configure MPD settings."
echo "*** Now edit : sudo nano /etc/mpd.conf"

sudo systemctl enable mpd
sudo systemctl start mpd
sudo systemctl status mpd
sudo apt-get install -y mpc