#!/usr/bin/env python3

from __future__ import annotations

import code
from typing import Any, Callable, Dict, Iterable, List, Mapping, Optional, Sequence, Set

import readline
import rlcompleter

_RESERVED_COMMAND_NAMES: Set[str] = {
    'get_command_list',
    'show_command_list',
}


def _iter_public_callables(target: Any) -> Iterable[tuple[str, Callable[..., Any]]]:
    for name in dir(target):
        if name.startswith('_'):
            continue
        attr = getattr(target, name)
        if callable(attr):
            yield name, attr


def get_command_list(
    namespace: Mapping[str, Any],
    *,
    exclude_names: Optional[Iterable[str]] = None,
) -> List[str]:
    excluded = set(exclude_names or ()) | _RESERVED_COMMAND_NAMES
    return sorted(
        name for name, value in namespace.items() if callable(value) and name not in excluded
    )


def show_command_list(
    namespace: Mapping[str, Any],
    *,
    exclude_names: Optional[Iterable[str]] = None,
) -> None:
    print('\n'.join(get_command_list(namespace, exclude_names=exclude_names)))


def build_console_namespace(
    target: Any,
    *,
    aliases: Optional[Mapping[str, Any]] = None,
    extra_namespace: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    namespace: Dict[str, Any] = {'util': target}

    if aliases:
        namespace.update(dict(aliases))

    for name, attr in _iter_public_callables(target):
        namespace[name] = attr

    if extra_namespace:
        namespace.update(dict(extra_namespace))

    def _local_get_command_list() -> List[str]:
        return get_command_list(namespace, exclude_names=set(namespace_aliases(namespace)))

    def _local_show_command_list() -> None:
        show_command_list(namespace, exclude_names=set(namespace_aliases(namespace)))

    namespace['get_command_list'] = _local_get_command_list
    namespace['show_command_list'] = _local_show_command_list

    return namespace


def namespace_aliases(namespace: Mapping[str, Any]) -> List[str]:
    return sorted(name for name, value in namespace.items() if not callable(value))


def setup_readline_completion(namespace: Mapping[str, Any]) -> None:
    completer = rlcompleter.Completer(dict(namespace))
    readline.set_completer(completer.complete)
    readline.parse_and_bind('tab: complete')


def run_interactive_console(
    *,
    banner_title: str,
    namespace: Mapping[str, Any],
    extra_banner_lines: Optional[Sequence[str]] = None,
) -> None:
    aliases = namespace_aliases(namespace)
    alias_text = ', '.join(aliases) if aliases else '(none)'

    banner_lines = [
        f'{banner_title} interactive console',
        f'Available objects: {alias_text}',
        'Use show_command_list() to print executable commands.',
        'Press Tab to complete command names.',
    ]
    if extra_banner_lines:
        banner_lines.extend(extra_banner_lines)
    banner_lines.append('Exit with Ctrl-D or exit() to close the console.')

    code.interact(banner='\n'.join(banner_lines), local=dict(namespace))


__all__ = [
    'build_console_namespace',
    'get_command_list',
    'namespace_aliases',
    'run_interactive_console',
    'setup_readline_completion',
    'show_command_list',
]
