#!/bin/bash

unset ROS_DISTRO
unset DOCKER_IMAGE_NAME
unset IMAGE_TAG
THIS_DIR="$(cd $(dirname "${BASH_SOURCE[0]}") && pwd)"
CONFIG_FILE="${THIS_DIR}/image.env"

if [[ -f "${CONFIG_FILE}" ]]; then
  # shellcheck disable=SC1090
  source "${CONFIG_FILE}"
fi

: "${ROS_DISTRO:=jazzy}"
: "${DOCKER_IMAGE_NAME:=kjm/ros2/${ROS_DISTRO}}"
: "${IMAGE_TAG:=latest}"

CURRENT_USER="${USER:-$(id -un)}"

while getopts "t:h" opt; do
  case ${opt} in
    t)
      IMAGE_TAG="${OPTARG}"
      ;;
    h)
      echo "Usage: $(basename "$0") [OPTIONS]"
      echo "Options:"
      echo " -t TAG            docker image tag"
      echo "Attach to a running container created from ${DOCKER_IMAGE_NAME}:${IMAGE_TAG}."
      exit 0
      ;;
    \?)
      echo "Invalid option: -${OPTARG}" >&2
      exit 1
      ;;
  esac
done

IMAGE="${DOCKER_IMAGE_NAME}:${IMAGE_TAG}"

echo "[ROS_DISTRO] ${ROS_DISTRO}"
echo "[DOCKER_IMAGE_NAME] ${DOCKER_IMAGE_NAME}"
echo "[IMAGE_TAG] ${IMAGE_TAG}"
echo "[Docker Image] ${IMAGE}"

mapfile -t MATCHED_CONTAINERS < <(docker ps --filter "ancestor=${IMAGE}" --format '{{.Names}}\t{{.Image}}')

if [[ ${#MATCHED_CONTAINERS[@]} -eq 0 ]]; then
  echo "Error: No running container found for image '${IMAGE}'."
  exit 1
fi

CONTAINER_NAME=""
if [[ ${#MATCHED_CONTAINERS[@]} -eq 1 ]]; then
  CONTAINER_NAME="${MATCHED_CONTAINERS[0]%%$'\t'*}"
else
  echo "Multiple containers found for image '${IMAGE}':"
  for index in "${!MATCHED_CONTAINERS[@]}"; do
    container_name="${MATCHED_CONTAINERS[${index}]%%$'\t'*}"
    container_image="${MATCHED_CONTAINERS[${index}]#*$'\t'}"
    echo "[${index}] ${container_name} (${container_image})"
  done

  while true; do
    read -r -p "Select container number [0-$(( ${#MATCHED_CONTAINERS[@]} - 1 ))]: " selection
    if [[ ${selection} =~ ^[0-9]+$ ]] && (( selection < ${#MATCHED_CONTAINERS[@]} )); then
      CONTAINER_NAME="${MATCHED_CONTAINERS[${selection}]%%$'\t'*}"
      break
    fi
    echo "Invalid selection: ${selection}"
  done
fi

echo "[Attach Container] ${CONTAINER_NAME}"
docker exec -it "${CONTAINER_NAME}" gosu "${CURRENT_USER}:${CURRENT_USER}" /bin/bash
