"""midisc OS patch. Build: ``python tools/build_midisc40.py``."""
from .memory_map import VER

__all__ = ["VER", "main"]


def __getattr__(name: str):
    if name == "main":
        from .build import main as _main

        return _main
    raise AttributeError(name)
