"""midisc — Octatrack 1.40C MIDI scenes OS patch."""
from __future__ import annotations

import pathlib
import subprocess
import sys

from ot3_asm import Asm  # noqa: F401

from .memory_map import *  # noqa: F403

def off(a: int) -> int:
    return a - BASE


def jmp_abs(t: int) -> bytes:
    return b"\x4e\xf9" + t.to_bytes(4, "big")


def jsr_abs(t: int) -> bytes:
    return b"\x4e\xb9" + t.to_bytes(4, "big")


def ensure_stock() -> bytes:
    cave_end = 0x400D7C30  # must be zeros; FF pad D7C3C..D7C4F is OK
    if STOCK.exists() and STOCK.stat().st_size == 1_112_560:
        data = STOCK.read_bytes()
        if not any(data[off(MSC) : off(cave_end)]):
            return data
    if not SYX.exists():
        sys.exit(f"missing {SYX}")
    STOCK.parent.mkdir(parents=True, exist_ok=True)
    r = subprocess.run(
        [sys.executable, str(ROOT / "tools" / "extract_main_os.py"), "-i", str(SYX), "-o", str(STOCK)],
        cwd=str(ROOT),
    )
    if r.returncode:
        sys.exit("extract failed")
    data = STOCK.read_bytes()
    if len(data) != 1_112_560:
        sys.exit(f"bad stock size {len(data)}")
    if any(data[off(MSC) : off(cave_end)]):
        sys.exit("stock cave not empty after extract")
    return data


def fix_jsr(blob: bytearray, sent: int, real: int) -> int:
    needle = bytes([0x4E, 0xB9]) + sent.to_bytes(4, "big")
    repl = bytes([0x4E, 0xB9]) + real.to_bytes(4, "big")
    n = 0
    i = 0
    while True:
        j = blob.find(needle, i)
        if j < 0:
            break
        blob[j : j + 6] = repl
        n += 1
        i = j + 6
    return n


