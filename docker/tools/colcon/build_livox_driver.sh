#!/bin/bash

export CCACHE_DIR=${HOME}/.ccache
export CCACHE_TEMPDIR=/tmp/ccache_temp

mkdir -p ${CCACHE_DIR} ${CCACHE_TEMPDIR}

: "${SOURCE_DIR:=${HOME}/ros2_ws/src}"

LIVOX_DRIVER_DIR=${SOURCE_DIR}/third_party/livox/livox_ros_driver2

if [ -z "${ROS_DISTRO:-}" ]; then
  echo "ROS_DISTRO is not set"
  exit 1
fi

if [ ! -f ${LIVOX_DRIVER_DIR}/package_ROS2.xml ]; then
  echo "package_ROS2.xml is not found: ${LIVOX_DRIVER_DIR}/package_ROS2.xml"
  exit 1
fi

cp ${LIVOX_DRIVER_DIR}/package_ROS2.xml ${LIVOX_DRIVER_DIR}/package.xml

pushd ${HOME}/ros2_ws

colcon build \
  --symlink-install \
  --packages-select livox_ros_driver2 \
  --cmake-args \
  -DROS_EDITION=ROS2 \
  -DDISTRO_ROS=${ROS_DISTRO} \
  -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_C_COMPILER_LAUNCHER=ccache \
  -DCMAKE_CXX_COMPILER_LAUNCHER=ccache

popd
