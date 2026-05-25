#!/bin/bash

export CCACHE_DIR=${HOME}/.ccache
export CCACHE_TEMPDIR=/tmp/ccache_temp
THIS_DIR="$(cd $(dirname "${BASH_SOURCE[0]}") && pwd)"

mkdir -p ${CCACHE_DIR} ${CCACHE_TEMPDIR}

# add specific build scripts for each package here
# ${THIS_DIR}/build_livox_driver.sh

pushd ${HOME}/ros2_ws

colcon build \
  --symlink-install \
  --packages-skip livox_ros_driver2 \
  --cmake-args \
  -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_C_COMPILER_LAUNCHER=ccache \
  -DCMAKE_CXX_COMPILER_LAUNCHER=ccache

popd
