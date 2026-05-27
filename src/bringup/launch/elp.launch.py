from __future__ import annotations

import os
from pathlib import Path
import sys

from ament_index_python.packages import get_package_share_directory
from ament_index_python.packages import PackageNotFoundError
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch import LaunchDescription
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

# TODO: 将来的にsr_commonの処理内容をROS依存にするか検討が必要？
_SOURCE_DIR = Path(os.environ.get("SOURCE_DIR", Path.home() / "ros2_ws" / "src"))
if str(_SOURCE_DIR) not in sys.path:
    sys.path.insert(0, str(_SOURCE_DIR))

from sr_common.camera.config_loader import load_camera_config
from sr_common.camera.gscam2_launch_builder import build_gscam2_launch_node


def generate_launch_description() -> LaunchDescription:
    """ELPカメラ用launchの生成"""
    config = load_camera_config(_camera_config_path("elp"))
    return LaunchDescription([
        DeclareLaunchArgument(
            "rviz",
            default_value="false",
            description="Start RViz.",
        ),
        DeclareLaunchArgument(
            "rviz_config",
            default_value=str(_rviz_config_path("elp")),
            description="RViz config file.",
        ),
        build_gscam2_launch_node(config),
        Node(
            package="rviz2",
            executable="rviz2",
            name="rviz2",
            arguments=["-d", LaunchConfiguration("rviz_config")],
            condition=IfCondition(LaunchConfiguration("rviz")),
            output="screen",
        ),
    ])


def _camera_config_path(camera_type: str) -> Path:
    """camera.yamlパスの生成"""
    return _bringup_dir() / "config" / camera_type / "camera.yaml"


def _rviz_config_path(camera_type: str) -> Path:
    """RViz設定パスの生成"""
    return _bringup_dir() / "config" / camera_type / "image.rviz"


def _bringup_dir() -> Path:
    """bringup共有ディレクトリの取得"""
    try:
        return Path(get_package_share_directory("bringup"))
    except PackageNotFoundError:
        return _SOURCE_DIR / "bringup"
