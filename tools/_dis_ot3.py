#!/usr/bin/env python3
"""ColdFire-aware disassembler pass for the OT3 scene work.

The stock image uses ISA_B encodings capstone's m68k mode mis-decodes:
  mvs/mvz  (0x7100 mask)  -> capstone shows ".byte" or bogus moveq
  mulu.l / divu.l         -> capstone shows "dc.w 0x4c.."
Those two families carry the track/param math in the scene path, so decoding
them wrong is how earlier builds shipped the wrong index.

Usage:
  python tools/_dis_ot3.py <start> <end> [image]
"""
from __future__ import annotations

import sys
from pathlib import Path

BASE = 0x40000400
ROOT = Path(__file__).resolve().parent.parent
DEFAULT_BIN = ROOT / "out" / "mainos_stock.bin"

REGS_D = [f"d{i}" for i in range(8)]
REGS_A = [f"a{i}" for i in range(8)]


class Dis:
    def __init__(self, img: bytes, base: int = BASE) -> None:
        self.s = img
        self.base = base
        from capstone import CS_ARCH_M68K, CS_MODE_M68K_000, Cs

        self.md = Cs(CS_ARCH_M68K, CS_MODE_M68K_000)
        self.md.skipdata = True

    def u16(self, o: int) -> int:
        return int.from_bytes(self.s[o : o + 2], "big")

    def u32(self, o: int) -> int:
        return int.from_bytes(self.s[o : o + 4], "big")

    def ea(self, mode: int, reg: int, o: int, size: str) -> tuple[str, int]:
        if mode == 0:
            return REGS_D[reg], 0
        if mode == 1:
            return REGS_A[reg], 0
        if mode == 2:
            return f"({REGS_A[reg]})", 0
        if mode == 3:
            return f"({REGS_A[reg]})+", 0
        if mode == 4:
            return f"-({REGS_A[reg]})", 0
        if mode == 5:
            d = self.u16(o)
            if d >= 0x8000:
                d -= 0x10000
            return f"{d:#x}({REGS_A[reg]})", 2
        if mode == 6:
            ext = self.u16(o)
            xn = (REGS_A if (ext >> 15) & 1 else REGS_D)[(ext >> 12) & 7]
            sz = "l" if (ext >> 11) & 1 else "w"
            sc = 1 << ((ext >> 9) & 3)
            disp = ext & 0xFF
            if disp >= 128:
                disp -= 256
            scs = f"*{sc}" if sc != 1 else ""
            dp = f"{disp:#x}," if disp else ""
            return f"({dp}{REGS_A[reg]},{xn}.{sz}{scs})", 2
        if mode == 7:
            if reg == 0:
                return f"({self.u16(o):#x}).w", 2
            if reg == 1:
                return f"({self.u32(o):#x}).l", 4
            if reg == 2:
                d = self.u16(o)
                if d >= 0x8000:
                    d -= 0x10000
                return f"{d:#x}(pc)", 2
            if reg == 4:
                if size == "b":
                    return f"#{self.u16(o) & 0xFF:#x}", 2
                if size == "w":
                    return f"#{self.u16(o):#x}", 2
                return f"#{self.u32(o):#x}", 4
        return f"?m{mode}r{reg}", 0

    def one(self, addr: int) -> tuple[str, int]:
        o = addr - self.base
        op = self.u16(o)

        # ColdFire TST.L An  (classic 68k forbids An; CF allows it)
        # 0100 1010 10 001 rrr = 0x4A88 | An
        if (op & 0xFFF8) == 0x4A88:
            return f"tst.l {REGS_A[op & 7]}", 2

        # MVS/MVZ  0111 ddd 1 z s mmm rrr
        if (op & 0xF100) == 0x7100:
            dx = (op >> 9) & 7
            mnem = "mvz" if (op >> 7) & 1 else "mvs"
            sz = "w" if (op >> 6) & 1 else "b"
            txt, n = self.ea((op >> 3) & 7, op & 7, o + 2, sz)
            return f"{mnem}.{sz} {txt}, {REGS_D[dx]}", 2 + n

        # MULU.L/MULS.L 0100 1100 00 mmm rrr + ext
        if (op & 0xFFC0) == 0x4C00:
            ext = self.u16(o + 2)
            dl = (ext >> 12) & 7
            mnem = "muls.l" if (ext >> 11) & 1 else "mulu.l"
            txt, n = self.ea((op >> 3) & 7, op & 7, o + 4, "l")
            return f"{mnem} {txt}, {REGS_D[dl]}", 4 + n

        # DIVU.L/DIVS.L 0100 1100 01 mmm rrr + ext
        if (op & 0xFFC0) == 0x4C40:
            ext = self.u16(o + 2)
            dq = (ext >> 12) & 7
            dr = ext & 7
            mnem = "divs.l" if (ext >> 11) & 1 else "divu.l"
            rem = "" if dq == dr else f"  ; rem->{REGS_D[dr]}"
            txt, n = self.ea((op >> 3) & 7, op & 7, o + 4, "l")
            return f"{mnem} {txt}, {REGS_D[dq]}{rem}", 4 + n

        for i in self.md.disasm(self.s[o : o + 16], addr):
            return f"{i.mnemonic} {i.op_str}", len(i.bytes)
        return f".word {op:#06x}", 2

    def range(self, start: int, end: int) -> None:
        a = start
        while a < end:
            txt, n = self.one(a)
            raw = self.s[a - self.base : a - self.base + n].hex()
            print(f"{a:08x}  {raw:<24s}  {txt}")
            a += n


def main() -> None:
    start = int(sys.argv[1], 16)
    end = int(sys.argv[2], 16)
    img = Path(sys.argv[3] if len(sys.argv) > 3 else DEFAULT_BIN).read_bytes()
    Dis(img).range(start, end)


if __name__ == "__main__":
    main()
