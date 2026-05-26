#!/usr/bin/env bash
set -euo pipefail

THIS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

RULES_SRC="${THIS_DIR}/../udev/99-elp48mp-usb-camera.rules"
RULES_DST="/etc/udev/rules.d/99-elp48mp-usb-camera.rules"

echo "[INFO] Installing udev rules for ELP 48MP USB camera"

# --- sanity check -----------------------------------------------------------
if [[ ! -f "${RULES_SRC}" ]]; then
  echo "[ERROR] Rules file not found: ${RULES_SRC}" >&2
  exit 1
fi

# --- require sudo -----------------------------------------------------------
if [[ ${EUID} -ne 0 ]]; then
  echo "[ERROR] This script must be run with sudo"
  echo "        Try: sudo $0"
  exit 1
fi

# --- install rules (idempotent) ---------------------------------------------
if [[ -f "${RULES_DST}" ]]; then
  if cmp -s "${RULES_SRC}" "${RULES_DST}"; then
    echo "[INFO] udev rules already installed (no changes)"
  else
    echo "[INFO] Updating existing udev rules"
    cp "${RULES_SRC}" "${RULES_DST}"
  fi
else
  echo "[INFO] Installing new udev rules"
  cp "${RULES_SRC}" "${RULES_DST}"
fi

# --- permissions ------------------------------------------------------------
chmod 666 "${RULES_DST}"

# --- reload udev ------------------------------------------------------------
echo "[INFO] Reloading udev rules"
udevadm control --reload-rules
udevadm trigger

# --- dialout group ----------------------------------------------------------
TARGET_USER="${SUDO_USER:-}"

if [[ -n "${TARGET_USER}" ]]; then
  if id -nG "${TARGET_USER}" | grep -qw dialout; then
    echo "[INFO] User '${TARGET_USER}' already in dialout group"
  else
    echo "[INFO] Adding user '${TARGET_USER}' to dialout group"
    usermod -aG dialout "${TARGET_USER}"
    echo "[INFO] Re-login required for group change to take effect"
  fi
else
  echo "[WARN] Could not determine non-root user for dialout group"
fi

echo "[INFO] Done."
echo "[INFO] Check with:"
echo "       ls -l /dev/usbcam-elp48mp-1"
echo "[INFO] Re-plug the USB camera if it is already connected."