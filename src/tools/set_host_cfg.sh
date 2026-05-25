#!/bin/bash -eu

THIS_DIR="$(cd $(dirname "${BASH_SOURCE[0]}") && pwd)"
SRC_DIR="$(cd "${THIS_DIR}/.." && pwd)"

HOST_CFG_FILE="${THIS_DIR}/host_cfg.env"
LIVOX_BRINGUP_CONFIG_DIR="${SRC_DIR}/bringup/config/livox"
LIVOX_MID360_CONFIG="${LIVOX_BRINGUP_CONFIG_DIR}/MID360_config.json"
LIVOX_MID360S_CONFIG="${LIVOX_BRINGUP_CONFIG_DIR}/MID360s_config.json"

usage() {
  echo "Usage: $(basename $0) [OPTIONS]"
  echo "Options:"
  echo " -c FILE    host config env file"
  echo " -h         show this help"
}

while getopts c:h OPT; do
  case ${OPT} in
    c) HOST_CFG_FILE="${OPTARG}" ;;
    h)
      usage
      exit 0
      ;;
    *)
      usage
      exit 1
      ;;
  esac
done

if [ ! -f "${HOST_CFG_FILE}" ]; then
  echo "host config file is not found: ${HOST_CFG_FILE}" >&2
  echo "run ./src/tools/copy_assets.sh first, then edit src/tools/host_cfg.env" >&2
  exit 1
fi

# shellcheck disable=SC1090
source "${HOST_CFG_FILE}"

: "${LIVOX_HOST_IP:?LIVOX_HOST_IP is not set}"
: "${LIVOX_MID360_IP:?LIVOX_MID360_IP is not set}"
: "${LIVOX_MID360S_IP:?LIVOX_MID360S_IP is not set}"

if [ ! -f "${LIVOX_MID360_CONFIG}" ]; then
  echo "MID360 config is not found: ${LIVOX_MID360_CONFIG}" >&2
  exit 1
fi

if [ ! -f "${LIVOX_MID360S_CONFIG}" ]; then
  echo "MID360s config is not found: ${LIVOX_MID360S_CONFIG}" >&2
  exit 1
fi

export LIVOX_HOST_IP
export LIVOX_MID360_IP
export LIVOX_MID360S_IP
export LIVOX_MID360_CONFIG
export LIVOX_MID360S_CONFIG

python3 - <<'PY'
import json
import os
from pathlib import Path


def write_json(path, data):
    path.write_text(json.dumps(data, indent=2) + "\n")


host_ip = os.environ["LIVOX_HOST_IP"]
mid360_ip = os.environ["LIVOX_MID360_IP"]
mid360s_ips = os.environ["LIVOX_MID360S_IP"].split()

mid360_path = Path(os.environ["LIVOX_MID360_CONFIG"])
mid360 = json.loads(mid360_path.read_text())
host_net_info = mid360["MID360"]["host_net_info"]
for key in ("cmd_data_ip", "push_msg_ip", "point_data_ip", "imu_data_ip"):
    host_net_info[key] = host_ip
for lidar_config in mid360["lidar_configs"]:
    lidar_config["ip"] = mid360_ip
write_json(mid360_path, mid360)

mid360s_path = Path(os.environ["LIVOX_MID360S_CONFIG"])
mid360s = json.loads(mid360s_path.read_text())
for host_net_info in mid360s["Mid360s"]["host_net_info"]:
    host_net_info["host_ip"] = host_ip
lidar_configs = mid360s["lidar_configs"]
if len(lidar_configs) != len(mid360s_ips):
    if len(lidar_configs) == 1:
        lidar_configs[0]["ip"] = mid360s_ips[0]
    else:
        raise SystemExit(
            "LIVOX_MID360S_IP count must match MID360s lidar_configs count"
        )
else:
    for lidar_config, lidar_ip in zip(lidar_configs, mid360s_ips):
        lidar_config["ip"] = lidar_ip
write_json(mid360s_path, mid360s)
PY

echo "Updated Livox config files:"
echo "  ${LIVOX_MID360_CONFIG}"
echo "  ${LIVOX_MID360S_CONFIG}"
echo
echo "Frame and topic settings are loaded from host_cfg.env by the container shell."
