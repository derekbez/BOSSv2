#!/bin/bash

# -----------------------------------------------------------------------------
# B.O.S.S. Systemd Service Setup / Re-Setup Script
#   Idempotent & repeatable provisioning of the boss systemd unit, virtualenv,
#   and required group memberships. Safe to re-run after pulling new code or
#   after an OS reinstall.
# -----------------------------------------------------------------------------
set -euo pipefail

DEFAULT_USER="rpi"
DEFAULT_ROOT="/home/${DEFAULT_USER}/boss"
SERVICE_NAME="boss"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
BACKUP_SUFFIX="$(date +%Y%m%d-%H%M%S)"

DISABLE_GETTY=0
FORCE_OVERWRITE=0
SKIP_VENV=0
RUN_USER="$DEFAULT_USER"
BOSS_ROOT="$DEFAULT_ROOT"
ALLOCATE_TTY=0

usage() {
	cat <<USAGE
Usage: $0 [options]

Options:
	-u, --user USER          System user that owns the deployment (default: ${DEFAULT_USER})
	-r, --root PATH          Root directory of boss checkout (default: /home/USER/boss)
	-f, --force              Overwrite existing service file without prompt
	-d, --disable-getty      Disable getty@tty1 (one time) for dedicated TTY screen
	-a, --allocate-tty       Add TTYPath=/dev/tty1 & related directives for textual backend
	-n, --no-venv            Skip virtual environment creation / package install
	-h, --help               Show this help and exit

Examples:
	$0 -u rpi -r /home/rpi/boss
	$0 --force --disable-getty
USAGE
}

while [[ $# -gt 0 ]]; do
	case "$1" in
		-u|--user) RUN_USER="$2"; shift 2;;
		-r|--root) BOSS_ROOT="$2"; shift 2;;
		-f|--force) FORCE_OVERWRITE=1; shift;;
		-d|--disable-getty) DISABLE_GETTY=1; shift;;
		-a|--allocate-tty) ALLOCATE_TTY=1; shift;;
		-n|--no-venv) SKIP_VENV=1; shift;;
		-h|--help) usage; exit 0;;
		*) echo "Unknown option: $1" >&2; usage; exit 1;;
	esac
done

# Derive BOSS_ROOT if left default but user overridden
if [[ "$BOSS_ROOT" == "/home/${DEFAULT_USER}/boss" && "$RUN_USER" != "$DEFAULT_USER" ]]; then
	BOSS_ROOT="/home/${RUN_USER}/boss"
fi

echo "==> B.O.S.S. setup starting (user=${RUN_USER} root=${BOSS_ROOT})"

if [[ $EUID -ne 0 ]]; then
	echo "[INFO] Script not run as root. Will use sudo for privileged operations."
	SUDO="sudo"
else
	SUDO=""
fi

req() {
	command -v "$1" >/dev/null 2>&1 || { echo "[ERROR] Required command '$1' not found" >&2; exit 1; }
}
req python3
req systemctl

if [[ ! -d "$BOSS_ROOT" ]]; then
	echo "[ERROR] BOSS root directory not found: $BOSS_ROOT" >&2
	exit 1
fi

echo "==> Ensuring '${RUN_USER}' is in gpio,video,audio groups"
$SUDO usermod -a -G gpio,video,audio "$RUN_USER"

VENV_PATH="$BOSS_ROOT/.venv"
PYTHON_BIN="${VENV_PATH}/bin/python"

if [[ $SKIP_VENV -eq 0 ]]; then
	if [[ ! -d "$VENV_PATH" ]]; then
		echo "==> Creating Python virtual environment (with system site packages)"
		python3 -m venv --system-site-packages "$VENV_PATH"
	else
		echo "==> Reusing existing virtual environment"
	fi
	echo "==> Upgrading pip & installing requirements"
	"$PYTHON_BIN" -m pip install --upgrade pip >/dev/null
	if [[ -f "$BOSS_ROOT/requirements/base.txt" ]]; then
		"$PYTHON_BIN" -m pip install -r "$BOSS_ROOT/requirements/base.txt"
	elif [[ -f "$BOSS_ROOT/requirements.txt" ]]; then
		"$PYTHON_BIN" -m pip install -r "$BOSS_ROOT/requirements.txt"
	else
		echo "[WARN] No requirements file found; continuing"
	fi
else
	echo "==> Skipping virtualenv creation/installation per flag"
fi

if [[ $DISABLE_GETTY -eq 1 ]]; then
	echo "==> Disabling getty@tty1 to free TTY for textual backend"
	$SUDO systemctl disable getty@tty1.service || true
	$SUDO systemctl stop getty@tty1.service || true
fi

