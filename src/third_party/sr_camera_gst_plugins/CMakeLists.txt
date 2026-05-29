cmake_minimum_required(VERSION 3.8)
project(sr_camera_gst_plugins VERSION 0.0.0 LANGUAGES C)

find_package(ament_cmake REQUIRED)
find_package(PkgConfig REQUIRED)

pkg_check_modules(GSTREAMER REQUIRED IMPORTED_TARGET
  gstreamer-1.0
  gstreamer-rtp-1.0
)

add_library(gstroutecamjpegfix SHARED
  src/gstroutecamjpegfix.c
)

target_compile_features(gstroutecamjpegfix PRIVATE c_std_99)
target_compile_definitions(gstroutecamjpegfix PRIVATE
  PACKAGE="${PROJECT_NAME}"
  PACKAGE_VERSION="${PROJECT_VERSION}"
)
target_compile_options(gstroutecamjpegfix PRIVATE
  -Wall
  -Wextra
  -Wpedantic
)
target_link_libraries(gstroutecamjpegfix PRIVATE
  PkgConfig::GSTREAMER
)

install(TARGETS gstroutecamjpegfix
  LIBRARY DESTINATION lib/gstreamer-1.0
)

ament_package()
