#!/usr/bin/env python3
"""Emit the midisc caves as GNU-as sources, and prove them byte-identical.

The caves are written against `ot3_asm.Asm`, a small Python encoder whose
routines are linked into fixed addresses by build.py. This script drives
the very same build_* functions with an Asm subclass that also records one
GNU-as line per instruction, so every routine comes out as `.s` text with
NO hand transcription -- and then assembles each region with m68k-elf-as,
links it at the address build.py uses, and compares the bytes against what
the encoder produced. Identity, region by region, or it fails.

What changes in the `.s` form, and why it is the point:

  * every cross-cave reference becomes a LINKER SYMBOL -- the SENT_* jsr
    sentinels that build.py patches with fix_jsr(), the addresses it computes
    and passes into builders (after / rel_after / unlock), the MSC table
    and the four state bytes past the STUB -- so a linker can place each
    region wherever there is room instead of at the address memory_map.py
    remembers. That is what lets midisc share an image with other mods.
  * stock addresses (0x4000xxxx code, 0x8000xxxx / 0x460dxxxx / 0x46c8xxxx
    RAM, the DRAM clipboard) stay literal: they are the firmware's, not ours.
  * absolute forms are forced (`(sym).l`, `jsr (sym).l`) so that a symbol
    which happens to land nearby is never shortened to a pc-relative or
    absolute-short encoding: the bytes must stay what the encoder made.

    python3 tools/gas_port.py            # writes gas/*.s, verifies each region
"""
from __future__ import annotations

import pathlib
import shutil
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import ot3_asm  # noqa: E402

OUT = ROOT / "gas"

# ---- cross-cave symbols ------------------------------------------------------
# build.py's own sentinels (fix_jsr targets), plus three sentinels of ours for
# the addresses build.py computes and hands to builders as plain ints.
AFTER_SENT, REL_AFTER_SENT, UNLOCK_SENT = 0x40BAD100, 0x40BAD104, 0x40BAD108


def _symbols(mm):
    return {
        mm.SENT_UNPACK: "unpack", mm.SENT_PACK: "pack", mm.SENT_DIRTY: "dirty",
        mm.SENT_REBUILD_MASK: "rebuild", mm.SENT_XF_MIX: "xf_mix",
        mm.SENT_CLAMP: "clamp", mm.SENT_VOICE_RELOAD: "voice_rel",
        mm.MSC: "msc",
        mm.LAST_PART: "last_part", mm.UNPACK_SRC: "unpack_src",
        mm.LAST_BANK: "last_bank", mm.APPLY_RET: "apply_ret",
        AFTER_SENT: "after", REL_AFTER_SENT: "rel_after", UNLOCK_SENT: "unlock",
    }


SYMBOLS: dict[int, str] = {}
CURRENT = "r"          # label prefix for the routine being built
INSTANCES: list = []   # every GasAsm created, in order


def _abs(v: int) -> str:
    return f"({SYMBOLS[v]}).l" if v in SYMBOLS else f"(0x{v:08x}).l"


def _imm(v: int) -> str:
    return f"#{SYMBOLS[v]}" if v in SYMBOLS else f"#0x{v & 0xFFFFFFFF:x}"


def _s8(v: int) -> int:
    v &= 0xFF
    return v - 0x100 if v >= 0x80 else v


