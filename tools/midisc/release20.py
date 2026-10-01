"""MIDISC2.0: guarded, reproducible MAIN patch for official 1.40C."""
from pathlib import Path
import hashlib, json, subprocess, sys

ROOT = Path(__file__).resolve().parents[2]


def patch(stock):
    spec = json.loads(Path(__file__).with_suffix(".json").read_text())
    if len(stock) != spec["size"] or hashlib.sha256(stock).hexdigest() != spec["stock_sha256"]:
        raise ValueError("Expected unmodified official Octatrack OS 1.40C MAIN")
    image = bytearray(stock)
    for offset, encoded in spec["writes"]:
        value = bytes.fromhex(encoded)
        image[offset : offset + len(value)] = value
    if hashlib.sha256(image).hexdigest() != spec["main_sha256"]:
        raise ValueError("MIDISC2.0 patch integrity failure")
    return bytes(image)


def main():
    from .util import ensure_stock

    out = ROOT / "out/MIDISC2.0_MAIN.bin"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(patch(ensure_stock()))
    desktop = Path.home() / "Desktop" / "MIDISC2.0.bin"
    # Intermediate SYX stays under out/ (not Desktop). Card image is the Desktop .bin.
    syx = ROOT / "out/OCTATRACK_MIDISC2.0.syx"
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "tools/repack_140fx.py"),
            "-m",
            str(out),
            "--bin",
            str(desktop),
            "-o",
            str(syx),
            "-V",
            "MIDISC2.0",
        ],
        cwd=ROOT,
        check=True,
    )


if __name__ == "__main__":
    main()
