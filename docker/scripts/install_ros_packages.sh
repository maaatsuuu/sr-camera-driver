#!/bin/bash -eu

sudo apt install -y \
  ros-${ROS_DISTRO}-rmw-cyclonedds-cpp \
  ros-${ROS_DISTRO}-camera-calibration-parsers \
  ros-${ROS_DISTRO}-camera-info-manager \
  ros-${ROS_DISTRO}-class-loader \
  ros-${ROS_DISTRO}-cv-bridge \
  ros-${ROS_DISTRO}-rosbag2-storage-mcap \
  ros-${ROS_DISTRO}-rviz2 \
  ros-${ROS_DISTRO}-image-transport \
  ros-${ROS_DISTRO}-compressed-image-transport \
  ros-${ROS_DISTRO}-image-transport-plugins \
  pkg-config \
  libgstreamer1.0-dev \
  libgstreamer-plugins-base1.0-dev \
  python3-gi \
  python3-numpy \
  python3-opencv \
  gir1.2-gstreamer-1.0 \
  gir1.2-gst-plugins-base-1.0 \
  gstreamer1.0-tools \
  gstreamer1.0-plugins-base \
  gstreamer1.0-plugins-good \
  gstreamer1.0-plugins-bad \
  gstreamer1.0-plugins-ugly \
  gstreamer1.0-libav \
  gstreamer1.0-x \
  v4l-utils \
  python3-colcon-common-extensions \
  python3-vcstool