class GasAsm(ot3_asm.Asm):
    """ot3_asm.Asm, plus one GNU-as line per instruction."""

    def __init__(self):
        super().__init__()
        self.lines: list[str] = []
        self.prefix = CURRENT
        INSTANCES.append(self)

    def _l(self, text):
        self.lines.append("        " + text)

    def _gl(self, name):          # (Asm already owns `_lab`, its label dict)
        return f".L{self.prefix}_{name}"

    # raw
    BRANCH_OPS = {0x60: "bra", 0x61: "bsr", 0x62: "bhi", 0x64: "bcc",
                  0x65: "bcs", 0x66: "bne", 0x67: "beq", 0x6A: "bpl",
                  0x6B: "bmi"}

    def hex(self, h):
        b = bytes.fromhex(h.replace(" ", ""))
        if getattr(self, "_quiet", False):
            return super().hex(h)
        # A HAND-ROLLED BRANCH. `Asm` has no `bsr` helper, so build_clear_part
        # pushes its own (offset, label) onto `_fix` and then emits the word
        # form's placeholder bytes itself. The displacement is therefore still
        # zero here and only `link()` fills it -- emit the real mnemonic and
        # let the linker compute it, or the `.s` keeps the zero (which is
        # exactly the one byte 1.40MIDISC5 first came out wrong by).
        if (self._fix and self._fix[-1][0] == len(self.b) and len(b) == 4
                and b[1:] == b"\x00\x00\x00" and b[0] in self.BRANCH_OPS):
            self._l(f"{self.BRANCH_OPS[b[0]]}.w {self._gl(self._fix[-1][1])}")
            return super().hex(h)
        self._l(".byte " + ", ".join(f"0x{x:02x}" for x in b))
        return super().hex(h)

    def label(self, name):
        self.lines.append(f"{self._gl(name)}:")
        return super().label(name)

    def _br(self, op, name):
        m = {"60": "bra", "67": "beq", "66": "bne", "64": "bcc", "65": "bcs",
             "62": "bhi", "6A": "bpl", "6B": "bmi"}[op]
        # super()._br goes through self.hex(), which would ALSO emit a
        # `.byte` line for the placeholder words: keep it quiet.
        return self._enc(f"{m}.w {self._gl(name)}", super()._br, op, name)

    def _enc(self, text, call, *args):
        self._l(text)
        self._quiet = True
        try:
            return call(*args)
        finally:
            self._quiet = False

    # control
    def jsr(self, t):      return self._enc(f"jsr {_abs(t)}", super().jsr, t)
    def jmp(self, t):      return self._enc(f"jmp {_abs(t)}", super().jmp, t)
    def rts(self):         return self._enc("rts", super().rts)

    def push(self, *regs):
        for r in regs:
            self._enc(f"move.l %{r},-(%sp)", super().push, r)
        return self

    def pop(self, *regs):
        for r in regs:
            self._enc(f"move.l (%sp)+,%{r}", super().pop, r)
        return self

    # data moves
    def move_l_sp(self, disp, dn):    return self._enc(f"move.l ({disp},%sp),%d{dn}", super().move_l_sp, disp, dn)
    def move_l_dd(self, s, d):        return self._enc(f"move.l %d{s},%d{d}", super().move_l_dd, s, d)
    def move_l_abs_d(self, a, dn):    return self._enc(f"move.l {_abs(a)},%d{dn}", super().move_l_abs_d, a, dn)
    def move_l_imm(self, imm, dn):
        v = imm & 0xFFFFFFFF
        if imm not in SYMBOLS and (v < 0x80 or v >= 0xFFFFFF80):
            # GAS shortens a small `move.l #imm,%dn` to moveq (2 bytes); the
            # encoder emits the 6-byte form. Keep the encoder's bytes.
            return self._enc(f".short 0x{0x203C + (dn << 9):04x}\n        .long 0x{imm & 0xFFFFFFFF:x}"
                             f"        | move.l #{imm},%d{dn} (long form kept)",
                             super().move_l_imm, imm, dn)
        return self._enc(f"move.l {_imm(imm)},%d{dn}", super().move_l_imm, imm, dn)
    def mvz_b_abs(self, a, dn):       return self._enc(f"mvz.b {_abs(a)},%d{dn}", super().mvz_b_abs, a, dn)
    def mvz_b_ind(self, an, dn):      return self._enc(f"mvz.b (%a{an}),%d{dn}", super().mvz_b_ind, an, dn)
    def mvz_b_disp(self, disp, an, dn): return self._enc(f"mvz.b ({disp},%a{an}),%d{dn}", super().mvz_b_disp, disp, an, dn)
    def move_b_d_ind(self, dn, an):   return self._enc(f"move.b %d{dn},(%a{an})", super().move_b_d_ind, dn, an)
    def movea_abs(self, a, an):       return self._enc(f"movea.l {_abs(a)},%a{an}", super().movea_abs, a, an)
    def movea_imm(self, imm, an):     return self._enc(f"movea.l {_imm(imm)},%a{an}", super().movea_imm, imm, an)
    def movea_d(self, dn, an):        return self._enc(f"movea.l %d{dn},%a{an}", super().movea_d, dn, an)
    def move_a_d(self, an, dn):       return self._enc(f"move.l %a{an},%d{dn}", super().move_a_d, an, dn)
    def adda_d(self, dn, an):         return self._enc(f"adda.l %d{dn},%a{an}", super().adda_d, dn, an)
    def adda_imm(self, imm, an):      return self._enc(f"adda.l {_imm(imm)},%a{an}", super().adda_imm, imm, an)
    def add_dd(self, s, d):           return self._enc(f"add.l %d{s},%d{d}", super().add_dd, s, d)
    def sub_dd(self, s, d):           return self._enc(f"sub.l %d{s},%d{d}", super().sub_dd, s, d)
    def addi(self, imm, dn):          return self._enc(f"addi.l {_imm(imm)},%d{dn}", super().addi, imm, dn)
    def andi(self, imm, dn):          return self._enc(f"andi.l {_imm(imm)},%d{dn}", super().andi, imm, dn)
    def cmpi(self, imm, dn):          return self._enc(f"cmpi.l {_imm(imm)},%d{dn}", super().cmpi, imm, dn)
    def addq(self, imm, dn):          return self._enc(f"addq.l #{imm},%d{dn}", super().addq, imm, dn)
    def tst_abs(self, a):             return self._enc(f"tst.l {_abs(a)}", super().tst_abs, a)
    def tst_d(self, dn):              return self._enc(f"tst.l %d{dn}", super().tst_d, dn)
    def lsl(self, c, dn):             return self._enc(f"lsl.l #{c},%d{dn}", super().lsl, c, dn)
    def asr(self, c, dn):             return self._enc(f"asr.l #{c},%d{dn}", super().asr, c, dn)
    def muls(self, s, d):             return self._enc(f"muls.l %d{s},%d{d}", super().muls, s, d)
    def lsl_reg(self, c, dn):         return self._enc(f"lsl.l %d{c},%d{dn}", super().lsl_reg, c, dn)
    def or_dd(self, s, d):            return self._enc(f"or.l %d{s},%d{d}", super().or_dd, s, d)
    def moveq(self, imm, dn):         return self._enc(f"moveq #{_s8(imm)},%d{dn}", super().moveq, imm, dn)
    def move_b_abs_d(self, a, dn):    return self._enc(f"move.b {_abs(a)},%d{dn}", super().move_b_abs_d, a, dn)
    def move_b_d_abs(self, dn, a):    return self._enc(f"move.b %d{dn},{_abs(a)}", super().move_b_d_abs, dn, a)
    def move_l_d_abs(self, dn, a):    return self._enc(f"move.l %d{dn},{_abs(a)}", super().move_l_d_abs, dn, a)
    def move_b_ind_d(self, an, dn):   return self._enc(f"move.b (%a{an}),%d{dn}", super().move_b_ind_d, an, dn)


