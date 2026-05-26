from __future__ import annotations

import re
from typing import Any, Mapping

from sr_common.camera.image_types import CapturePreset
from sr_common.camera.image_types import GstreamerConfig
from sr_common.camera.image_types import ResolvedCameraConfig


_TEMPLATE_PATTERN = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}")


def build_gstreamer_pipeline(
    config: ResolvedCameraConfig,
    preset_name: str | None = None,
) -> str:
    """GStreamer pipeline文字列の生成"""
    gstreamer = config.gstreamer
    preset = _get_capture_preset(gstreamer, preset_name)
    return _build_pipeline_from_preset(gstreamer, preset)


def build_gstreamer_preview_pipeline(
    config: ResolvedCameraConfig,
    preset_name: str | None = None,
) -> str:
    """プレビュー用GStreamer pipeline文字列の生成"""
    pipeline = build_gstreamer_pipeline(config, preset_name=preset_name)
    return _normalize_pipeline(f"{pipeline} ! {config.gstreamer.preview_sink}")


def _get_capture_preset(
    config: GstreamerConfig,
    preset_name: str | None,
) -> CapturePreset:
    """キャプチャープリセットの取得"""
    name = config.default_preset if preset_name is None else preset_name
    try:
        return config.presets[name]
    except KeyError as exc:
        raise KeyError(f"capture preset is not defined: {name}") from exc


def _build_template_values(
    config: GstreamerConfig,
    preset: CapturePreset,
) -> dict[str, Any]:
    """pipeline templateへ埋め込む値の生成"""
    values = dict(config.params)
    preset_values = {
        "width": preset.width,
        "height": preset.height,
        "fps_num": preset.fps_num,
        "fps_den": preset.fps_den,
        **preset.extra,
    }
    values.update({
        key: value
        for key, value in preset_values.items()
        if value is not None
    })
    return values


def _build_pipeline_from_preset(
    config: GstreamerConfig,
    preset: CapturePreset,
) -> str:
    """プリセット指定pipelineの生成"""
    values = _build_template_values(config, preset)
    pipeline = _render_pipeline_template(config.pipeline_template, values)
    return _normalize_pipeline(pipeline)


def _render_pipeline_template(
    template: str,
    values: Mapping[str, Any],
) -> str:
    """pipeline templateの展開"""
    return _TEMPLATE_PATTERN.sub(lambda m: _template_value(m.group(1), values), template)


def _template_value(name: str, values: Mapping[str, Any]) -> str:
    """template値の取得"""
    if name not in values:
        raise KeyError(f"pipeline template value is not set: {name}")
    return _format_gstreamer_value(values[name])


def _format_gstreamer_value(value: Any) -> str:
    """GStreamer向け値表現への変換"""
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def _normalize_pipeline(pipeline: str) -> str:
    """pipeline文字列の整形"""
    return " ".join(pipeline.split())


__all__ = [
    "build_gstreamer_pipeline",
    "build_gstreamer_preview_pipeline",
]
