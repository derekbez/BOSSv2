BOSS Admin Features

1.
Shutdown
- As a user I want to shutdown the app or the system gracefully
- so that risk of corruption and data loss is minimised.
- Acceptance Criteria:
	- When I select the appropriate mini-app number (initially this could be "255"), the Shutdown app will run.
	- The Yellow, Blue and Green lights will illuminate to indicate the Yellow, Blue and Green buttons are available.
	- There will be appropriate text on the screen to tell me what each of the buttons do and what I should expect.
	- When the Yellow button is pressed, the BOSS application should shut down gracefully, and the system reboot.
	- When the Blue button is pressed, the BOSS application should shut down gracefully, and the system shut down.
	- When the Green button is pressed, the BOSS application should shut down gracefully, and the user is returned to the OS.
	
2.
Wifi Configuration
- As an Admin, I want to select or change the wifi that is being used
- so that the BOSS application and the mini-apps can connect to the internet.
- Acceptance Critiera:
	- When I select the appropriate mini-app number (initially this could be "252"), the wifi config app will run.
	- A web server will run in the background
	- The wifi network is switched to Access Point Mode (see notes below)
	- The web server's IP address and port will be displayed on the screen, allowing the Admin to connect 
	- The Admin can connect to the webpage and enter the wifi credentials
	- The Access Point Mode is disabled, and wifi network is enabled on the new wifi connection, and results are displayed on the screen.  (Perhaps ping default gateway and ping Google to prove the connection is successful)
	

3.
BOSS Admin
- As an Admin, I want to 
	- view the list of mini-apps
	- assign mini-apps to specific numbers, including changing the order (see bossconfiguration.json)
	- see which mini-apps are not assigned
	- view and edit the manifest for a mini-app
	- view and edit the config file for a mini-app
	- view the contents of a mini-app's Assets
	- download and upload a mini-app's Assets
	- update the BOSS software from github
- Acceptance Criteria:
	- When I select the appropriate mini-app number (initially this could be "254"), the Admin app will run.
	- A web server will run in the background
	- The web server's IP address and port will be displayed on the screen, allowing the Admin to connect 
	- The Admin can connect to the website and perform various admin tasks 
	- when the mini-app terminates, the webserver should be shut down gracefully
	
4.
Startup app - update check
- as a user, when I start BOSS, as well as seeing the "ready" prompt on the screen, I also want to know if there are updates to the software
- so that I can perform an update
- Acceptance Criteria:
	- The startup app checks if the git repo is more recent than what is installed, and displays a message on screen if there are updates available.
	
5.	
Startup app - network check
- as a user, when I start BOSS, I want to know if there is no network connection.
- so that I know to perform maintenance
- Acceptance Criteria:
	- the startup app checks if an internet connection is available, and displays a messahe on screen if not.
	
	
	
Wifi Config notes:
```
import subprocess

def start_ap(ssid="PiSetup", password="raspberry"):
    subprocess.run([
        "nmcli", "connection", "add",
        "type", "wifi",
        "ifname", "wlan0",
        "con-name", "setup-hotspot",
        "autoconnect", "yes",
        "ssid", ssid
    ])
    subprocess.run([
        "nmcli", "connection", "modify", "setup-hotspot",
        "802-11-wireless.mode", "ap",
        "ipv4.method", "shared",
        "wifi-sec.key-mgmt", "wpa-psk",
        "wifi-sec.psk", password
    ])
    subprocess.run(["nmcli", "connection", "up", "setup-hotspot"])

def stop_ap():
    subprocess.run(["nmcli", "connection", "down", "setup-hotspot"])
    subprocess.run(["nmcli", "connection", "delete", "setup-hotspot"])
```	
	
	
	
	
	