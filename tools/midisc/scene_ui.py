"""midisc — Octatrack 1.40C MIDI scenes OS patch."""
from __future__ import annotations

from ot3_asm import Asm

from .memory_map import *  # noqa: F403
from .emit import emit_ensure_msc, emit_force_xf_mix, emit_invalidate_lock_masks

def build_pad_has_locks() -> bytes:
    a = Asm()
    a.hex("4fefffe4")
    a.hex("48d704fc")
    emit_ensure_msc(a, "pad_sync")

    a.move_l_sp(0x20, 2)
    a.move_l_dd(2, 0)
    a.andi(0xF, 0)
    a.lsl(8, 0)
    a.movea_imm(MSC, 0)
    a.adda_d(0, 0)

    a.move_l_imm(256, 1)
    a.label("loop")
    a.mvz_b_ind(0, 0)
    a.cmpi(0xFF, 0)
    a.bne("hit")
    a.hex("5288")
    a.hex("5381")
    a.bne("loop")

    a.move_l_sp(0x20, 0)
    a.jmp(PAD_CONT)

    a.label("hit")
    a.moveq(1, 0)
    a.hex("4cd704fc")
    a.hex("4fef001c")
    a.rts()
    return a.link()


def build_clear_scene() -> bytes:
    a = Asm()
    a.jsr(SENT_UNPACK)
    a.push("d0", "d1", "d2", "a0")
    a.move_l_sp(0x14, 0)
    a.andi(0xF, 0)
    a.lsl(8, 0)
    a.movea_imm(MSC, 0)
    a.adda_d(0, 0)
    a.move_l_imm(256, 1)
    a.label("ff")
    a.hex("10bc00ff")
    a.hex("5288")
    a.hex("5381")
    a.bne("ff")
    # If this was the last lock, pack skips durable — wipe magics so shadow
    # cannot resurrect the cleared scene.
    a.mvz_b_abs(PART_DISP, 2)
    a.andi(0xF, 2)
    a.move_l_dd(2, 0)
    a.move_l_imm(0x18B2, 1)
    a.muls(0, 1)
    a.movea_abs(BANK_PTR, 0)
    a.adda_d(1, 0)
    a.adda_imm(SPARSE_OFF, 0)
    a.hex("4250")  # clr.w working 'MS'
    a.movea_abs(BANK_PTR, 0)
    a.adda_d(1, 0)
    a.adda_imm(SHADOW_SPARSE_OFF, 0)
    a.hex("4250")  # clr.w shadow 'MS'
    a.pop("a0", "d2", "d1", "d0")
    a.mvz_b_abs(PART_DISP, 0)
    a.move_b_d_abs(0, LAST_PART)
    a.jsr(SENT_PACK)
    a.jsr(SENT_DIRTY)
    emit_invalidate_lock_masks(a)
    emit_force_xf_mix(a)
    a.jsr(SENT_XF_MIX)
    a.jmp(STOCK_CLEAR_SCENE)
    return a.link()


def build_copy_scene(clip: int) -> bytes:
    a = Asm()
    a.jsr(SENT_UNPACK)
    a.push("d0", "d1", "a0", "a1")
    a.move_l_sp(0x18, 0)
    a.andi(0xF, 0)
    a.lsl(8, 0)
    a.movea_imm(MSC, 0)
    a.adda_d(0, 0)
    a.movea_imm(clip, 1)
    a.move_l_imm(256, 1)
    a.label("cp")
    a.hex("1018")
    a.hex("12c0")
    a.hex("5381")
    a.bne("cp")
    a.pop("a1", "a0", "d1", "d0")
    a.jmp(STOCK_COPY_SCENE)
    return a.link()


def build_paste_scene(clip: int) -> bytes:
    a = Asm()
    a.move_l_abs_d(0x460D0FFA, 0)
    a.cmpi(0x10, 0)
    a.bne("stock")

    a.jsr(SENT_UNPACK)
    a.push("d0", "d1", "a0", "a1")
    a.move_l_sp(0x18, 0)
    a.andi(0xF, 0)
    a.lsl(8, 0)
    a.movea_imm(MSC, 0)
    a.adda_d(0, 0)
    a.hex("2248")
    a.movea_imm(clip, 0)
    a.move_l_imm(256, 1)
    a.label("ps")
    a.hex("1018")
    a.hex("12c0")
    a.hex("5381")
    a.bne("ps")
    a.pop("a1", "a0", "d1", "d0")
    a.mvz_b_abs(PART_DISP, 0)
    a.move_b_d_abs(0, LAST_PART)
    a.jsr(SENT_PACK)
    a.jsr(SENT_DIRTY)
    emit_invalidate_lock_masks(a)
    emit_force_xf_mix(a)
    a.jsr(SENT_XF_MIX)

    a.label("stock")
    a.jmp(STOCK_PASTE_SCENE)
    return a.link()


def build_release_mix() -> bytes:
    """Scene pad release: clear held + UI only. No xf_mix — must not touch playback."""
    a = Asm()
    a.hex("42b9460d1694")  # clr.l held-pad (stock insn we replace)
    a.hex("42b9460d169c")  # clr.l SCENE_HELD
    a.hex("4878ffff")
    a.jsr(UI_OVERLAY)
    a.jsr(PRESS_UI)
    a.hex("508f")
    a.jmp(RELEASE_CONT)
    return a.link()


