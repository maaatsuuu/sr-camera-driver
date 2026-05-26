from __future__ import annotations

from typing import Any

import numpy as np
from sensor_msgs.msg import CompressedImage
from sensor_msgs.msg import Image
from std_msgs.msg import Header

from sr_common.camera.image_types import DecodedImageData
from sr_common.camera.image_types import EncodedImageData


def bytes_per_pixel(encoding: str) -> int:
    """encodingごとの1 pixelあたりbyte数を取得"""
    if encoding in {"rgb8", "bgr8"}:
        return 3
    if encoding == "mono8":
        return 1
    raise ValueError(f"unsupported image encoding: {encoding}")


def encode_image_msg(
    image: DecodedImageData,
    frame_id: str | None = None,
    stamp: Any | None = None,
) -> Image:
    """DecodedImageData から sensor_msgs/Image を作成"""
    msg = Image()
    msg.header = _make_header(
        frame_id=image.frame_id if frame_id is None else frame_id,
        stamp=image.stamp if stamp is None else stamp,
    )
    msg.height = image.height
    msg.width = image.width
    msg.encoding = image.encoding
    msg.is_bigendian = False
    msg.step = image.width * bytes_per_pixel(image.encoding)
    msg.data = np.ascontiguousarray(image.data).tobytes()
    return msg


def decode_image_msg(msg: Image) -> DecodedImageData:
    """sensor_msgs/Image から DecodedImageData を作成"""
    channels = bytes_per_pixel(msg.encoding)
    dtype = np.uint8
    array = np.frombuffer(msg.data, dtype=dtype).copy()
    if channels == 1:
        array = array.reshape((msg.height, msg.width))
    else:
        array = array.reshape((msg.height, msg.width, channels))

    return DecodedImageData(
        data=array,
        encoding=msg.encoding,
        width=msg.width,
        height=msg.height,
        frame_id=msg.header.frame_id,
        stamp=msg.header.stamp,
    )


def encode_compressed_image_msg(
    image: EncodedImageData,
    frame_id: str | None = None,
    stamp: Any | None = None,
) -> CompressedImage:
    """EncodedImageData から sensor_msgs/CompressedImage を作成"""
    msg = CompressedImage()
    msg.header = _make_header(
        frame_id=image.frame_id if frame_id is None else frame_id,
        stamp=image.stamp if stamp is None else stamp,
    )
    msg.format = image.format
    msg.data = image.data
    return msg


def decode_compressed_image_msg(msg: CompressedImage) -> EncodedImageData:
    """sensor_msgs/CompressedImage から EncodedImageData を作成"""
    return EncodedImageData(
        data=bytes(msg.data),
        format=msg.format,
        frame_id=msg.header.frame_id,
        stamp=msg.header.stamp,
    )


def _make_header(frame_id: str = "", stamp: Any | None = None) -> Header:
    """Headerの生成"""
    header = Header()
    header.frame_id = frame_id
    if stamp is not None:
        header.stamp = stamp
    return header


__all__ = [
    "bytes_per_pixel",
    "encode_image_msg",
    "decode_image_msg",
    "encode_compressed_image_msg",
    "decode_compressed_image_msg",
]
