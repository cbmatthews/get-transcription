"""Lazy provider lookup: name -> "module:Class", imported only when selected."""

from __future__ import annotations

import importlib
from typing import Any

from prism.config import Settings
from prism.errors import ConfigError


def load_provider(kind: str, name: str, table: dict[str, str], settings: Settings) -> Any:
    target = table.get(name)
    if target is None:
        known = ", ".join(sorted(table))
        raise ConfigError(f"Unknown {kind} provider '{name}'. Known providers: {known}.")
    module_name, class_name = target.split(":", 1)
    cls = getattr(importlib.import_module(module_name), class_name)
    return cls(settings)
