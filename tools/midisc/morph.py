"""midisc — Octatrack 1.40C MIDI scenes OS patch."""

from __future__ import annotations



from ot3_asm import Asm



from .memory_map import *  # noqa: F403

from .emit import emit_ctrl_enable, emit_force_xf_mix, emit_invalidate_lock_masks



def build_rebuild_lock_mask() -> bytes:

    """Cold: ents + TNC/TOFF. Preserves d7/a1. PLOCK-only."""

    a = Asm()

    a.hex("2f07")

    a.hex("2f09")

    a.moveq(0, 6)



    a.movea_abs(BANK_PTR, 0)

    a.move_a_d(0, 0)

    a.tst_d(0)

    a.beq("abort")  # do not publish magic



    a.movea_imm(LOCK_TNC, 0)

    a.moveq(8, 1)

    a.label("zt")

    a.hex("4210")

    a.hex("5288")

    a.hex("5381")

    a.bne("zt")



    a.mvz_b_abs(PART_DISP, 0)

    a.andi(0xF, 0)

    a.move_l_imm(0x18B2, 1)

    a.muls(0, 1)

    a.movea_abs(BANK_PTR, 0)

    a.adda_d(1, 0)

    a.adda_imm(SCENE_ASSIGN, 0)

    a.mvz_b_ind(0, 3)

    a.mvz_b_disp(1, 0, 5)



    a.moveq(0, 4)

    a.label("tr")

    a.movea_imm(LOCK_TOFF, 0)

    a.adda_d(4, 0)

    a.move_b_d_ind(6, 0)



    a.moveq(0, 1)

    a.label("fl")

    a.moveq(0xFF, 0)

    a.cmpi(0xFF, 3)

    a.beq("va_d")

    a.move_l_dd(3, 2)

    a.andi(0xF, 2)

    a.lsl(8, 2)

    a.movea_imm(MSC, 0)

    a.adda_d(2, 0)

    a.move_l_dd(4, 2)

    a.lsl(5, 2)

    a.adda_d(2, 0)

    a.adda_d(1, 0)

    a.mvz_b_ind(0, 0)

    a.label("va_d")

    a.moveq(0xFF, 2)

    a.cmpi(0xFF, 5)

    a.beq("vb_d")

    a.move_l_dd(5, 7)

    a.andi(0xF, 7)

    a.lsl(8, 7)

    a.movea_imm(MSC, 0)

    a.adda_d(7, 0)

    a.move_l_dd(4, 7)

    a.lsl(5, 7)

    a.adda_d(7, 0)

    a.adda_d(1, 0)

    a.mvz_b_ind(0, 2)

    a.label("vb_d")

    a.cmpi(0xFF, 0)

    a.bne("keep")

    a.cmpi(0xFF, 2)

    a.beq("nxf")

    a.label("keep")

    a.cmpi(LOCK_ENTS_MAX, 6)

    a.bcc("fin")

    a.move_l_dd(4, 7)

    a.lsl(5, 7)

    a.or_dd(1, 7)

    a.hex("2f02")

    a.movea_imm(LOCK_ENTS, 0)

    a.move_l_dd(6, 2)

    a.add_dd(2, 2)

    a.add_dd(6, 2)

    a.adda_d(2, 0)

    a.hex("10c7")

    a.hex("10c0")

    a.hex("241f")

    a.hex("10c2")

    a.addq(1, 6)

    a.movea_imm(LOCK_TNC, 0)

    a.adda_d(4, 0)

    a.hex("5210")

    a.label("nxf")

    a.addq(1, 1)

    a.cmpi(30, 1)

    a.bcs("fl")

    a.addq(1, 4)

    a.cmpi(8, 4)

    a.bcs("tr")

    a.label("fin")

    a.move_b_d_abs(6, LOCK_COUNT)

    a.move_l_imm(LOCK_MAGIC_VAL, 0)

    a.move_l_d_abs(0, LOCK_MAGIC)

    a.hex("225f")  # a1

    a.hex("2e1f")  # d7

    a.rts()

    a.label("abort")

    a.hex("225f")

    a.hex("2e1f")

    a.rts()

    return a.link()





