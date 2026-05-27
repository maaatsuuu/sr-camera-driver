from __future__ import annotations

import os
from pathlib import Path
import sys

from ament_index_python.packages import get_package_share_directory
from ament_index_python.packages import PackageNotFoundError
from launch import LaunchDescription

_SOURCE_DIR = Path(os.environ.get("SOURCE_DIR", Path.home() / "ros2_ws" / "src"))
if str(_SOURCE_DIR) not in sys.path:
    sys.path.insert(0, str(_SOURCE_DIR))

from sr_common.camera.config_loader import load_camera_config
from sr_common.camera.gscam2_launch_builder import build_gscam2_launch_node


def generate_launch_description() -> LaunchDescription:
    """RouteCAM用launchの生成"""
    config = load_camera_config(_camera_config_path("routecam"))
    return LaunchDescription([
        build_gscam2_launch_node(config),
    ])


def _camera_config_path(camera_type: str) -> Path:
    """camera.yamlパスの生成"""
    try:
        bringup_dir = Path(get_package_share_directory("bringup"))
    except PackageNotFoundError:
        bringup_dir = _SOURCE_DIR / "bringup"
    return bringup_dir / "config" / camera_type / "camera.yaml"
