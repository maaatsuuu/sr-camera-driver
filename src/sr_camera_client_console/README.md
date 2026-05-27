# client_console

A small reusable helper package for building interactive client consoles.

This package is ROS-independent. It provides helpers to:

- expose public methods of an object into an interactive console namespace
- add aliases such as `util`, `ext_tracking`, or `elevator`
- print available command names with `show_command_list()`
- retrieve command names with `get_command_list()`
- enable tab completion with `readline` and `rlcompleter`
- launch an interactive console with a standard banner

## API

### `build_console_namespace(target, aliases=None, extra_namespace=None)`

Build a console namespace from a target object.

- `target`: object whose public callable methods will be exposed
- `aliases`: extra object aliases to add to the namespace
- `extra_namespace`: additional values or helper functions to inject

The returned namespace always contains:

- `util`
- public callable methods from `target`
- `get_command_list()`
- `show_command_list()`

### `setup_readline_completion(namespace)`

Enable tab completion for the provided namespace.

### `run_interactive_console(banner_title, namespace, extra_banner_lines=None)`

Launch a Python interactive console with a standard banner.

## Basic usage

```python
from client_console import (
    build_console_namespace,
    run_interactive_console,
    setup_readline_completion,
)


class DemoClient:
    def ping(self) -> str:
        return 'pong'

    def set_speed(self, speed: float) -> None:
        self._speed = float(speed)

    def get_speed(self) -> float:
        return self._speed


client = DemoClient()
namespace = build_console_namespace(
    client,
    aliases={'demo': client},
)
setup_readline_completion(namespace)
run_interactive_console(
    banner_title='DemoClient',
    namespace=namespace,
)
```

## Example

See [client_console/sample_client_console.py](client_console/sample_client_console.py).

Run it with:

```bash
python3 client_console/sample_client_console.py
```

Inside the console:

```python
show_command_list()
get_command_list()
ping()
set_speed(1.5)
get_speed()
```
