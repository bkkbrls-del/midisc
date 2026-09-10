"""midisc — Octatrack 1.40C MIDI scenes OS patch."""
from __future__ import annotations

from ot3_asm import Asm

from .memory_map import *  # noqa: F403
from .emit import emit_ensure_msc, emit_force_xf_mix, emit_invalidate_lock_masks


def build_scene_lock_clamp() -> bytes:
    """Clamp scene-lock d1; flat d5. ARP = PAGE_MODE 2 (stock MIDI map).

    Evidence: FUN_40031da4 MIDI cases — 0=NOTE, 1=LFO, 2=ARP, 3=CTRL1, 4=CTRL2
    (docs/PARAM_PAGES.md). ARP knobs TRAN LEG MODE SPD RNGE NLEN; flats 12-17.
    enc1 LEG 0-1, enc2 MODE 0-6, enc3 SPD 0-95, enc4 RNGE 0-7; else 0-127.
    Clobbers d0,d2.
    """
    a = Asm()
    a.tst_d(1)
    a.bpl("pos")
    a.moveq(0, 1)
    a.rts()
    a.label("pos")
    a.move_l_abs_d(PAGE_MODE, 0)
    a.cmpi(2, 0)  # ARP — not 0 NOTE, not 1 LFO
    a.bne("std")
    a.move_l_dd(5, 0)
    a.addi(0xFFFFFFF4, 0)  # flat - 12 => encoder on page 2
    a.moveq(1, 2)
    a.cmpi(1, 0)
    a.beq("cap")
    a.moveq(6, 2)
    a.cmpi(2, 0)
    a.beq("cap")
    a.moveq(95, 2)
    a.cmpi(3, 0)
    a.beq("cap")
    a.moveq(7, 2)
    a.cmpi(4, 0)
    a.bne("std")
    a.label("cap")
    a.hex("b282")  # cmp.l d2, d1
    a.bhi("clip")  # d1 > d2
    a.bra("ok")
    a.label("clip")
    a.move_l_dd(2, 1)
    a.bra("ok")
    a.label("std")
    a.cmpi(0x80, 1)
    a.bcs("ok")
    a.moveq(0x7F, 1)
    a.label("ok")
    a.rts()
    return a.link()



def build_enc_unlock() -> bytes:
    """MSC[held scene][track][flat] = 0xFF; pack; dirty; remix; UI."""
    a = Asm()
    # d5 = flat (must survive emit_ensure_msc which clobbers d0/d1)
    a.push("d0", "d1", "d2", "d3", "d5", "a0", "a1")
    # d4 = event still live from press fn; encoder = d4 - 0x38
    a.move_l_dd(4, 3)
    a.addi(0xFFFFFFC8, 3)
    a.cmpi(5, 3)
    a.bhi("out")
    # flat = PAGE_MODE*6 + encoder  (same as hold_store)
    a.move_l_abs_d(PAGE_MODE, 0)
    a.move_l_dd(0, 5)
    a.lsl(3, 5)
    a.add_dd(0, 0)
    a.sub_dd(0, 5)
    a.add_dd(3, 5)
    a.andi(0x1F, 5)
    emit_ensure_msc(a, "ul_sync")
    a.move_l_abs_d(SCENE_HELD, 2)
    a.mvz_b_abs(PART_DISP, 0)
    a.move_l_imm(0x18B2, 3)
    a.muls(0, 3)
    a.movea_abs(BANK_PTR, 0)
    a.adda_d(3, 0)
    a.adda_imm(SCENE_ASSIGN, 0)
    a.cmpi(1, 2)
    a.beq("sc_a")
    a.mvz_b_disp(1, 0, 2)
    a.bra("got_sc")
    a.label("sc_a")
    a.mvz_b_ind(0, 2)
    a.label("got_sc")
    a.cmpi(0xFF, 2)
    a.beq("out")
    a.andi(0xF, 2)
    a.lsl(8, 2)
    a.mvz_b_abs(TRACK_DISP, 0)
    a.andi(7, 0)
    a.lsl(5, 0)
    a.add_dd(0, 2)
    a.add_dd(5, 2)
    a.movea_imm(MSC, 0)
    a.adda_d(2, 0)
    a.moveq(0xFF, 1)
    a.move_b_d_ind(1, 0)
    a.mvz_b_abs(PART_DISP, 0)
    a.move_b_d_abs(0, LAST_PART)
    a.jsr(SENT_PACK)
    a.jsr(SENT_DIRTY)
    emit_invalidate_lock_masks(a)
    emit_force_xf_mix(a)
    a.jsr(SENT_XF_MIX)
    a.hex("4878ffff")
    a.jsr(UI_OVERLAY)
    a.hex("588f")
    a.label("out")
    a.pop("a1", "a0", "d5", "d3", "d2", "d1", "d0")
    a.rts()
    return a.link()


