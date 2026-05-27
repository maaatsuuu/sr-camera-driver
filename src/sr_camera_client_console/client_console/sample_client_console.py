#!/usr/bin/env python3

from __future__ import annotations

from client_console import (
    build_console_namespace,
    run_interactive_console,
    setup_readline_completion,
)


class DemoClient:

    def __init__(self) -> None:
        self._speed = 0.0

    def ping(self) -> str:
        return 'pong'

    def set_speed(self, speed: float) -> None:
        self._speed = float(speed)

    def get_speed(self) -> float:
        return self._speed

    def stop(self) -> None:
        self._speed = 0.0


def main() -> None:
    client = DemoClient()
    namespace = build_console_namespace(
        client,
        aliases={'demo': client},
    )
    setup_readline_completion(namespace)

    try:
        run_interactive_console(
            banner_title='DemoClient',
            namespace=namespace,
            extra_banner_lines=[
                'Try: show_command_list(), ping(), set_speed(1.2), demo.get_speed()',
            ],
        )

    finally:
        client.stop()
        print('DemoClient stopped.')


if __name__ == '__main__':
    main()
