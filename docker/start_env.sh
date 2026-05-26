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

: "${IMAGE:=${DOCKER_IMAGE_NAME}:${IMAGE_TAG}}"
: "${WORKSPACE_DIR:=${THIS_DIR}/ws}"
: "${SOURCE_DIR:=${THIS_DIR}/../src}"

USER_ID=$(id -u ${USER})
GROUP_ID=$(id -g ${USER})
COMMAND="${USER} ${USER_ID} ${GROUP_ID}"

NAME=""
RUNTIME=""

# add camera device link if available
CAMERA_LINK="/dev/usbcam-elp48mp-1"
if [[ -e "${CAMERA_LINK}" ]]; then
  CAMERA_REAL="$(readlink -f "${CAMERA_LINK}")"
  RUNTIME+=" --device=${CAMERA_REAL}:${CAMERA_LINK}"
else
  echo "[WARN] USB camera device not found: ${CAMERA_LINK}"
fi

while getopts n:t:w:gh OPT; do
  case ${OPT} in
    n)
      NAME="--name=${OPTARG}"
      echo "[Docker Container Name] ${OPTARG}"
      ;;
    t) IMAGE="${DOCKER_IMAGE_NAME}:${OPTARG}" ;;
    w) WORKSPACE_DIR="${OPTARG}" ;;
    g) RUNTIME+="--runtime=nvidia" ;;
    h)
      echo "Usage: $(basename $0) [OPTIONS]"
      echo "Options:"
      echo " -n NAME           docker container name"
      echo " -t TAG            docker image tag"
      echo " -w WORKSPACE_DIR  workspace directory"
      echo " -g                nvidia runtime"
      exit 1
      ;;
  esac
done

ws_dir="$(realpath -m -- "$WORKSPACE_DIR")"
src_dir="$(realpath -m -- "$SOURCE_DIR")"
home_dir="$(realpath -m -- "$HOME")"
if [[ "${ws_dir}" == "${home_dir}" ]]; then
  echo "WORKSPACE_DIR must be under home directory"
  exit 1
fi
if [[ "${ws_dir}" != "${home_dir}/"* ]]; then
  echo "WORKSPACE_DIR must be under home directory"
  exit 1
fi

echo "[Docker Image] ${IMAGE}"
echo "[workspace] ${ws_dir}"
echo "[source] ${src_dir}"
echo "[RUNTIME] ${RUNTIME}"

# mkdir -p ${WORKSPACE_DIR}/src
mkdir -p "${ws_dir}"
mkdir -p "${src_dir}"

NETWORK_MODE="--network host"
WORKING_DIR="-w=${HOME}/ros2_ws"
DISPLAY_VALUE="${DISPLAY:-:0}"
ENVIRONMENT="-e DISPLAY=${DISPLAY_VALUE} \
             -e ROS_DISTRO=${ROS_DISTRO} \
             -e NVIDIA_VISIBLE_DEVICES=all \
             -e NVIDIA_DRIVER_CAPABILITIES=compute,graphics,utility \
             -e QT_X11_NO_MITSHM=1 \
             -e TZ=Asia/Tokyo \
             -e WORKSPACE_DIR=${HOME}/ros2_ws \
             -e SOURCE_DIR=${HOME}/ros2_ws/src"
VOLUMES="--mount type=bind,src=${HOME}/.ssh,dst=${HOME}/.ssh \
         --mount type=bind,src=${HOME}/.ros,dst=${HOME}/.ros \
         --mount type=bind,src=${HOME}/.gitconfig,dst=${HOME}/.gitconfig \
         --mount type=bind,src=${ws_dir},dst=${HOME}/ros2_ws \
         --mount type=bind,src=${src_dir},dst=${HOME}/ros2_ws/src \
         --mount type=bind,src=${THIS_DIR}/tools,dst=${HOME}/tools \
         --mount type=bind,src=/tmp/.X11-unix,dst=/tmp/.X11-unix "
#  --mount type=bind,src=/dev/snd,dst=/dev/snd,readonly "

if [ -e ${HOME}/.ccache ]; then
  VOLUMES+="--mount type=bind,src=${HOME}/.ccache,dst=${HOME}/.ccache "
fi
# Japanese input support
if [ -e /run/user/${USER_ID}/bus ]; then
  ENVIRONMENT+=" -e DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/${USER_ID}/bus "
  VOLUMES+="--mount type=bind,src=/run/user/${USER_ID}/bus,dst=/run/user/${USER_ID}/bus "
fi

xhost + local:${USER}
docker run -it ${RUNTIME} ${NETWORK_MODE} ${WORKING_DIR} ${ENVIRONMENT} ${VOLUMES} ${NAME} --privileged --rm ${IMAGE} ${COMMAND}
