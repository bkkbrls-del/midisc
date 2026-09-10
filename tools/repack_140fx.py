#!/usr/bin/env python3
"""
Repack 1.40FX -> Desktop 1.40FX.bin (and out/OCTATRACK_1.40FX.syx).

    python tools/build_140fx.py
    python tools/repack_140fx.py

FX2: TAPE DELAY (Plate) + CLOUDS (Spring). Dark Reverb stock. No other patches.
"""
from __future__ import annotations

import argparse
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

from aplib_elektron import ap_pack  # noqa: E402
from syx_elektron import (  # noqa: E402
    decode_syx_elek,
    encode_syx_elek,
    replace_elek_section,
    set_elek_version,
)

ELUP_SEED = 0x2F1349D2
XOR_A, XOR_B = 0x9E3B16A2, 0x764E28CA
C3, C7 = 0x360FA955, 0xEF4A9AB6
M = 0xFFFFFFFF


def rot16(v: int) -> int:
    return ((v << 16) | (v >> 16)) & M


def bswap(v: int) -> int:
    return (
        ((v & 0xFF) << 24)
        | ((v & 0xFF00) << 8)
        | ((v & 0xFF0000) >> 8)
        | (v >> 24)
    ) & M


def encode_word(k: int, p: int) -> int:
    x = (k ^ (C3 if (k & 0x800000) == 0 else C7) ^ p) & M
    if (k & 0x800000) == 0:
        return (rot16(x) ^ XOR_A) & M
    return (bswap(x) ^ XOR_B) & M


def make_elup_bin(elek_container: bytes, out: Path) -> None:
    payload = struct.pack(">I", len(elek_container)) + elek_container
    pad = (-len(payload)) % 4
    if pad:
        payload += b"\x00" * pad
    words = list(struct.unpack(f">{len(payload) // 4}I", payload))
    k, acc, cipher = ELUP_SEED, 0, []
    for p in words:
        c = encode_word(k, p)
        cipher.append(c)
        acc = (acc + p) & M
        k = c
    cipher.append(encode_word(k, acc))
    blob = struct.pack(">II", 0x454C5550, ELUP_SEED) + struct.pack(
        f">{len(cipher)}I", *cipher
    )
    out.write_bytes(blob)


def main() -> None:
    desktop = Path.home() / "Desktop" / "1.40FX.bin"
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "-i",
        "--input",
        type=Path,
        default=ROOT / "downloads/extracted/OCTATRACK_OS1.40C.syx",
    )
    ap.add_argument("-m", "--mainos", type=Path, default=ROOT / "out/mainos_140fx.bin")
    ap.add_argument("-o", "--output", type=Path, default=ROOT / "out/OCTATRACK_1.40FX.syx")
    ap.add_argument("--bin", type=Path, default=desktop)
    ap.add_argument("-V", "--version", default="1.40FX")
    args = ap.parse_args()

    if not args.input.exists():
        sys.exit(f"missing stock syx: {args.input}")
    if not args.mainos.exists():
        sys.exit(f"missing {args.mainos}\n  run: python tools/build_140fx.py")

    ver = args.version[:10]
    patched = args.mainos.read_bytes()
    print(f"[1/5] patched MAIN OS {len(patched):,} B")

    container, dev = decode_syx_elek(args.input.read_bytes())
    print(f"[2/5] decoded ELEK {len(container):,} B")

    packed = ap_pack(patched)
    print(f"[3/5] compressed {len(packed):,} B")

    nc = bytearray(container)
    set_elek_version(nc, ver)
    nc = replace_elek_section(nc, packed)

    syx = encode_syx_elek(bytes(nc), dev)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(syx)
    print(f"[4/5] wrote {args.output} ({len(syx):,} B)")

    args.bin.parent.mkdir(parents=True, exist_ok=True)
    make_elup_bin(bytes(nc), args.bin)
    print(f"[5/5] wrote {args.bin} ({args.bin.stat().st_size:,} B)")
    # Generic: this repacker serves every build in the tree, so it must not
    # describe one. The caller names what it built.
    print(f"\nFlash: copy {args.bin.name} to CF root -> OS UPGRADE  (version={ver})")
    print(f"Recovery: {args.input.name}")


if __name__ == "__main__":
    main()
