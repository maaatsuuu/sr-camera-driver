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

while getopts t:h OPT; do
  case ${OPT} in
    t) IMAGE_TAG="${OPTARG}" ;;
    h)
      echo "Usage: $(basename $0) [OPTIONS]"
      echo "Options:"
      echo " -t TAG            docker image tag"
      exit 1
      ;;
  esac
done

IMAGE="${DOCKER_IMAGE_NAME}:${IMAGE_TAG}"

echo "[ROS_DISTRO] ${ROS_DISTRO}"
echo "[DOCKER_IMAGE_NAME] ${DOCKER_IMAGE_NAME}"
echo "[IMAGE_TAG] ${IMAGE_TAG}"
echo "[Docker Image] ${IMAGE}"

docker build \
  -f "${THIS_DIR}/Dockerfile" \
  --build-arg ROS_DISTRO="${ROS_DISTRO}" \
  -t "${IMAGE}" \
  "${THIS_DIR}/.."