def build_plock_morph_body() -> bytes:
    """a1=row, d7=track. Full-A/B only: scene-locked flats on that end -> row=VOICE.

    Mid-XF: no row pokes (M had no stepping). Pure end: step plocks must vanish
    so notes/params hear absolute scene.
    """
    a = Asm()
    a.move_l_abs_d(XF_RAM, 5)
    a.andi(0x7F, 5)
    a.move_l_imm(0x7F, 0)
    a.sub_dd(5, 0)
    a.move_l_dd(0, 5)  # d5 = weight toward B (0=full A, 0x7F=full B)
    a.tst_d(5)
    a.beq("pure")
    a.cmpi(0x7F, 5)
    a.bne("out")  # mid — leave row as stock+xf_mix LFO only
    a.label("pure")

    a.mvz_b_abs(PART_DISP, 0)
    a.andi(0xF, 0)
    a.move_l_imm(0x18B2, 6)
    a.muls(0, 6)
    a.movea_abs(BANK_PTR, 0)
    a.adda_d(6, 0)
    a.adda_imm(SCENE_ASSIGN, 0)
    a.mvz_b_ind(0, 3)       # scene A id
    a.mvz_b_disp(1, 0, 4)   # scene B id

    # pick active end: d5==0 -> A in d3; d5==0x7F -> B in d3
    a.tst_d(5)
    a.beq("use_a")
    a.move_l_dd(4, 3)
    a.label("use_a")
    a.cmpi(0xFF, 3)
    a.beq("out")
    a.andi(0xF, 3)
    a.lsl(8, 3)
    a.movea_imm(MSC, 2)
    a.adda_d(3, 2)
    a.move_l_dd(7, 3)
    a.lsl(5, 3)
    a.adda_d(3, 2)  # a2 = MSC[active][track]

    a.moveq(0, 1)
    a.label("lp")
    a.hex("204A")
    a.adda_d(1, 0)
    a.mvz_b_ind(0, 5)
    a.cmpi(0xFF, 5)
    a.beq("nx")
    a.move_l_dd(7, 0)
    a.lsl(6, 0)
    a.move_l_dd(7, 4)
    a.lsl(2, 4)
    a.add_dd(4, 0)
    a.add_dd(1, 0)
    a.movea_imm(MIDI_VOICE, 0)
    a.adda_d(0, 0)
    a.mvz_b_ind(0, 0)
    a.hex("2049")
    a.adda_d(1, 0)
    a.move_b_d_ind(0, 0)
    a.label("nx")
    a.addq(1, 1)
    a.cmpi(30, 1)
    a.bcs("lp")
    a.label("out")
    a.rts()
    return a.link()


def build_scene_after_plock(morph_abs: int = 0) -> bytes:
    """M path + pure-end row suppress (full A/B absolute scene)."""
    a = Asm()
    a.hex("93fc00000020")
    a.move_a_d(1, 0)
    a.move_a_d(5, 1)
    a.sub_dd(1, 0)
    a.asr(5, 0)
    a.move_l_dd(0, 7)
    a.cmpi(8, 7)
    a.bcc("stock")

    a.hex("2f09")
    a.move_l_dd(7, 0)
    a.lsl(5, 0)
    a.movea_imm(TRIG_SNAP, 0)
    a.adda_d(0, 0)
    a.hex("2257")
    for _ in range(8):
        a.hex("20d9")
    a.hex("225f")

    a.mvz_b_abs(PART_DISP, 0)
    a.andi(0xF, 0)
    a.move_l_imm(0x18B2, 6)
    a.muls(0, 6)
    a.movea_abs(BANK_PTR, 0)
    a.adda_d(6, 0)
    a.adda_imm(SCENE_ASSIGN, 0)
    a.mvz_b_ind(0, 3)
    a.mvz_b_disp(1, 0, 4)
    a.cmpi(0xFF, 3)
    a.bne("sc")
    a.cmpi(0xFF, 4)
    a.beq("stock")

    a.label("sc")
    a.jsr(SENT_XF_MIX)
    a.jsr(SENT_REBUILD_MASK)  # full A/B only: row=VOICE for that end's locks
    a.label("stock")
    a.hex(PLOCK_DONE_STOCK)
    return a.link()


