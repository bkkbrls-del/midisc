"""midisc — Octatrack 1.40C MIDI scenes OS patch."""
from __future__ import annotations

from ot3_asm import Asm

from .memory_map import *  # noqa: F403

def emit_ensure_msc(a: Asm, synced: str = "synced") -> None:
    """Sync MSC to APPLY_PART (80001829) — same commit as audio part apply.

    PART_DISP lags until pattern start (stock copies pattern→PART_DISP at
    0x40062148). Following PART_DISP made MIDI wait a full pattern while audio
    (STOCK_APPLY) had already switched. apply_bridge publishes PART_DISP and
    PAT_ACTIVE (80000003) from APPLY_PART then xf_mix's immediately.
    """
    a.mvz_b_abs(LAST_PART, 0)
    a.cmpi(0xFF, 0)
    a.beq("do_disp")
    a.mvz_b_abs(APPLY_PART, 1)
    a.hex("b081")
    a.beq(synced)
    a.move_b_d_abs(1, UNPACK_SRC)
    a.jsr(SENT_UNPACK)
    a.bra(synced)
    a.label("do_disp")
    a.jsr(SENT_UNPACK)  # UNPACK_SRC=FF → PART_DISP
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




