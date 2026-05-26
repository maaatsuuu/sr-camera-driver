#!/bin/bash -eu

THIS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${THIS_DIR}/.." && pwd)"

HOST_CFG_TEMPLATE="${THIS_DIR}/host_cfg.env.template"
HOST_CFG_FILE="${REPO_ROOT}/docker/host_cfg.env"

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

copy_file "${HOST_CFG_TEMPLATE}" "${HOST_CFG_FILE}"

echo "Host config is ready: ${HOST_CFG_FILE}"