def build_xf_mix_out() -> bytes:
    """Scene x XF -> VOICE. Never SOUND/8f162 store.

    Audio XF_MORPH: empty = TRIG_SNAP (trig) else behind; locked = MSC.
    Write VOICE always; scene-locked flats also write LFO (=VOICE) so XF
    offsets trigs instantly (continuous + plock). CC_TX on morph change.
    """
    a = Asm()
    a.push("d0", "d1", "d2", "d3", "d4", "d5", "d6", "d7", "a0", "a1")
    a.hex("2f0a")  # a2
    a.hex("2f0b")  # a3

    a.movea_abs(BANK_PTR, 0)
    a.move_a_d(0, 0)
    a.tst_d(0)
    a.beq("out")

    a.mvz_b_abs(PART_DISP, 0)
    a.andi(0xF, 0)
    a.move_l_imm(0x18B2, 7)
    a.muls(0, 7)

    # H: raw XF weight, no end-snap deadzone
    a.move_l_abs_d(XF_RAM, 5)
    a.andi(0x7F, 5)
    a.move_l_imm(0x7F, 0)
    a.sub_dd(5, 0)
    a.move_l_dd(0, 5)

    a.movea_abs(BANK_PTR, 0)
    a.adda_d(7, 0)
    a.adda_imm(SCENE_ASSIGN, 0)
    a.mvz_b_ind(0, 3)
    a.mvz_b_disp(1, 0, 1)

    a.movea_imm(0, 2)
    a.cmpi(0xFF, 3)
    a.beq("no_a")
    a.andi(0xF, 3)
    a.lsl(8, 3)
    a.movea_imm(MSC, 2)
    a.adda_d(3, 2)
    a.label("no_a")
    a.movea_imm(0, 3)
    a.cmpi(0xFF, 1)
    a.beq("no_b")
    a.andi(0xF, 1)
    a.lsl(8, 1)
    a.movea_imm(MSC, 3)
    a.adda_d(1, 3)
    a.label("no_b")

    a.move_l_imm(0, 6)
    a.label("tr")
    a.move_l_imm(0, 1)
    a.label("pr")

    a.move_l_dd(6, 0)
    a.lsl(5, 0)
    a.add_dd(1, 0)
    a.move_a_d(2, 4)
    a.tst_d(4)
    a.beq("va_ff")
    a.hex("204A")
    a.adda_d(0, 0)
    a.mvz_b_ind(0, 3)
    a.bra("va_got")
    a.label("va_ff")
    a.moveq(0xFF, 3)
    a.label("va_got")

    a.move_l_dd(6, 0)
    a.lsl(5, 0)
    a.add_dd(1, 0)
    a.move_a_d(3, 4)
    a.tst_d(4)
    a.beq("vb_ff")
    a.hex("204B")
    a.adda_d(0, 0)
    a.mvz_b_ind(0, 4)
    a.bra("vb_got")
    a.label("vb_ff")
    a.moveq(0xFF, 4)
    a.label("vb_got")

    a.cmpi(0xFF, 3)
    a.bne("a_ok")
    a.cmpi(0xFF, 4)
    a.bne("b_only")
    # Both unlocked: push behind so VOICE tracks UI
    a.move_l_dd(6, 0)
    a.lsl(5, 0)
    a.add_dd(1, 0)
    a.movea_abs(BANK_PTR, 0)
    a.adda_d(7, 0)
    a.adda_d(0, 0)
    a.adda_imm(MIDI_BEHIND, 0)
    a.mvz_b_ind(0, 0)
    a.bra("write_ui")  # no CC â€” dial path already transmits
    a.label("b_only")
    # Empty A: trig layer (LFO_BASE) like audio live; behind if FF
    a.move_l_dd(6, 0)
    a.lsl(5, 0)
    a.add_dd(1, 0)
    a.movea_imm(TRIG_SNAP, 0)
    a.adda_d(0, 0)
    a.mvz_b_ind(0, 3)
    a.cmpi(0xFF, 3)
    a.bne("mix")
    a.move_l_dd(6, 0)
    a.lsl(5, 0)
    a.add_dd(1, 0)
    a.movea_abs(BANK_PTR, 0)
    a.adda_d(7, 0)
    a.adda_d(0, 0)
    a.adda_imm(MIDI_BEHIND, 0)
    a.mvz_b_ind(0, 3)
    a.bra("mix")

    a.label("a_ok")
    a.cmpi(0xFF, 4)
    a.bne("mix")
    # Empty B: trig layer (LFO_BASE); behind if FF
    a.move_l_dd(6, 0)
    a.lsl(5, 0)
    a.add_dd(1, 0)
    a.movea_imm(TRIG_SNAP, 0)
    a.adda_d(0, 0)
    a.mvz_b_ind(0, 4)
    a.cmpi(0xFF, 4)
    a.bne("mix")
    a.move_l_dd(6, 0)
    a.lsl(5, 0)
    a.add_dd(1, 0)
    a.movea_abs(BANK_PTR, 0)
    a.adda_d(7, 0)
    a.adda_d(0, 0)
    a.adda_imm(MIDI_BEHIND, 0)
    a.mvz_b_ind(0, 4)

    a.label("mix")
    a.tst_d(5)
    a.beq("use_a")
    a.cmpi(0x7F, 5)
    a.bne("lerp")
    a.move_l_dd(4, 0)
    a.bra("write_morph")
    a.label("use_a")
    a.move_l_dd(3, 0)
    a.bra("write_morph")
    a.label("lerp")
    a.move_l_dd(4, 0)
    a.sub_dd(3, 0)
    a.muls(5, 0)
    a.asr(7, 0)
    a.add_dd(3, 0)

    a.label("write_ui")
    a.andi(0x7F, 0)
    a.move_l_dd(0, 2)
    a.move_l_dd(6, 0)
    a.lsl(6, 0)
    a.move_l_dd(6, 3)
    a.lsl(2, 3)
    a.add_dd(3, 0)
    a.add_dd(1, 0)
    a.movea_imm(MIDI_VOICE, 0)
    a.adda_d(0, 0)
    a.move_b_d_ind(2, 0)
    a.bra("ctrl")

    a.label("write_morph")
    a.andi(0x7F, 0)
    a.move_l_dd(0, 2)
    # VOICE addr; CC only when value changes (continuous XF like audio filter)
    a.move_l_dd(6, 0)
    a.lsl(6, 0)
    a.move_l_dd(6, 3)
    a.lsl(2, 3)
    a.add_dd(3, 0)
    a.add_dd(1, 0)
    a.movea_imm(MIDI_VOICE, 0)
    a.adda_d(0, 0)
    a.mvz_b_ind(0, 3)  # old
    a.move_b_d_ind(2, 0)
    a.hex("b682")  # cmp.l d2, d3
    a.beq("ctrl")
    a.push("d1", "d2", "d5", "d6", "d7")
    a.hex("2f0a2f0b")  # a2, a3
    a.hex("42a7")  # clr.l -(sp) arg3=0
    a.hex("2f02")  # value
    a.hex("2f01")  # flat
    a.hex("2f06")  # track
    a.jsr(CC_TX)
    a.hex("4fef0010")
    a.hex("265f245f")  # pop a3, a2
    a.pop("d7", "d6", "d5", "d2", "d1")

    a.label("ctrl")
    # Scene-locked flats: same value to LFO so XF offsets trigs instantly
    a.move_a_d(2, 0)
    a.tst_d(0)
    a.beq("lb")
    a.hex("204A")
    a.adda_d(1, 0)
    a.mvz_b_ind(0, 0)
    a.cmpi(0xFF, 0)
    a.bne("wl")
    a.label("lb")
    a.move_a_d(3, 0)
    a.tst_d(0)
    a.beq("nxc")
    a.hex("204B")
    a.adda_d(1, 0)
    a.mvz_b_ind(0, 0)
    a.cmpi(0xFF, 0)
    a.beq("nxc")
    a.label("wl")
    a.move_l_dd(6, 0)
    a.lsl(5, 0)
    a.add_dd(1, 0)
    a.movea_imm(LFO_BASE, 0)
    a.adda_d(0, 0)
    a.move_b_d_ind(2, 0)
    a.label("nxc")
    # CTRL1/2: clear OFF only (H)
    a.cmpi(18, 1)
    a.bcs("next")
    a.cmpi(30, 1)
    a.bcc("next")
    emit_ctrl_enable(a, 6, 1)

    a.label("next")
    a.addq(1, 1)
    a.cmpi(30, 1)
    a.bcs("pr")
    a.addq(1, 6)
    a.cmpi(8, 6)
    a.bcs("tr")

    a.label("out")
    a.hex("265f")
    a.hex("245f")
    a.pop("a1", "a0", "d7", "d6", "d5", "d4", "d3", "d2", "d1", "d0")
    a.rts()
    return a.link()


