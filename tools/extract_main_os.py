#!/usr/bin/env python3
"""Extract MAIN OS (section 3) from a stock Octatrack .syx — pure Python, Windows-safe."""
from __future__ import annotations

import argparse
import hashlib
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

from aplib_elektron import ap_depack  # noqa: E402
from syx_elektron import decode_syx_elek  # noqa: E402

STOCK_SYX_SHA256 = None  # optional check disabled for flexibility


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "-i",
        "--input",
        type=Path,
        default=ROOT / "downloads/extracted/OCTATRACK_OS1.40C.syx",
        help="stock .syx file",
    )
    ap.add_argument(
        "-o",
        "--output",
        type=Path,
        default=ROOT / "out/raw/section_3_MAIN_OS.bin",
    )
    args = ap.parse_args()

    if not args.input.exists():
        sys.exit(f"missing {args.input}\n  run scripts/fetch-os.ps1 first")

    raw = args.input.read_bytes()
    print(f"input: {args.input} ({len(raw):,} B)")
    print(f"sha256: {hashlib.sha256(raw).hexdigest()}")

    container, dev = decode_syx_elek(raw)
    print(f"ELEK container: {len(container):,} B  device=0x{dev:02x}")

    sec = container[0x12:]
    ulen = struct.unpack(">I", sec[:4])[0]
    main_os = ap_depack(sec[: ulen + 8])
    print(f"MAIN OS: {len(main_os):,} B")

    if len(main_os) != 1_112_560:
        print(f"  [!] unexpected size (expected 1,112,560)")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(main_os)
    print(f"wrote {args.output}")


if __name__ == "__main__":
    main()
