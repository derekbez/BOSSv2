"""
Project-wide path constants for B.O.S.S.
"""
import os

# Path to the root of the project (parent of the 'boss' package)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Key directories
CONFIG_DIR = os.path.join(PROJECT_ROOT, "config")
APPS_DIR = os.path.join(PROJECT_ROOT, "apps")
ASSETS_DIR = os.path.join(PROJECT_ROOT, "assets")
LOGS_DIR = os.path.join(PROJECT_ROOT, "logs")

# Key files
CONFIG_PATH = os.path.join(CONFIG_DIR, "BOSSsettings.json")
