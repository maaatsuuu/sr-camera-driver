from __future__ import annotations

from typing import Any

from sensor_msgs.msg import CameraInfo
from sensor_msgs.msg import CompressedImage
from sensor_msgs.msg import Image

from sr_common.camera.image_types import DecodedImageData
from sr_common.camera.image_types import EncodedImageData
from sr_common.camera.image_types import ResolvedCameraRosConfig
from sr_common.camera.message_converter import encode_compressed_image_msg
from sr_common.camera.message_converter import encode_image_msg


def resolve_topic(namespace: str, topic: str) -> str:
    """ROS topic名の解決"""
    if not topic:
        raise ValueError("topic must not be empty")
    if topic.startswith("/"):
        return _normalize_topic(topic)
    if not namespace:
        return _normalize_topic(topic)
    return _normalize_topic(f"{namespace}/{topic}")


def resolve_image_topic(
    ros_config: ResolvedCameraRosConfig,
    compressed: bool = False,
) -> str:
    """画像topic名の解決"""
    topic = resolve_topic(ros_config.namespace, ros_config.image_topic)
    if compressed and not topic.endswith("/compressed"):
        return f"{topic}/compressed"
    return topic


def resolve_camera_info_topic(ros_config: ResolvedCameraRosConfig) -> str:
    """CameraInfo topic名の解決"""
    return resolve_topic(ros_config.namespace, ros_config.camera_info_topic)


def create_image_publisher(
    node: Any,
    ros_config: ResolvedCameraRosConfig,
    compressed: bool,
    qos_profile: Any = 10,
) -> Any:
    """画像Publisherの作成"""
    msg_type = CompressedImage if compressed else Image
    topic = resolve_image_topic(ros_config, compressed=compressed)
    return node.create_publisher(msg_type, topic, qos_profile)


def create_camera_info_publisher(
    node: Any,
    ros_config: ResolvedCameraRosConfig,
    qos_profile: Any = 10,
) -> Any:
    """CameraInfo Publisherの作成"""
    topic = resolve_camera_info_topic(ros_config)
    return node.create_publisher(CameraInfo, topic, qos_profile)


def publish_image(
    publisher: Any,
    image: EncodedImageData | DecodedImageData,
    frame_id: str | None = None,
    stamp: Any | None = None,
) -> None:
    """画像データのpublish"""
    if isinstance(image, EncodedImageData):
        publisher.publish(encode_compressed_image_msg(image, frame_id=frame_id, stamp=stamp))
        return
    if isinstance(image, DecodedImageData):
        publisher.publish(encode_image_msg(image, frame_id=frame_id, stamp=stamp))
        return
    raise TypeError("image must be EncodedImageData or DecodedImageData")


def _normalize_topic(topic: str) -> str:
    """topic名の正規化"""
    return "/" + topic.strip("/")


__all__ = [
    "resolve_topic",
    "resolve_image_topic",
    "resolve_camera_info_topic",
    "create_image_publisher",
    "create_camera_info_publisher",
    "publish_image",
]
