#!/bin/bash

pushd ${HOME}/ros2_ws

colcon test \
  --event-handlers console_direct+ \
  --ctest-args \
  --output-on-failure

popd
