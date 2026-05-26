from __future__ import annotations

from typing import Any

from launch_ros.actions import Node

from sr_common.camera.gstreamer_pipeline import build_gstreamer_pipeline
from sr_common.camera.image_types import ResolvedCameraConfig


def build_gscam2_parameters(
    config: ResolvedCameraConfig,
    preset_name: str | None = None,
) -> dict[str, Any]:
    """gscam2 parameterの生成"""
    gscam2 = config.gscam2
    return {
        "gst_plugin_path": gscam2.gst_plugin_path,
        "gscam_config": _resolve_gscam_config(config, preset_name),
        "sync_sink": gscam2.sync_sink,
        "preroll": gscam2.preroll,
        "use_gst_timestamps": gscam2.use_gst_timestamps,
        "image_encoding": _resolve_image_encoding(config, preset_name),
        "camera_info_url": gscam2.camera_info_url,
        "camera_name": gscam2.camera_name,
        "frame_id": gscam2.frame_id,
        "skip": gscam2.skip,
    }


def build_gscam2_remappings(
    config: ResolvedCameraConfig,
) -> list[tuple[str, str]]:
    """gscam2 topic remapの生成"""
    remappings: list[tuple[str, str]] = []
    if config.ros.image_topic != "image_raw":
        remappings.append(("image_raw", config.ros.image_topic))
        remappings.append(("image_raw/compressed", _compressed_topic(config.ros.image_topic)))
    if config.ros.camera_info_topic != "camera_info":
        remappings.append(("camera_info", config.ros.camera_info_topic))
    return remappings


def build_gscam2_launch_node(
    config: ResolvedCameraConfig,
    preset_name: str | None = None,
    node_name: str = "gscam2",
    output: str = "screen",
) -> Node:
    """gscam2 launch Nodeの生成"""
    return Node(
        package="gscam2",
        executable="gscam_main",
        name=node_name,
        namespace=config.ros.namespace,
        output=output,
        parameters=[build_gscam2_parameters(config, preset_name=preset_name)],
        remappings=build_gscam2_remappings(config),
    )


def _resolve_gscam_config(
    config: ResolvedCameraConfig,
    preset_name: str | None,
) -> str:
    """gscam_config値の解決"""
    if config.gscam2.gscam_config:
        return config.gscam2.gscam_config
    return build_gstreamer_pipeline(config, preset_name=preset_name)


def _resolve_image_encoding(
    config: ResolvedCameraConfig,
    preset_name: str | None,
) -> str:
    """image_encoding値の解決"""
    if config.gscam2.gscam_config or preset_name is None:
        return config.gscam2.image_encoding
    preset = config.gstreamer.presets[preset_name]
    return str(preset.image_encoding or config.gscam2.image_encoding)


def _compressed_topic(topic: str) -> str:
    """compressed topic名の生成"""
    if topic.endswith("/compressed"):
        return topic
    return f"{topic}/compressed"


__all__ = [
    "build_gscam2_parameters",
    "build_gscam2_remappings",
    "build_gscam2_launch_node",
]