ot3_asm.Asm = GasAsm          # every `from ot3_asm import Asm` below gets this

from midisc import memory_map as mm  # noqa: E402
from midisc.parts import (  # noqa: E402
    build_after_apply, build_apply_wrap, build_bank_invalidate, build_bank_switch,
    build_after_project_load, build_bank_publish, build_clear_part, build_dirty,
    build_pack, build_reload_after, build_reload_ui, build_save_ui, build_unpack)
from midisc.hold import (  # noqa: E402
    build_addi_d0, build_addi_d1, build_dial, build_enc_press_hook, build_enc_unlock,
    build_hold_store, build_press_refresh, build_scene_lock_clamp)
from midisc.scene_ui import (  # noqa: E402
    build_clear_scene, build_copy_scene, build_pad_has_locks, build_paste_scene,
    build_release_mix)
from midisc.morph import (  # noqa: E402
    build_morph, build_rebuild_lock_mask, build_scene_after_plock, build_scene_applied,
    build_voice_reload_d2, build_write_remixed, build_xf_after, build_xf_mix_out)

SYMBOLS.update(_symbols(mm))

# Each region, in build.py's own order; (routine symbol, builder, args).
REGIONS = {
    "safe_cave": (mm.SAFE_CAVE, [
        ("dirty", build_dirty, ()),
        ("clamp", build_scene_lock_clamp, ()),
        ("pack", build_pack, ()), ("unpack", build_unpack, ()),
        ("save", build_save_ui, ()), ("rel_after", build_reload_after, ()),
        ("xf_mix", build_xf_mix_out, ()),
        ("xf2", build_xf_after, (mm.XF_AFTER2_CONT, mm.XF_AFTER2_STOCK)),
        ("plock", build_scene_after_plock, ())]),
    "cave2": (mm.CAVE2, [("rebuild", build_rebuild_lock_mask, ())]),
    "code2": (mm.CODE2, [
        ("after", build_after_apply, ()), ("apply", build_apply_wrap, (AFTER_SENT,)),
        ("reload", build_reload_ui, (REL_AFTER_SENT,)),
        ("bank_sw", build_bank_switch, ()), ("bank_inv", build_bank_invalidate, ()),
        ("scene_done", build_scene_applied, ()), ("write_mix", build_write_remixed, ())]),
    "stub": (mm.STUB, [
        ("xf1", build_xf_after, (mm.XF_AFTER1_CONT, mm.XF_AFTER1_STOCK)),
        ("hold_a", build_hold_store, ("a",)), ("hold_b", build_hold_store, ("b",)),
        ("dial", build_dial, ()), ("taddi", build_addi_d0, ()), ("paddi", build_addi_d1, ()),
        ("pad", build_pad_has_locks, ()), ("press", build_press_refresh, ()),
        ("release", build_release_mix, ()),
        ("pst_sc", build_paste_scene, (mm.CLIP,)), ("clr_sc", build_clear_scene, ()),
        ("cpy_sc", build_copy_scene, (mm.CLIP,)), ("morph", build_morph, ()),
        ("bank_pub", build_bank_publish, ())]),
    "project_cave": (mm.PROJECT_CAVE, [
        ("clr_pt", build_clear_part, ()),
        ("after_proj", build_after_project_load, (mm.AFTER_PROJECT_LOAD_CONT,))]),
    "voice_reload": (mm.VOICE_RELOAD_CAVE, [
        ("voice_rel", build_voice_reload_d2, ())]),
    "enc_unlock": (mm.ENC_UNLOCK_CAVE, [
        ("unlock", build_enc_unlock, ()),
        ("hook_a", build_enc_press_hook, (mm.ENC_PRESS_A_CONT, mm.ENC_PRESS_A_BAIL, UNLOCK_SENT)),
        ("hook_b", build_enc_press_hook, (mm.ENC_PRESS_B_CONT, mm.ENC_PRESS_B_BAIL, UNLOCK_SENT))]),
}

