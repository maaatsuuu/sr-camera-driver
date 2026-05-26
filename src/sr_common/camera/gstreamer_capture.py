from __future__ import annotations

from typing import Any

import numpy as np

from sr_common.camera.gstreamer_pipeline import build_gstreamer_pipeline
from sr_common.camera.image_types import CapturePreset
from sr_common.camera.image_types import DecodedImageData
from sr_common.camera.image_types import EncodedImageData
from sr_common.camera.image_types import ResolvedCameraConfig


_APP_SINK_NAME = "sr_camera_capture_sink"


def capture_encoded_image(
    config: ResolvedCameraConfig,
    preset_name: str | None = None,
    timeout_sec: float = 5.0,
) -> EncodedImageData:
    """圧縮画像の1フレーム取得"""
    preset = _get_capture_preset(config, preset_name)
    if preset.image_encoding != "jpeg":
        raise ValueError("encoded capture requires a jpeg preset")

    sample = _pull_sample(
        _build_appsink_pipeline(config, preset_name=preset_name),
        timeout_sec=timeout_sec,
    )
    data, width, height = _sample_bytes(sample)
    return EncodedImageData(
        data=data,
        format="jpeg",
        width=width or preset.width,
        height=height or preset.height,
        frame_id=config.gscam2.frame_id,
    )


def capture_decoded_image(
    config: ResolvedCameraConfig,
    preset_name: str | None = None,
    encoding: str = "rgb8",
    timeout_sec: float = 5.0,
) -> DecodedImageData:
    """デコード済み画像の1フレーム取得"""
    preset = _get_capture_preset(config, preset_name)
    pipeline = _build_decoded_pipeline(config, preset, preset_name, encoding)
    sample = _pull_sample(pipeline, timeout_sec=timeout_sec)
    data, width, height = _sample_bytes(sample)
    image = _bytes_to_array(data, width, height, encoding)
    return DecodedImageData(
        data=image,
        encoding=encoding,
        width=width,
        height=height,
        frame_id=config.gscam2.frame_id,
    )


def _build_decoded_pipeline(
    config: ResolvedCameraConfig,
    preset: CapturePreset,
    preset_name: str | None,
    encoding: str,
) -> str:
    """デコード用pipelineの生成"""
    pipeline = build_gstreamer_pipeline(config, preset_name=preset_name)
    if preset.image_encoding == "jpeg":
        pipeline = f"{pipeline} ! jpegdec"
    return _build_appsink_pipeline(
        pipeline=f"{pipeline} ! videoconvert ! {_raw_caps(encoding)}",
    )


def _build_appsink_pipeline(
    config: ResolvedCameraConfig | None = None,
    preset_name: str | None = None,
    pipeline: str | None = None,
) -> str:
    """appsink付きpipelineの生成"""
    base_pipeline = pipeline
    if base_pipeline is None:
        if config is None:
            raise ValueError("config is required when pipeline is not set")
        base_pipeline = build_gstreamer_pipeline(config, preset_name=preset_name)
    return (
        f"{base_pipeline} ! "
        f"appsink name={_APP_SINK_NAME} emit-signals=false sync=false "
        "max-buffers=1 drop=true"
    )


def _pull_sample(pipeline_text: str, timeout_sec: float):
    """appsinkからのsample取得"""
    Gst = _load_gst()
    pipeline = Gst.parse_launch(pipeline_text)
    sink = pipeline.get_by_name(_APP_SINK_NAME)
    if sink is None:
        raise RuntimeError("appsink is not found")

    pipeline.set_state(Gst.State.PLAYING)
    try:
        sample = sink.emit("try-pull-sample", int(timeout_sec * Gst.SECOND))
        if sample is None:
            _raise_bus_error_if_any(Gst, pipeline)
            raise TimeoutError(f"failed to capture image within {timeout_sec} seconds")
        return sample
    finally:
        pipeline.set_state(Gst.State.NULL)


def _sample_bytes(sample: Any) -> tuple[bytes, int | None, int | None]:
    """sample bufferのbytes化"""
    buffer = sample.get_buffer()
    caps = sample.get_caps()
    width, height = _sample_size(caps)
    ok, map_info = buffer.map(_load_gst().MapFlags.READ)
    if not ok:
        raise RuntimeError("failed to map gstreamer buffer")
    try:
        return bytes(map_info.data), width, height
    finally:
        buffer.unmap(map_info)


def _sample_size(caps: Any) -> tuple[int | None, int | None]:
    """sample capsからの画像サイズ取得"""
    if caps is None or caps.get_size() == 0:
        return None, None
    structure = caps.get_structure(0)
    width = structure.get_value("width") if structure.has_field("width") else None
    height = structure.get_value("height") if structure.has_field("height") else None
    return width, height


def _bytes_to_array(
    data: bytes,
    width: int | None,
    height: int | None,
    encoding: str,
) -> np.ndarray:
    """画像bytesのNumPy化"""
    if width is None or height is None:
        raise RuntimeError("decoded image size is not set")
    channels = _channels(encoding)
    expected_size = width * height * channels
    if len(data) < expected_size:
        raise RuntimeError("decoded image buffer is smaller than expected")

    array = np.frombuffer(data[:expected_size], dtype=np.uint8).copy()
    if channels == 1:
        return array.reshape((height, width))
    return array.reshape((height, width, channels))


def _channels(encoding: str) -> int:
    """encodingごとのchannel数"""
    if encoding in {"rgb8", "bgr8"}:
        return 3
    if encoding == "mono8":
        return 1
    raise ValueError(f"unsupported decoded image encoding: {encoding}")


def _raw_caps(encoding: str) -> str:
    """encodingに対応するraw caps"""
    if encoding == "rgb8":
        return "video/x-raw,format=RGB"
    if encoding == "bgr8":
        return "video/x-raw,format=BGR"
    if encoding == "mono8":
        return "video/x-raw,format=GRAY8"
    raise ValueError(f"unsupported decoded image encoding: {encoding}")


def _get_capture_preset(
    config: ResolvedCameraConfig,
    preset_name: str | None,
) -> CapturePreset:
    """キャプチャープリセットの取得"""
    name = config.gstreamer.default_preset if preset_name is None else preset_name
    try:
        return config.gstreamer.presets[name]
    except KeyError as exc:
        raise KeyError(f"capture preset is not defined: {name}") from exc


def _raise_bus_error_if_any(Gst: Any, pipeline: Any) -> None:
    """GStreamer bus errorの送出"""
    bus = pipeline.get_bus()
    message = bus.pop_filtered(Gst.MessageType.ERROR | Gst.MessageType.EOS)
    if message is None or message.type != Gst.MessageType.ERROR:
        return
    error, debug = message.parse_error()
    raise RuntimeError(f"gstreamer error: {error.message}; {debug}")


def _load_gst():
    """GStreamer Python bindingの読み込み"""
    import gi

    gi.require_version("Gst", "1.0")
    from gi.repository import Gst

    Gst.init(None)
    return Gst


__all__ = [
    "capture_encoded_image",
    "capture_decoded_image",
]
