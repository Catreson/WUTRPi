#!/bin/sh -e
# Renders rc.local.template with the real ntrip credentials and installs it
# as /etc/rc.local. Run as root: sudo ./install_rc_local.sh

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CRED_FILE="$SCRIPT_DIR/ntrip_credentials.sh"

if [ ! -f "$CRED_FILE" ]; then
    echo "Missing $CRED_FILE - copy ntrip_credentials.sh.example to ntrip_credentials.sh and fill in your ASG-EUPOS account" >&2
    exit 1
fi

. "$CRED_FILE"

: "${NTRIP_MOUNTPOINT:=RADM_RTCM_3_2}"

if [ -z "$NTRIP_USER" ] || [ -z "$NTRIP_PASS" ]; then
    echo "NTRIP_USER / NTRIP_PASS not set in $CRED_FILE" >&2
    exit 1
fi

if ! command -v envsubst >/dev/null 2>&1; then
    echo "envsubst not found - install it with: sudo apt install gettext-base" >&2
    exit 1
fi

export NTRIP_USER NTRIP_PASS NTRIP_MOUNTPOINT
envsubst '${NTRIP_USER} ${NTRIP_PASS} ${NTRIP_MOUNTPOINT}' < "$SCRIPT_DIR/rc.local.template" > /etc/rc.local
chmod +x /etc/rc.local
echo "Installed /etc/rc.local"
