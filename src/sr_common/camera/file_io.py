from __future__ import annotations

from datetime import datetime
import os
from pathlib import Path

import cv2

from sr_common.camera.image_types import DecodedImageData
from sr_common.camera.image_types import EncodedImageData


DEFAULT_IMAGE_OUTPUT_DIR = (
    Path(os.environ.get("WORKSPACE_DIR", Path.home() / "ros2_ws")) / "src"/ "data" / "images"
)


def build_timestamped_image_path(
    output_dir: str | Path,
    camera_name: str,
    condition_name: str,
    extension: str,
    timestamp: datetime | None = None,
) -> Path:
    """タイムスタンプ付き画像保存パスの生成"""
    stamp = timestamp or datetime.now()
    ext = extension.lstrip(".")
    filename = (
        f"{stamp:%Y%m%d_%H%M%S}_{stamp.microsecond // 1000:03d}_"
        f"{camera_name}_{condition_name}.{ext}"
    )
    return Path(output_dir) / camera_name / filename


def guess_image_format(path: str | Path) -> str:
    """拡張子からの画像形式推定"""
    suffix = Path(path).suffix.lower()
    if suffix in {".jpg", ".jpeg"}:
        return "jpeg"
    if suffix == ".png":
        return "png"
    raise ValueError(f"unsupported image extension: {suffix}")


def save_encoded_image(image: EncodedImageData, path: str | Path) -> None:
    """圧縮済み画像データの保存"""
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(image.data)


def load_encoded_image(
    path: str | Path,
    format: str | None = None,
) -> EncodedImageData:
    """圧縮済み画像データの読み込み"""
    input_path = Path(path)
    image_format = guess_image_format(input_path) if format is None else format
    return EncodedImageData(
        data=input_path.read_bytes(),
        format=image_format,
    )


def save_decoded_image(image: DecodedImageData, path: str | Path) -> None:
    """デコード済み画像データの保存"""
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    data = _to_cv_image(image)
    if not cv2.imwrite(str(output_path), data):
        raise RuntimeError(f"failed to save image: {output_path}")


def load_decoded_image(
    path: str | Path,
    encoding: str = "bgr8",
) -> DecodedImageData:
    """デコード済み画像データの読み込み"""
    input_path = Path(path)
    data = cv2.imread(str(input_path), cv2.IMREAD_UNCHANGED)
    if data is None:
        raise RuntimeError(f"failed to load image: {input_path}")

    if encoding == "rgb8":
        data = cv2.cvtColor(data, cv2.COLOR_BGR2RGB)
    elif encoding not in {"bgr8", "mono8"}:
        raise ValueError(f"unsupported image encoding: {encoding}")

    return DecodedImageData(
        data=data,
        encoding=encoding,
        width=int(data.shape[1]),
        height=int(data.shape[0]),
    )


def _to_cv_image(image: DecodedImageData):
    """OpenCV保存用画像への変換"""
    if image.encoding == "bgr8":
        return image.data
    if image.encoding == "rgb8":
        return cv2.cvtColor(image.data, cv2.COLOR_RGB2BGR)
    if image.encoding == "mono8":
        return image.data
    raise ValueError(f"unsupported image encoding: {image.encoding}")


__all__ = [
    "DEFAULT_IMAGE_OUTPUT_DIR",
    "build_timestamped_image_path",
    "guess_image_format",
    "save_encoded_image",
    "load_encoded_image",
    "save_decoded_image",
    "load_decoded_image",
]
