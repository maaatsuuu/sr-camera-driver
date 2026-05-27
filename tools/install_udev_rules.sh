#!/bin/bash -eu

THIS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${THIS_DIR}/.." && pwd)"

RULES_SRC_DIR="${REPO_ROOT}/udev"
RULES_DST_DIR="/etc/udev/rules.d"

usage() {
  echo "Usage: sudo $(basename $0) [OPTIONS]"
  echo "Options:"
  echo " -h    show this help"
}

while getopts h OPT; do
  case "${OPT}" in
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

if [ "${EUID}" -ne 0 ]; then
  echo "run with sudo: sudo $0" >&2
  exit 1
fi

if [ ! -d "${RULES_SRC_DIR}" ]; then
  echo "udev rule directory is not found: ${RULES_SRC_DIR}" >&2
  exit 1
fi

shopt -s nullglob
rule_files=("${RULES_SRC_DIR}"/*.rules)
if [ "${#rule_files[@]}" -eq 0 ]; then
  echo "udev rule file is not found: ${RULES_SRC_DIR}/*.rules" >&2
  exit 1
fi

for src_file in "${rule_files[@]}"; do
  dst_file="${RULES_DST_DIR}/$(basename "${src_file}")"
  if [ -f "${dst_file}" ] && cmp -s "${src_file}" "${dst_file}"; then
    echo "skip unchanged: ${dst_file}"
    continue
  fi
  cp "${src_file}" "${dst_file}"
  chmod 644 "${dst_file}"
  echo "installed: ${dst_file}"
done

udevadm control --reload-rules
udevadm trigger

echo "udev rules are ready."
echo "re-plug USB cameras if they are already connected."