HEADER = """| {name} -- midisc cave, emitted from tools/midisc/*.py by tools/gas_port.py.
| DO NOT EDIT BY HAND: regenerate with `python3 tools/gas_port.py`, which also
| proves this file assembles to the bytes the Python encoder produces.
| Cross-cave references are linker symbols (see gas_port.py); everything
| else is the firmware's own address and stays literal.
        .text
"""


def build_all():
    """Run every builder; return {region: (base, [(name, bytes, lines)])}."""
    global CURRENT
    out = {}
    for region, (base, routines) in REGIONS.items():
        got = []
        for name, fn, args in routines:
            CURRENT = name
            before = len(INSTANCES)
            b = fn(*args)
            made = INSTANCES[before:]
            assert len(made) == 1, f"{name}: builder created {len(made)} Asm instances"
            got.append((name, b, made[0].lines))
        out[region] = (base, got)
    return out


def write_sources(built):
    OUT.mkdir(exist_ok=True)
    for region, (base, routines) in built.items():
        text = HEADER.format(name=region)
        for name, _b, lines in routines:
            text += f"\n        .global {name}\n{name}:\n" + "\n".join(lines) + "\n"
        (OUT / f"{region}.s").write_text(text)
    (OUT / "msc.s").write_text(
        "| MSC -- 16 scenes x 8 tracks x 32 flat locks, one byte each; 0xff = no lock.\n"
        "| Placed by the linker; every cave reaches it through the `msc` symbol.\n"
        "        .text\n        .global msc\nmsc:    .fill 4096,1,0xff\n")
    (OUT / "state.s").write_text(
        "| The four state words build.py used to keep just past the STUB.\n"
        "        .text\n"
        "        .global last_part, unpack_src, last_bank, apply_ret\n"
        "last_part:  .byte 0xff\nunpack_src: .byte 0xff\nlast_bank:  .byte 0xff\n"
        "            .byte 0\napply_ret:  .long 0\n")


