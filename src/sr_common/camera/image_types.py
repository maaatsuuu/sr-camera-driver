from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np


@dataclass(frozen=True)
class DecodedImageData:
    """NumPyへデコード済みの画像データ型"""

    data: np.ndarray
    encoding: str
    width: int
    height: int
    frame_id: str = ""
    stamp: Any | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.data, np.ndarray):
            raise TypeError("data must be a numpy.ndarray")
        if self.data.ndim < 2:
            raise ValueError("data must have at least height and width dimensions")
        if self.width <= 0 or self.height <= 0:
            raise ValueError("width and height must be positive")
        if self.data.shape[1] != self.width or self.data.shape[0] != self.height:
            raise ValueError("data shape does not match width and height")
        if not self.encoding:
            raise ValueError("encoding must not be empty")


@dataclass(frozen=True)
class EncodedImageData:
    """JPEGなどの圧縮済み画像データ型"""

    data: bytes
    format: str
    width: int | None = None
    height: int | None = None
    frame_id: str = ""
    stamp: Any | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.data, bytes):
            raise TypeError("data must be bytes")
        if not self.format:
            raise ValueError("format must not be empty")
        if self.width is not None and self.width <= 0:
            raise ValueError("width must be positive")
        if self.height is not None and self.height <= 0:
            raise ValueError("height must be positive")


@dataclass(frozen=True)
class CapturePreset:
    """GStreamerでキャプチャーする際のcamera.yaml のプリセット"""

    name: str
    width: int | None = None
    height: int | None = None
    fps_num: int | None = None
    fps_den: int | None = None
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ResolvedCameraRosConfig:
    """解決済みのROS名前設定。"""

    namespace: str
    image_topic: str = "image_raw"
    camera_info_topic: str = "camera_info"


@dataclass(frozen=True)
class GstreamerConfig:
    """GStreamer pipeline生成に必要な設定項目"""

    pipeline_template: str
    default_preset: str
    presets: dict[str, CapturePreset]
    preview_sink: str = "autovideosink"
    params: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Gscam2Config:
    """gscam2ノードへ渡すパラメータ"""

    gst_plugin_path: str = ""
    gscam_config: str = ""
    sync_sink: bool = True
    preroll: bool = False
    use_gst_timestamps: bool = False
    image_encoding: str = "rgb8"
    camera_info_url: str = ""
    camera_name: str = ""
    frame_id: str = "camera_frame"
    skip: int = 0


@dataclass(frozen=True)
class ResolvedCameraConfig:
    """envとcamera.yamlを統合した最終カメラ設定"""

    name: str
    type: str
    backend: str
    gstreamer: GstreamerConfig
    gscam2: Gscam2Config
    ros: ResolvedCameraRosConfig


__all__ = [
    "DecodedImageData",
    "EncodedImageData",
    "CapturePreset",
    "ResolvedCameraRosConfig",
    "GstreamerConfig",
    "Gscam2Config",
    "ResolvedCameraConfig",
]