echo "==> Preparing systemd service unit"
if [[ -f "$SERVICE_FILE" && $FORCE_OVERWRITE -ne 1 ]]; then
	echo "[INFO] Existing unit found at $SERVICE_FILE (use --force to overwrite). Backing up copy."
	$SUDO cp "$SERVICE_FILE" "${SERVICE_FILE}.${BACKUP_SUFFIX}.bak" || true
fi

cat > /tmp/${SERVICE_NAME}.service.new <<EOF
[Unit]
Description=B.O.S.S. (Buttons, Operations, Switches & Screen)
Documentation=https://github.com/derekbez/BOSSv2
After=network.target sound.target
Wants=network.target

[Service]
Type=simple
User=${RUN_USER}
Group=gpio
SupplementaryGroups=video audio

# Working directory and environment
WorkingDirectory=${BOSS_ROOT}
Environment=PYTHONPATH=${BOSS_ROOT}
Environment=BOSS_LOG_LEVEL=INFO
Environment=BOSS_CONFIG_PATH=${BOSS_ROOT}/boss/config/boss_config.json
Environment=GPIOZERO_PIN_FACTORY=lgpio
Environment=BOSS_DEV_MODE=0
Environment=BOSS_TEST_MODE=0
# Prefer automatic screen backend selection (textual primary, rich fallback)
Environment=BOSS_SCREEN_BACKEND=auto

# Optional explicit disable: set BOSS_DISABLE_TEXTUAL=1 to force rich backend

# Switch to tty1 (ignore errors if already active or insufficient perms)
ExecStartPre=-/bin/chvt 1
ExecStart=${PYTHON_BIN:-${BOSS_ROOT}/.venv/bin/python} -m boss.main
ExecReload=/bin/kill -HUP \$MAINPID

# Restart policy
Restart=on-failure
RestartSec=5
StartLimitIntervalSec=60
StartLimitBurst=5

# Resource limits
MemoryMax=512M
CPUQuota=80%

# Security hardening (allow writes only where needed)
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ReadWritePaths=${BOSS_ROOT}/boss/logs ${BOSS_ROOT}/boss/config

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=boss

EOF

# Append optional TTY allocation if requested
if [[ $ALLOCATE_TTY -eq 1 ]]; then
	cat >> /tmp/${SERVICE_NAME}.service.new <<EOF
# TTY allocation directives (enabled via --allocate-tty)
TTYPath=/dev/tty1
StandardInput=tty
TTYReset=yes
TTYVHangup=yes
TTYVTDisallocate=yes
StandardOutput=tty
StandardError=journal
# Force textual backend explicitly when we own the TTY
Environment=BOSS_SCREEN_BACKEND=textual
# Ensure getty@tty1 is stopped first if present
After=getty@tty1.service
EOF
fi

cat >> /tmp/${SERVICE_NAME}.service.new <<EOF

[Install]
WantedBy=multi-user.target
EOF

CHANGED=1
if [[ -f "$SERVICE_FILE" ]]; then
	if cmp -s /tmp/${SERVICE_NAME}.service.new "$SERVICE_FILE"; then
		CHANGED=0
		echo "==> Service file unchanged"
	else
		echo "==> Updating service file (differs from existing)"
	fi
fi

if [[ $CHANGED -eq 1 ]]; then
	$SUDO cp /tmp/${SERVICE_NAME}.service.new "$SERVICE_FILE"
fi
rm -f /tmp/${SERVICE_NAME}.service.new

echo "==> Ensuring logs directory exists & ownership set"
mkdir -p "${BOSS_ROOT}/boss/logs"
$SUDO chown -R ${RUN_USER}:${RUN_USER} "${BOSS_ROOT}/boss/logs"

echo "==> systemd daemon-reload"
$SUDO systemctl daemon-reload
echo "==> Enabling service (${SERVICE_NAME})"
$SUDO systemctl enable ${SERVICE_NAME} >/dev/null

echo ""
echo "B.O.S.S. systemd service setup complete. Next steps:"
echo "  sudo systemctl start ${SERVICE_NAME}        # Start now"
echo "  sudo journalctl -u ${SERVICE_NAME} -f       # Follow logs"
echo "  sudo systemctl status ${SERVICE_NAME}       # Status"
if [[ $DISABLE_GETTY -eq 1 ]]; then
	echo "(getty@tty1 disabled; reboot may be required if it previously owned tty1)"
fi
if [[ $CHANGED -eq 0 ]]; then
	echo "(Service unit unchanged – no restart required unless code changed)"
else
	echo "(Service unit updated – consider: sudo systemctl restart ${SERVICE_NAME})"
fi
echo ""
echo "Re-run this script after pulling updates; it is safe & idempotent." 
