from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any, Mapping

import yaml

from sr_common.camera.image_types import CapturePreset
from sr_common.camera.image_types import Gscam2Config
from sr_common.camera.image_types import GstreamerConfig
from sr_common.camera.image_types import ResolvedCameraConfig
from sr_common.camera.image_types import ResolvedCameraRosConfig


_ENV_PATTERN = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}")
_GSTREAMER_PARAM_EXCLUDED_KEYS = {
    "pipeline_template",
    "default_preset",
    "presets",
    "preview_sink",
}


def load_camera_config(
    config_path: str | Path,
    env: Mapping[str, str] | None = None,
) -> ResolvedCameraConfig:
    """camera.yaml と env から最終カメラ設定を作成"""
    env_map = os.environ if env is None else env
    config = _load_yaml(config_path)

    camera = _require_mapping(config, "camera")
    gstreamer = _require_mapping(config, "gstreamer")
    gscam2 = _require_mapping(config, "gscam2")
    ros = _require_mapping(config, "ros")

    return ResolvedCameraConfig(
        name=str(_resolve_env(camera["name"], env_map)),
        type=str(_resolve_env(camera["type"], env_map)),
        backend=str(_resolve_env(camera["backend"], env_map)),
        gstreamer=_create_gstreamer_config(gstreamer, env_map),
        gscam2=_create_gscam2_config(gscam2, env_map),
        ros=_create_ros_config(ros, env_map),
    )


def _load_yaml(config_path: str | Path) -> dict[str, Any]:
    """YAMLファイルの読み込み。"""
    path = Path(config_path)
    if not path.is_file():
        raise FileNotFoundError(f"camera config is not found: {path}")

    data = yaml.safe_load(path.read_text())
    if not isinstance(data, dict):
        raise ValueError(f"camera config must be a mapping: {path}")
    return data


def _require_mapping(data: Mapping[str, Any], key: str) -> dict[str, Any]:
    """必須セクションの取得。"""
    value = data.get(key)
    if not isinstance(value, dict):
        raise ValueError(f"camera config section must be a mapping: {key}")
    return value


def _resolve_env(value: Any, env: Mapping[str, str]) -> Any:
    """${VAR}形式の環境変数展開。"""
    if isinstance(value, str):
        return _ENV_PATTERN.sub(lambda m: _env_value(m.group(1), env), value)
    if isinstance(value, list):
        return [_resolve_env(item, env) for item in value]
    if isinstance(value, dict):
        return {key: _resolve_env(item, env) for key, item in value.items()}
    return value


def _env_value(name: str, env: Mapping[str, str]) -> str:
    """環境変数値の取得。"""
    if name not in env:
        raise KeyError(f"environment variable is not set: {name}")
    return env[name]


def _create_gstreamer_config(
    data: Mapping[str, Any],
    env: Mapping[str, str],
) -> GstreamerConfig:
    """GStreamer設定オブジェクトの生成。"""
    presets_data = data.get("presets", {})
    if not isinstance(presets_data, dict):
        raise ValueError("gstreamer.presets must be a mapping")

    presets = {
        name: _create_capture_preset(name, preset_data)
        for name, preset_data in presets_data.items()
    }

    params = {
        key: _resolve_env(value, env)
        for key, value in data.items()
        if key not in _GSTREAMER_PARAM_EXCLUDED_KEYS
    }

    return GstreamerConfig(
        pipeline_template=str(data["pipeline_template"]),
        default_preset=str(_resolve_env(data["default_preset"], env)),
        presets=presets,
        preview_sink=str(_resolve_env(data.get("preview_sink", "autovideosink"), env)),
        params=params,
    )


def _create_capture_preset(name: str, data: Any) -> CapturePreset:
    """キャプチャープリセットの生成。"""
    if data is None:
        data = {}
    if not isinstance(data, dict):
        raise ValueError(f"capture preset must be a mapping: {name}")

    known_keys = {"width", "height", "fps_num", "fps_den"}
    return CapturePreset(
        name=str(name),
        width=data.get("width"),
        height=data.get("height"),
        fps_num=data.get("fps_num"),
        fps_den=data.get("fps_den"),
        extra={key: value for key, value in data.items() if key not in known_keys},
    )


def _create_gscam2_config(
    data: Mapping[str, Any],
    env: Mapping[str, str],
) -> Gscam2Config:
    """gscam2設定オブジェクトの生成。"""
    resolved = _resolve_env(dict(data), env)
    return Gscam2Config(
        gst_plugin_path=str(resolved.get("gst_plugin_path", "")),
        gscam_config=str(resolved.get("gscam_config", "")),
        sync_sink=bool(resolved.get("sync_sink", True)),
        preroll=bool(resolved.get("preroll", False)),
        use_gst_timestamps=bool(resolved.get("use_gst_timestamps", False)),
        image_encoding=str(resolved.get("image_encoding", "rgb8")),
        camera_info_url=str(resolved.get("camera_info_url", "")),
        camera_name=str(resolved.get("camera_name", "")),
        frame_id=str(resolved.get("frame_id", "camera_frame")),
        skip=int(resolved.get("skip", 0)),
    )


def _create_ros_config(
    data: Mapping[str, Any],
    env: Mapping[str, str],
) -> ResolvedCameraRosConfig:
    """ROS名前設定オブジェクトの生成。"""
    resolved = _resolve_env(dict(data), env)
    return ResolvedCameraRosConfig(
        namespace=str(resolved["namespace"]),
        image_topic=str(resolved.get("image_topic", "image_raw")),
        camera_info_topic=str(resolved.get("camera_info_topic", "camera_info")),
    )


__all__ = ["load_camera_config"]