def build_enc_press_hook(cont: int, bail: int, unlock_abs: int) -> bytes:
    """Replace stock tst MIDI + bne bail. Unlock when SCENE_HELD."""
    a = Asm()
    a.tst_abs(MIDI_FLAG)
    a.beq("audio")
    a.move_l_abs_d(SCENE_HELD, 0)
    a.tst_d(0)
    a.beq("bail")
    a.jsr(unlock_abs)
    a.label("bail")
    a.jmp(bail)
    a.label("audio")
    a.jmp(cont)
    return a.link()


def build_hold_store(which: str) -> bytes:
    is_a = which == "a"
    audio = AUDIO_A if is_a else AUDIO_B
    bail = BAIL_A if is_a else BAIL_B
    tail = TAIL_A if is_a else TAIL_B
    assign_disp = 0 if is_a else 1

    a = Asm()
    a.tst_abs(MIDI_FLAG)
    a.beq("audio")

    # Ensure only — never wipe MSC every tick. Always-unpack + empty/missed
    # CKPT cleared all locks then reseeded from 8f162+delta → 2 values, and
    # every other lock vanished between encoder events.
    emit_ensure_msc(a, "hold_sync")
    a.move_l_abs_d(PAGE_MODE, 0)
    a.move_l_dd(0, 5)
    a.lsl(3, 5)
    a.add_dd(0, 0)
    a.sub_dd(0, 5)
    a.add_dd(3, 5)
    a.andi(0x1F, 5)

    a.mvz_b_abs(PAT_DISP, 0)
    a.move_l_imm(0x18B2, 1)
    a.muls(0, 1)
    a.movea_abs(BANK_PTR, 0)
    a.adda_d(1, 0)
    a.adda_imm(SCENE_ASSIGN, 0)
    if assign_disp:
        a.mvz_b_disp(1, 0, 4)
    else:
        a.mvz_b_ind(0, 4)
    a.cmpi(0xFF, 4)
    a.beq("bail")
    a.andi(0xF, 4)

    a.move_l_dd(4, 2)
    a.lsl(8, 2)
    a.mvz_b_abs(TRACK_DISP, 0)
    a.andi(7, 0)
    a.lsl(5, 0)
    a.add_dd(0, 2)
    a.add_dd(5, 2)

    a.movea_imm(MSC, 0)
    a.adda_d(2, 0)
    a.hex("2248")
    a.mvz_b_ind(0, 1)
    a.cmpi(0xFF, 1)
    a.bne("have_val")

    a.mvz_b_abs(PAT_DISP, 0)
    a.move_l_imm(0x18B2, 1)
    a.muls(0, 1)
    a.mvz_b_abs(TRACK_DISP, 0)
    a.andi(7, 0)
    a.lsl(5, 0)
    a.add_dd(0, 1)
    a.add_dd(5, 1)
    a.movea_abs(BANK_PTR, 0)
    a.adda_d(1, 0)
    a.adda_imm(0x8F162, 0)
    a.mvz_b_ind(0, 1)

    a.label("have_val")
    a.add_dd(6, 1)
    a.jsr(SENT_CLAMP)  # 0-127; ARP page LEG/MODE/SPD/RNG tighter

    a.move_b_d_ind(1, 1)  # MSC only — unlocked UI (8f162) stays put

    # Always hear at XF: write MSC then mix (never poke sinks live).
    a.mvz_b_abs(PART_DISP, 0)
    a.move_b_d_abs(0, LAST_PART)
    a.jsr(SENT_PACK)
    a.jsr(SENT_DIRTY)
    emit_invalidate_lock_masks(a)
    emit_force_xf_mix(a)
    a.jsr(SENT_XF_MIX)
    a.jmp(tail)

    a.label("bail")
    a.jmp(bail)
    a.label("audio")
    a.jmp(audio)
    return a.link()


