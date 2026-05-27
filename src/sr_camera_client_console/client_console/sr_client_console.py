#!/usr/bin/env python3

from __future__ import annotations

import os
from pathlib import Path
import sys

from client_console import (
    build_console_namespace,
    run_interactive_console,
    setup_readline_completion,
)


_SOURCE_DIR = Path(os.environ.get('SOURCE_DIR', Path.home() / 'ros2_ws' / 'src'))
if str(_SOURCE_DIR) not in sys.path:
    sys.path.insert(0, str(_SOURCE_DIR))


def main() -> None:
    import rclpy
    from sr_util.sr_camera_util import SrCameraUtil

    camera_type = os.environ.get('CAMERA_TYPE', 'elp')

    rclpy.init()
    node = rclpy.create_node(f'sr_camera_console_{camera_type}')
    client = SrCameraUtil.from_camera_type(camera_type, node=node)
    namespace = build_console_namespace(
        client,
        aliases={
            'camera': client,
            'node': node,
        },
    )
    setup_readline_completion(namespace)

    try:
        run_interactive_console(
            banner_title='SrCameraUtil',
            namespace=namespace,
            extra_banner_lines=[
                'Try: show_command_list(), capture_and_save_encoded_image()',
                'Topic save: save_latest_compressed_topic(), save_latest_raw_topic()',
            ],
        )

    finally:
        node.destroy_node()
        rclpy.shutdown()
        print('SrCameraUtil console stopped.')


if __name__ == '__main__':
    main()
