#!/bin/bash

export CCACHE_DIR=${HOME}/.ccache
export CCACHE_TEMPDIR=/tmp/ccache_temp

mkdir -p "${CCACHE_DIR}" "${CCACHE_TEMPDIR}"

pushd "${HOME}/ros2_ws"

colcon build \
  --symlink-install \
  --cmake-args \
  -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_C_COMPILER_LAUNCHER=ccache \
  -DCMAKE_CXX_COMPILER_LAUNCHER=ccache

popd