def build_morph() -> bytes:
    """After audio morph: ensure MSC only. Never xf_mix here (kills trigs)."""
    a = Asm()
    a.mvz_b_abs(LAST_PART, 0)
    a.mvz_b_abs(PART_DISP, 1)
    a.hex("b081")
    a.beq("go")
    a.jsr(SENT_UNPACK)
    a.label("go")
    a.jmp(MORPH_CONT)
    return a.link()


def build_xf_after(cont: int, stock_hex: str) -> bytes:

    """After stock XF publish insn: ensure MSC, mix at current XF, stock insn."""

    a = Asm()

    a.mvz_b_abs(LAST_PART, 0)

    a.mvz_b_abs(PART_DISP, 1)

    a.hex("b081")

    a.beq("ok")

    a.jsr(SENT_UNPACK)

    a.label("ok")
    a.jsr(SENT_XF_MIX)

    a.hex(stock_hex)

    a.jmp(cont)

    return a.link()





def build_scene_applied() -> bytes:

    """A/B scene press/assign: mix immediately at current XF.



    No MIDI_FLAG gate — MIDI scenes must update while UI is on audio.

    """

    a = Asm()

    a.mvz_b_abs(LAST_PART, 0)

    a.mvz_b_abs(PART_DISP, 1)

    a.hex("b081")

    a.beq("ok")

    a.jsr(SENT_UNPACK)

    a.label("ok")

    emit_invalidate_lock_masks(a)

    emit_force_xf_mix(a)

    a.jsr(SENT_XF_MIX)

    a.jmp(SCENE_DONE_CONT)

    return a.link()





def build_voice_reload_d2() -> bytes:

    """d4=track, d6=flat. d2 = MIDI_VOICE[track*0x44+flat]. rts.



    After xf_mix, stock still CC_TX / mirrors with dialed d2. Reload so full-B

    locks (esp. CTRL CCs) stay frozen while mid-XF B-only still morphs.

    """

    a = Asm()

    a.moveq(0x44, 0)

    a.muls(4, 0)

    a.add_dd(6, 0)

    a.movea_imm(MIDI_VOICE, 0)

    a.adda_d(0, 0)

    a.mvz_b_ind(0, 2)

    a.rts()

    return a.link()





def build_write_remixed() -> bytes:

    """After unlocked MIDI live write: re-apply scene x XF so locks win / XF holds.



    Then reload d2 from VOICE so stock CC_TX uses the mixed lock (MIDISC5).

    No MIDI_FLAG gate — keep morph sinks live while UI is on audio.

    """

    a = Asm()

    a.hex(WRITE_STOCK)

    a.jsr(SENT_XF_MIX)

    a.jsr(SENT_VOICE_RELOAD)

    a.jmp(WRITE_CONT)

    return a.link()





