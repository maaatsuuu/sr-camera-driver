from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Mapping

from sr_common.camera.config_loader import load_camera_config
from sr_common.camera.file_io import DEFAULT_IMAGE_OUTPUT_DIR
from sr_common.camera.file_io import build_timestamped_image_path
from sr_common.camera.file_io import save_decoded_image
from sr_common.camera.file_io import save_encoded_image
from sr_common.camera.gstreamer_capture import capture_decoded_image
from sr_common.camera.gstreamer_capture import capture_encoded_image
from sr_common.camera.image_types import DecodedImageData
from sr_common.camera.image_types import EncodedImageData
from sr_common.camera.image_types import ResolvedCameraConfig
from sr_common.camera.message_converter import decode_compressed_image_msg
from sr_common.camera.message_converter import decode_image_msg
from sr_common.camera.ros_interface import publish_image
from sr_common.camera.ros_interface import resolve_image_topic


class SrCameraUtil:
    """カメラ検証用ユーティリティ"""

    def __init__(
        self,
        config_path: str | Path,
        node: Any | None = None,
        env: Mapping[str, str] | None = None,
    ) -> None:
        self._config = load_camera_config(config_path, env=env)
        self._node = node
        self._image_publisher = None

    @classmethod
    def from_camera_type(
        cls,
        camera_type: str,
        node: Any | None = None,
        env: Mapping[str, str] | None = None,
    ) -> "SrCameraUtil":
        """カメラ種別から生成"""
        return cls(
            _camera_config_path(camera_type),
            node=node,
            env=env,
        )

    @property
    def config(self) -> ResolvedCameraConfig:
        """解決済みカメラ設定"""
        return self._config

    def capture_and_save_encoded_image(
        self,
        preset_name: str | None = None,
        output_dir: str | Path = DEFAULT_IMAGE_OUTPUT_DIR,
        extension: str = "jpg",
        timeout_sec: float = 5.0,
    ) -> Path:
        """圧縮画像の取得と保存"""
        image = capture_encoded_image(
            self._config,
            preset_name=preset_name,
            timeout_sec=timeout_sec,
        )
        path = self._build_image_path(
            condition_name=preset_name,
            output_dir=output_dir,
            extension=extension,
        )
        save_encoded_image(image, path)
        return path

    def capture_and_save_decoded_image(
        self,
        preset_name: str | None = None,
        encoding: str = "rgb8",
        output_dir: str | Path = DEFAULT_IMAGE_OUTPUT_DIR,
        extension: str = "jpg",
        timeout_sec: float = 5.0,
    ) -> Path:
        """デコード済み画像の取得と保存"""
        image = capture_decoded_image(
            self._config,
            preset_name=preset_name,
            encoding=encoding,
            timeout_sec=timeout_sec,
        )
        path = self._build_image_path(
            condition_name=preset_name,
            output_dir=output_dir,
            extension=extension,
        )
        save_decoded_image(image, path)
        return path

    def save_latest_compressed_topic(
        self,
        output_dir: str | Path = DEFAULT_IMAGE_OUTPUT_DIR,
        extension: str = "jpg",
        timeout_sec: float = 5.0,
    ) -> Path:
        """CompressedImage topicの1枚保存"""
        image = self._receive_latest_compressed_image(timeout_sec=timeout_sec)
        path = self._build_image_path(
            condition_name="topic_compressed",
            output_dir=output_dir,
            extension=extension,
        )
        save_encoded_image(image, path)
        return path

    def save_latest_raw_topic(
        self,
        output_dir: str | Path = DEFAULT_IMAGE_OUTPUT_DIR,
        extension: str = "jpg",
        timeout_sec: float = 5.0,
    ) -> Path:
        """Image topicの1枚保存"""
        image = self._receive_latest_raw_image(timeout_sec=timeout_sec)
        path = self._build_image_path(
            condition_name="topic_raw",
            output_dir=output_dir,
            extension=extension,
        )
        save_decoded_image(image, path)
        return path

    def publish_encoded_image(
        self,
        image: EncodedImageData,
        publisher: Any | None = None,
        frame_id: str | None = None,
        stamp: Any | None = None,
    ) -> None:
        """圧縮画像のpublish"""
        publish_image(
            self._resolve_publisher(publisher),
            image,
            frame_id=frame_id,
            stamp=stamp,
        )

    def publish_decoded_image(
        self,
        image: DecodedImageData,
        publisher: Any | None = None,
        frame_id: str | None = None,
        stamp: Any | None = None,
    ) -> None:
        """デコード済み画像のpublish"""
        publish_image(
            self._resolve_publisher(publisher),
            image,
            frame_id=frame_id,
            stamp=stamp,
        )

    def set_image_publisher(self, publisher: Any) -> None:
        """画像Publisherの登録"""
        self._image_publisher = publisher

    def _build_image_path(
        self,
        condition_name: str | None,
        output_dir: str | Path,
        extension: str,
    ) -> Path:
        """保存パスの生成"""
        return build_timestamped_image_path(
            output_dir=output_dir,
            camera_name=self._config.gscam2.camera_name or self._config.name,
            condition_name=condition_name or self._config.gstreamer.default_preset,
            extension=extension,
        )

    def _receive_latest_compressed_image(
        self,
        timeout_sec: float,
    ) -> EncodedImageData:
        """CompressedImage topicの受信"""
        from sensor_msgs.msg import CompressedImage

        topic = resolve_image_topic(self._config.ros, compressed=True)
        msg = self._receive_one_message(CompressedImage, topic, timeout_sec)
        return decode_compressed_image_msg(msg)

    def _receive_latest_raw_image(
        self,
        timeout_sec: float,
    ) -> DecodedImageData:
        """Image topicの受信"""
        from sensor_msgs.msg import Image

        topic = resolve_image_topic(self._config.ros, compressed=False)
        msg = self._receive_one_message(Image, topic, timeout_sec)
        return decode_image_msg(msg)

    def _receive_one_message(
        self,
        msg_type: Any,
        topic: str,
        timeout_sec: float,
    ) -> Any:
        """topicから1メッセージ受信"""
        import rclpy
        from rclpy.task import Future

        node = self._require_node()
        future = Future()

        def callback(msg: Any) -> None:
            if not future.done():
                future.set_result(msg)

        subscription = node.create_subscription(msg_type, topic, callback, 10)
        try:
            rclpy.spin_until_future_complete(node, future, timeout_sec=timeout_sec)
            if not future.done():
                raise TimeoutError(f"failed to receive message: {topic}")
            return future.result()
        finally:
            node.destroy_subscription(subscription)

    def _resolve_publisher(self, publisher: Any | None) -> Any:
        """Publisherの解決"""
        if publisher is not None:
            return publisher
        if self._image_publisher is None:
            raise RuntimeError("image publisher is not set")
        return self._image_publisher

    def _require_node(self) -> Any:
        """Nodeの取得"""
        if self._node is None:
            raise RuntimeError("node is required")
        return self._node


def _camera_config_path(camera_type: str) -> Path:
    """camera.yamlパスの生成"""
    source_dir = Path(os.environ.get("SOURCE_DIR", Path.home() / "ros2_ws" / "src"))
    return source_dir / "bringup" / "config" / camera_type / "camera.yaml"


__all__ = ["SrCameraUtil"]