def his_addresses(built):
    """Where build.py links each routine: region base + cumulative length."""
    at = {}
    for region, (base, routines) in built.items():
        off = 0
        for name, b, _ in routines:
            at[name] = base + off
            off += len(b)
    at.update({"msc": mm.MSC, "last_part": mm.LAST_PART, "unpack_src": mm.UNPACK_SRC,
               "last_bank": mm.LAST_BANK, "apply_ret": mm.APPLY_RET})
    return at


def his_bytes(built, at):
    """Each region as build.py would link it: sentinels patched to addresses
    (its fix_jsr, generalised to every sentinel we hand a builder)."""
    out = {}
    for region, (base, routines) in built.items():
        blob = bytearray(b"".join(b for _, b, _ in routines))
        for sent, name in SYMBOLS.items():
            needle = sent.to_bytes(4, "big")
            i = blob.find(needle)
            while i >= 0:
                blob[i:i + 4] = at[name].to_bytes(4, "big")
                i = blob.find(needle, i + 4)
        out[region] = bytes(blob)
    return out


def assemble(src: pathlib.Path, at: int, defsyms: dict) -> bytes:
    with tempfile.TemporaryDirectory() as td:
        o, e, b = (pathlib.Path(td) / n for n in ("u.o", "u.elf", "u.bin"))
        subprocess.run(["m68k-elf-as", "-mcpu=5475", "-o", o, src], check=True)
        subprocess.run(["m68k-elf-ld", f"-Ttext=0x{at:x}",
                        *[f"--defsym={n}=0x{v:x}" for n, v in defsyms.items()],
                        "-o", e, o], check=True, capture_output=True)
        subprocess.run(["m68k-elf-objcopy", "-O", "binary", "-j", ".text", e, b], check=True)
        return b.read_bytes()


def verify(built):
    at = his_addresses(built)
    want = his_bytes(built, at)
    ok = True
    for region, (base, routines) in built.items():
        local = {name for name, _, _ in routines}
        defs = {n: a for n, a in at.items() if n not in local}
        got = assemble(OUT / f"{region}.s", base, defs)
        if base % 4 and got[:2] == b"\x4e\x71" and len(got) == len(want[region]) + 2:
            # ld aligns .text to 4 and pads a 2-mod-4 -Ttext with one nop;
            # build.py packs CAVE2 at such an address. Content is what we
            # compare; a linker-placed unit simply lands aligned.
            print(f"  ({region}: 2-byte alignment pad at 0x{base:08x} ignored)")
            got = got[2:]
        same = got == want[region]
        ok &= same
        print(f"  {region:11s} {len(got):5d} B at 0x{base:08x}  "
              f"{'IDENTICAL' if same else 'DIFFERS'}")
        if not same:
            n = next((i for i, (x, y) in enumerate(zip(got, want[region])) if x != y),
                     min(len(got), len(want[region])))
            print(f"    first difference at +0x{n:x}: got {got[n:n+8].hex()} want "
                  f"{want[region][n:n+8].hex()} (sizes {len(got)} vs {len(want[region])})")
    return ok


def main():
    for t in ("m68k-elf-as", "m68k-elf-ld", "m68k-elf-objcopy"):
        if not shutil.which(t):
            sys.exit(f"need {t} (brew install m68k-elf-gcc)")
    built = build_all()
    write_sources(built)
    print(f"wrote {len(built) + 2} sources to {OUT}/")
    if not verify(built):
        sys.exit("gas_port: a region does not reproduce the encoder's bytes")
    print("every region assembles to the encoder's bytes at build.py's addresses")


if __name__ == "__main__":
    main()
