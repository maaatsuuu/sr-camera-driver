#!/bin/bash -eu

THIS_DIR="$(cd $(dirname "${BASH_SOURCE[0]}") && pwd)"
SRC_DIR="$(cd "${THIS_DIR}/.." && pwd)"

LIVOX_VENDOR_CONFIG_DIR="${SRC_DIR}/third_party/livox/livox_ros_driver2/config"
LIVOX_BRINGUP_CONFIG_DIR="${SRC_DIR}/bringup/config/livox"
HOST_CFG_TEMPLATE="${THIS_DIR}/host_cfg.env.template"
HOST_CFG_FILE="${THIS_DIR}/host_cfg.env"

OVERWRITE=0

usage() {
  echo "Usage: $(basename $0) [OPTIONS]"
  echo "Options:"
  echo " -f    overwrite existing local assets"
  echo " -h    show this help"
}

while getopts fh OPT; do
  case "${OPT}" in
    f) OVERWRITE=1 ;;
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

copy_file() {
  local src_file="$1"
  local dst_file="$2"

  if [ ! -f "${src_file}" ]; then
    echo "missing source: ${src_file}" >&2
    exit 1
  fi

  if [ -e "${dst_file}" ] && [ "${OVERWRITE}" -ne 1 ]; then
    echo "skip existing: ${dst_file}"
    return
  fi

  cp "${src_file}" "${dst_file}"
  echo "copied: ${src_file} -> ${dst_file}"
}

mkdir -p "${LIVOX_BRINGUP_CONFIG_DIR}"

copy_file "${LIVOX_VENDOR_CONFIG_DIR}/MID360_config.json" \
  "${LIVOX_BRINGUP_CONFIG_DIR}/MID360_config.json"
copy_file "${LIVOX_VENDOR_CONFIG_DIR}/MID360s_config.json" \
  "${LIVOX_BRINGUP_CONFIG_DIR}/MID360s_config.json"
copy_file "${LIVOX_VENDOR_CONFIG_DIR}/display_point_cloud_ROS2.rviz" \
  "${LIVOX_BRINGUP_CONFIG_DIR}/display_point_cloud_ROS2.rviz"
copy_file "${HOST_CFG_TEMPLATE}" "${HOST_CFG_FILE}"

echo "Livox assets are ready under ${LIVOX_BRINGUP_CONFIG_DIR}"
