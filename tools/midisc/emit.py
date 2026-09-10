"""midisc — Octatrack 1.40C MIDI scenes OS patch."""
from __future__ import annotations

from ot3_asm import Asm

from .memory_map import *  # noqa: F403

def emit_ensure_msc(a: Asm, synced: str = "synced") -> None:
    """If MSC is not mirroring PART_DISP, unpack first (reboot / part switch)."""
    a.mvz_b_abs(LAST_PART, 0)
    a.mvz_b_abs(PART_DISP, 1)
    a.hex("b081")
    a.beq(synced)
    a.jsr(SENT_UNPACK)
    a.label(synced)

def emit_ctrl_enable(a: Asm, track_dn: int, flat_dn: int) -> None:
    """Clear CTRL OFF bit for flat on track. Clobbers d0,a0; track/flat ≠ d0."""
    a.move_l_dd(track_dn, 0)
    a.lsl(2, 0)
    a.movea_d(0, 0)
    a.adda_imm(CTRL_BASE, 0)
    a.moveq(1, 0)
    a.lsl_reg(flat_dn, 0)
    a.hex("4680")  # not.l d0
    a.hex("c1a8017e")  # and.l d0, $17e(a0)



def emit_invalidate_lock_masks(a: Asm) -> None:
    a.hex(f"42b9{LOCK_MAGIC:08x}")  # clr.l magic — PLOCK rebuilds lazily


def emit_force_xf_mix(a: Asm) -> None:
    a.moveq(0xFF, 0)
    a.move_b_d_abs(0, LOCK_LAST_XF)




