#!/usr/bin/env python3
"""Build midisc MIDISC2.2 (exact MIDISC4.0 / midisc21 engine)."""
from __future__ import annotations
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from midisc.build import main

if __name__ == "__main__":
    main()