def build_dial() -> bytes:
    a = Asm()
    a.move_l_abs_d(SCENE_HELD, 2)
    a.tst_d(2)
    a.beq("live")

    a.push("d1", "d2", "d3", "a0", "a1")
    emit_ensure_msc(a, "dial_sync")

    a.mvz_b_abs(PAT_DISP, 0)
    a.move_l_imm(0x18B2, 1)
    a.muls(0, 1)
    a.movea_abs(BANK_PTR, 0)
    a.adda_d(1, 0)
    a.hex("2248")
    a.adda_imm(SCENE_ASSIGN, 0)

    a.cmpi(1, 2)
    a.beq("sel_a")
    a.cmpi(2, 2)
    a.bne("fallback")

    a.mvz_b_disp(1, 0, 1)
    a.bra("got_scene")
    a.label("sel_a")
    a.mvz_b_ind(0, 1)
    a.label("got_scene")
    a.cmpi(0xFF, 1)
    a.beq("fallback")
    a.andi(0xF, 1)

    a.lsl(8, 1)
    a.movea_imm(MSC, 0)
    a.hex("2008")
    a.add_dd(1, 0)
    a.mvz_b_abs(TRACK_DISP, 3)
    a.andi(7, 3)
    a.lsl(5, 3)
    a.add_dd(3, 0)
    a.move_l_abs_d(PAGE_MODE, 2)
    a.move_l_dd(2, 1)
    a.lsl(3, 1)
    a.add_dd(2, 2)
    a.sub_dd(2, 1)
    a.add_dd(1, 0)
    a.hex("d08c")
    a.hex("2040")
    a.hex("7110")
    a.cmpi(0xFF, 0)
    a.beq("fallback")
    a.cmpi(0x80, 0)
    a.bcc("fallback")

    a.moveq(1, 1)
    a.or_dd(1, 5)
    a.pop("a1", "a0", "d3", "d2", "d1")
    a.jmp(DIAL_DRAW)

    a.label("fallback")
    a.pop("a1", "a0", "d3", "d2", "d1")
    a.label("live")
    a.hex(DIAL_LIVE_ALL)
    a.jmp(DIAL_DRAW)
    return a.link()


def build_addi_d0() -> bytes:
    """Replace addi #8f3e2,d0 — jsr from TRACK_ADDI / LED lock-paint sites."""
    a = Asm()
    a.tst_abs(MIDI_FLAG)
    a.beq("aud")
    a.push("d1", "d2")
    a.mvz_b_abs(PAT_DISP, 1)
    a.move_l_imm(0x18B2, 2)
    a.muls(1, 2)
    a.sub_dd(2, 0)
    a.move_l_abs_d(BANK_PTR, 1)
    a.sub_dd(1, 0)
    a.addi(MSC, 0)
    a.pop("d2", "d1")
    a.rts()
    a.label("aud")
    a.addi(0x8F3E2, 0)
    a.rts()
    return a.link()


def build_addi_d1() -> bytes:
    """Replace addi #8f3e2,d1 — jsr from PAGE_ADDI."""
    a = Asm()
    a.tst_abs(MIDI_FLAG)
    a.beq("aud")
    a.push("d0", "d2")
    a.mvz_b_abs(PAT_DISP, 0)
    a.move_l_imm(0x18B2, 2)
    a.muls(0, 2)
    a.sub_dd(2, 1)
    a.move_l_abs_d(BANK_PTR, 0)
    a.sub_dd(0, 1)
    a.addi(MSC, 1)
    a.pop("d2", "d0")
    a.rts()
    a.label("aud")
    a.addi(0x8F3E2, 1)
    a.rts()
    return a.link()


def build_press_refresh() -> bytes:
    a = Asm()
    a.jsr(PRESS_UI)
    a.tst_abs(MIDI_FLAG)
    a.beq("done")
    emit_ensure_msc(a, "press_sync")
    a.hex("4878ffff")
    a.jsr(UI_OVERLAY)
    a.hex("588f")
    a.label("done")
    a.hex("241f")
    a.jmp(PRESS_TAIL)
    return a.link()


