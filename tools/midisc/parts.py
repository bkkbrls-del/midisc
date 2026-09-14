"""midisc — Octatrack 1.40C MIDI scenes OS patch."""
from __future__ import annotations

from ot3_asm import Asm

from .memory_map import *  # noqa: F403


def build_part_window() -> bytes:
    """Octakit seam: part/kit index → part-window base in the active store.

    IN:  d3 = part or kit index (any width)
    OUT: d3 = index & 0xFF (kits 0..255; stock banks still use low nibble)
         d1 = index * 0x18B2
         a0 = *BANK_PTR + d1
    Clobber: d0

    Lock store (144B sparse) = a0 + SPARSE_OFF. Octakit overrides this routine
    to use her kit payload base instead of BANK_PTR; offsets stay identical.
    """
    a = Asm()
    a.andi(0xFF, 3)
    a.move_l_dd(3, 0)
    a.move_l_imm(0x18B2, 1)
    a.muls(0, 1)
    a.movea_abs(BANK_PTR, 0)
    a.adda_d(1, 0)
    a.rts()
    return a.link()


def build_pack() -> bytes:
    """MSC → working sparse, then working → shadow → PART_PROJECT + PART_SAVED.

    Shadow write = reboot persistence without Project Save (MIDISCN1 proven).
    Never write PART_STAGING — STOCK_SAVE stores the Part-Save freeze there;
    Reload restores from staging. LAST==0xFF → rts.
    """
    a = Asm()
    a.mvz_b_abs(LAST_PART, 3)
    a.cmpi(0xFF, 3)
    a.beq("skip")
    a.push("d0", "d1", "d2", "d3", "d4", "d5", "a0", "a1")
    a.hex("2f0a2f0b")  # push a2, a3
    a.jsr(SENT_PART_WINDOW)
    a.move_l_dd(3, 4)
    a.move_l_dd(1, 5)
    a.adda_imm(SPARSE_OFF, 0)
    a.hex("2248")
    a.hex("2f09")
    a.move_l_imm(SPARSE_MAGIC, 0)
    a.hex("3280")
    a.hex("42290002")
    a.hex("41e90004")
    a.movea_imm(MSC, 2)
    a.move_l_imm(4096, 2)
    a.moveq(0, 3)
    a.label("pk_loop")
    a.hex("719a")
    a.cmpi(0xFF, 0)
    a.beq("pk_next")
    a.cmpi(SPARSE_MAX, 3)
    a.beq("pk_done")
    a.move_l_imm(4096, 1)
    a.sub_dd(2, 1)
    a.hex("30c1")
    a.hex("10c0")
    a.addq(1, 3)
    a.label("pk_next")
    a.hex("5382")
    a.bne("pk_loop")
    a.label("pk_done")
    a.hex("225f")
    a.hex("13430002")

    a.movea_abs(BANK_PTR, 0)
    a.hex("2008")
    a.add_dd(5, 0)
    a.move_l_dd(0, 2)
    a.addi(0x9504A, 2)  # shadow
    a.move_l_dd(0, 1)
    a.addi(0x8ED80, 1)  # working
    a.movea_imm(MEMCPY, 3)
    a.hex("487818b2")
    a.hex("2f01")
    a.hex("2f02")
    a.hex("4e93")
    a.hex("4fef000c")
    a.hex("487818b2")
    a.hex("2f02")  # src shadow
    a.move_l_imm(PART_PROJECT, 0)
    a.add_dd(5, 0)
    a.hex("2f00")
    a.hex("4e93")
    a.hex("4fef000c")
    a.movea_abs(BANK_PTR, 0)
    a.adda_imm(PART_SAVED, 0)
    a.move_l_dd(4, 1)
    a.andi(3, 1)
    a.adda_d(1, 0)
    a.moveq(1, 1)
    a.hex("1081")

    a.hex("265f245f")
    a.pop("a1", "a0", "d5", "d4", "d3", "d2", "d1", "d0")
    a.label("skip")
    a.rts()
    return a.link()


def build_unpack() -> bytes:
    """sparse -> MSC. Try working; if no MS magic, try SAVE-shadow.

    M5 shape (SAFE-fit): hit and miss both set LAST=part (no bit7 empty-settled).
    Shadow hit syncs 144B shadow->working. No count==0 scan.
    """
    a = Asm()
    a.push("d0", "d1", "d2", "d3", "d4", "a0", "a1")
    a.movea_imm(MSC, 0)
    a.move_l_imm(4096, 1)
    a.label("uf")
    a.hex("10bc00ff")
    a.hex("5288")
    a.hex("5381")
    a.bne("uf")
    a.move_l_imm(SPARSE_OFF, 2)
    a.mvz_b_abs(UNPACK_SRC, 3)
    a.moveq(0, 4)
    a.cmpi(0xFE, 3)
    a.bne("not_sh")
    a.move_l_imm(SHADOW_SPARSE_OFF, 2)
    a.mvz_b_abs(PART_DISP, 3)
    a.moveq(1, 4)
    a.bra("got")
    a.label("not_sh")
    a.cmpi(0xFF, 3)
    a.bne("got")
    a.mvz_b_abs(PART_DISP, 3)
    a.label("got")
    a.moveq(0xFF, 0)
    a.move_b_d_abs(0, UNPACK_SRC)
    a.label("try")
    a.jsr(SENT_PART_WINDOW)  # a0=window, d1=stride, d3&=0xFF
    a.adda_d(2, 0)  # + working or shadow sparse off
    a.hex("2248")
    a.hex("3011")
    a.cmpi(SPARSE_MAGIC, 0)
    a.beq("load")
    a.cmpi(SPARSE_OFF, 2)
    a.bne("hit")  # M5: miss shares hit epilogue
    a.move_l_imm(SHADOW_SPARSE_OFF, 2)
    a.moveq(1, 4)
    a.bra("try")
    a.label("load")
    a.mvz_b_disp(2, 1, 2)
    a.andi(0xFF, 2)
    a.beq("maybe_sync")
    a.hex("41e90004")
    a.label("uloop")
    a.hex("3018")
    a.hex("1218")
    a.movea_imm(MSC, 1)
    a.adda_d(0, 1)
    a.hex("1281")
    a.hex("5382")
    a.bne("uloop")
    a.label("maybe_sync")
    a.tst_d(4)
    a.beq("hit")
    a.jsr(SENT_PART_WINDOW)
    a.hex("2248")
    a.adda_imm(SHADOW_SPARSE_OFF, 0)
    a.adda_imm(SPARSE_OFF, 1)
    a.move_l_imm(SPARSE_BYTES, 2)
    a.label("cp_sp")
    a.hex("1018")
    a.hex("12c0")
    a.hex("5382")
    a.bne("cp_sp")
    a.label("hit")
    a.move_l_dd(3, 0)
    a.move_b_d_abs(0, LAST_PART)
    a.pop("a1", "a0", "d4", "d3", "d2", "d1", "d0")
    a.rts()
    return a.link()



def build_freeze_alt_to_working() -> bytes:
    """d3=part. Promote Part-Save freeze twin → working sparse if 'MS'.

    save_ui parks freeze at FREEZE_SPARSE_OFF; pack only touches SPARSE_OFF, so
    the twin survives edit packs + reboot (stock RELOAD copies shadow→working).
    """
    a = Asm()
    a.push("d0", "d1", "a0", "a1")
    a.move_l_dd(3, 0)
    a.andi(0xF, 0)
    a.jsr(SENT_PART_WINDOW)
    a.hex("2248")  # a1 = window
    a.adda_imm(FREEZE_SPARSE_OFF, 0)
    a.hex("3010")
    a.cmpi(SPARSE_MAGIC, 0)
    a.bne("try_sh")
    a.adda_imm(SPARSE_OFF, 1)
    a.move_l_imm(SPARSE_BYTES, 1)
    a.label("cp_w")
    a.hex("1018")
    a.hex("12c0")
    a.hex("5381")
    a.bne("cp_w")
    a.bra("done")
    a.label("try_sh")
    a.move_l_dd(3, 0)
    a.jsr(SENT_PART_WINDOW)
    a.hex("2248")
    a.adda_imm(SHADOW_FREEZE_SPARSE_OFF, 0)
    a.hex("3010")
    a.cmpi(SPARSE_MAGIC, 0)
    a.bne("done")
    a.adda_imm(SPARSE_OFF, 1)
    a.move_l_imm(SPARSE_BYTES, 1)
    a.label("cp_s")
    a.hex("1018")
    a.hex("12c0")
    a.hex("5381")
    a.bne("cp_s")
    a.label("done")
    a.pop("a1", "a0", "d1", "d0")
    a.rts()
    return a.link()


def build_reload_after() -> bytes:
    """After stock RELOAD: restore Part-Save MIDI freeze, then remix.

    1) MSC_CKPT if magic (same session)
    2) else freeze-alt → working sparse → unpack (survives reboot)
    3) pack + force xf + invalidate
    """
    from .emit import emit_force_xf_mix, emit_invalidate_lock_masks

    a = Asm()
    a.hex("2f00")
    a.push("d1", "d2", "d3", "a0", "a1")
    a.hex("2f0a")
    a.move_l_sp(0x1C, 3)
    a.andi(0xF, 3)
    a.move_l_dd(3, 0)
    a.lsl(2, 0)
    a.movea_imm(MSC_CKPT_MAGIC, 0)
    a.adda_d(0, 0)
    a.hex("2010")
    a.cmpi(MSC_CKPT_MAGIC_VAL, 0)
    a.bne("no_msc")
    a.move_l_dd(3, 0)
    a.lsl(8, 0)
    a.lsl(4, 0)
    a.movea_imm(MSC_CKPT, 1)
    a.adda_d(0, 1)
    a.movea_imm(MSC, 0)
    a.movea_imm(MEMCPY, 2)
    a.hex("48781000")
    a.hex("2f09")
    a.hex("2f08")
    a.hex("4e92")
    a.hex("4fef000c")
    a.move_l_dd(3, 0)
    a.move_b_d_abs(0, LAST_PART)
    a.bra("ok")
    a.label("no_msc")
    a.jsr(SENT_SPARSE_CKPT)  # freeze-alt → working sparse
    a.move_l_dd(3, 0)
    a.move_b_d_abs(0, UNPACK_SRC)
    a.jsr(SENT_UNPACK)
    a.label("ok")
    a.jsr(SENT_PACK)
    emit_invalidate_lock_masks(a)
    emit_force_xf_mix(a)
    a.jsr(SENT_XF_MIX)
    a.hex("245f")
    a.pop("a1", "a0", "d3", "d2", "d1")
    a.hex("201f")
    a.movea_abs(APPLY_RET, 0)
    a.hex("4ed0")
    return a.link()


def build_bank_switch() -> bytes:
    """d0=new BANK_PTR. Pack, publish, unpack. Site A only (0x400622aa).

    When KITS_GATE!=0, skip pack/unpack — Octakit owns the part/kit set;
    bank change must not assume parts moved. Still publishes BANK_PTR.
    """
    a = Asm()
    a.hex("4fefffc4")  # lea -0x3c(sp),sp  ; 15 regs
    a.hex("48d77ffe")  # movem.l d1-d7/a0-a6,(sp)
    a.hex("2f00")  # push d0
    a.mvz_b_abs(KITS_GATE, 1)
    a.tst_d(1)
    a.bne("kits")
    a.jsr(SENT_PACK)
    a.hex("201f")  # pop d0
    a.move_l_d_abs(0, BANK_PTR)
    a.jsr(SENT_UNPACK)
    a.bra("done")
    a.label("kits")
    a.hex("201f")  # pop d0
    a.move_l_d_abs(0, BANK_PTR)
    a.label("done")
    a.hex("4cd77ffe")  # movem.l (sp),d1-d7/a0-a6
    a.hex("4fef003c")  # lea 0x3c(sp),sp
    a.rts()
    return a.link()


def build_bank_publish() -> bytes:
    """d0=new BANK_PTR. Publish then unpack. Never pack (Bam Site B).

    Site B (0x40087d44): BANK_ID already published. Pack here = Bam emu bug
    (durable SAVE mid bank-load → wrong pattern). Publish + unpack only.
    Octakit: kits keep part layout/offsets; midisc DRAM stays at CLIP/CKPT
    (0x460C9A00+) — never 0x47fc7410..0x47fd910f boot temp.
    """
    a = Asm()
    a.hex("4fefffc4")  # lea -0x3c(sp),sp
    a.hex("48d77ffe")  # movem.l d1-d7/a0-a6,(sp)
    a.move_l_d_abs(0, BANK_PTR)
    a.jsr(SENT_UNPACK)
    a.hex("4cd77ffe")
    a.hex("4fef003c")
    a.rts()
    return a.link()


def build_seed_msc_from_ckpt() -> bytes:
    """CKPT[0..3] with MS → unpack each → MSC_CKPT snapshot. For project load."""
    a = Asm()
    a.push("d0", "d1", "d2", "d3", "a0", "a1")
    a.hex("2f0a")
    a.movea_imm(MEMCPY, 2)
    a.moveq(0, 3)
    a.label("lp")
    a.move_l_dd(3, 0)
    a.move_l_imm(SPARSE_BYTES, 1)
    a.muls(0, 1)
    a.movea_imm(CKPT, 0)
    a.adda_d(1, 0)
    a.hex("3010")
    a.cmpi(SPARSE_MAGIC, 0)
    a.bne("next")
    a.hex("2f08")
    a.jsr(SENT_PART_WINDOW)
    a.adda_imm(SPARSE_OFF, 0)
    a.hex("2248")
    a.hex("205f")
    a.move_l_imm(SPARSE_BYTES, 1)
    a.label("cp")
    a.hex("1018")
    a.hex("12c0")
    a.hex("5381")
    a.bne("cp")
    a.move_l_dd(3, 0)
    a.move_b_d_abs(0, UNPACK_SRC)
    a.jsr(SENT_UNPACK)
    a.move_l_dd(3, 0)
    a.lsl(8, 0)
    a.lsl(4, 0)
    a.movea_imm(MSC_CKPT, 0)
    a.adda_d(0, 0)
    a.movea_imm(MSC, 1)
    a.hex("48781000")
    a.hex("2f09")
    a.hex("2f08")
    a.hex("4e92")
    a.hex("4fef000c")
    a.move_l_dd(3, 0)
    a.lsl(2, 0)
    a.movea_imm(MSC_CKPT_MAGIC, 0)
    a.adda_d(0, 0)
    a.move_l_imm(MSC_CKPT_MAGIC_VAL, 1)
    a.hex("2081")
    a.label("next")
    a.addq(1, 3)
    a.cmpi(4, 3)
    a.bcs("lp")
    a.hex("245f")
    a.pop("a1", "a0", "d3", "d2", "d1", "d0")
    a.rts()
    return a.link()


def build_after_project_load(cont: int = 0x400418E0) -> bytes:
    """After faf0: seed CKPT from PART_PROJECT, clear MSC magics, unpack.

    Do not touch PART_STAGING (Part-Save freeze) or bank working. Pack writes
    shadow for reboot edit persistence; staging stays STOCK_SAVE freeze.
    """
    a = Asm()
    a.push("d0", "d1", "d2", "d3", "a0", "a1")
    a.hex("2f0a")
    a.movea_imm(MSC_CKPT_MAGIC, 0)
    a.moveq(15, 1)
    a.label("zmk")
    a.hex("4290")
    a.adda_imm(4, 0)
    a.hex("5381")
    a.bpl("zmk")
    a.movea_imm(MEMCPY, 2)
    a.moveq(0, 3)
    a.label("lp")
    a.move_l_dd(3, 0)
    a.move_l_imm(0x18B2, 1)
    a.muls(0, 1)
    a.movea_imm(PART_PROJECT, 1)
    a.adda_d(1, 1)
    a.adda_imm(0x17A2, 1)
    a.move_l_dd(3, 0)
    a.move_l_imm(SPARSE_BYTES, 1)
    a.muls(0, 1)
    a.movea_imm(CKPT, 0)
    a.adda_d(1, 0)
    a.hex("48780090")
    a.hex("2f09")
    a.hex("2f08")
    a.hex("4e92")
    a.hex("4fef000c")
    a.addq(1, 3)
    a.cmpi(4, 3)
    a.bcs("lp")
    a.hex("245f")
    a.pop("a1", "a0", "d3", "d2", "d1", "d0")
    a.jsr(SENT_UNPACK)
    a.jmp(cont)
    return a.link()



def build_bank_invalidate() -> bytes:
    """d0=new BANK_PTR. Publish, clear CKPTs. Preserve d1-d7/a0-a6 (sample load).

    When KITS_GATE!=0, only publish BANK_PTR — do not clear LAST_PART/CKPT
    (kits are not tied to bank change).
    """
    a = Asm()
    a.hex("4fefffc4")  # lea -0x3c(sp),sp
    a.hex("48d77ffe")  # movem.l d1-d7/a0-a6,(sp)
    a.move_l_d_abs(0, BANK_PTR)
    a.mvz_b_abs(KITS_GATE, 1)
    a.tst_d(1)
    a.bne("done")
    a.moveq(0xFF, 1)
    a.move_b_d_abs(1, LAST_PART)
    # wipe CKPT magics + MSC_CKPT magics so Reload won't restore DRAM garbage
    a.movea_imm(CKPT, 0)
    a.move_l_imm(CKPT_SLOTS - 1, 2)
    a.label("zck")
    a.hex("4250")  # clr.w (a0)
    a.adda_imm(SPARSE_BYTES, 0)
    a.hex("5382")
    a.bpl("zck")
    a.movea_imm(MSC_CKPT_MAGIC, 0)
    a.move_l_imm(CKPT_SLOTS - 1, 2)
    a.label("zmk")
    a.hex("4290")  # clr.l (a0)
    a.adda_imm(4, 0)
    a.hex("5382")
    a.bpl("zmk")
    a.label("done")
    a.hex("4cd77ffe")  # movem.l (sp),d1-d7/a0-a6
    a.hex("4fef003c")  # lea 0x3c(sp),sp
    a.rts()
    return a.link()


def build_dirty() -> bytes:
    """Match stock scene-edit dirty: asterisk + bank flush flags.

    Asterisk alone (95048 / 100b145e) is not enough — without bank+0x9b332
    and 0x100f8598 the project never hits CF, so unsaved packs die on reboot.
    Part Paste survives because stock sets the full dirty set.
    """
    a = Asm()
    a.push("d0", "d2", "a0", "a1")
    a.hex("2279" + f"{BANK_PTR:08x}")  # a1 = bank
    a.hex("71b9" + f"{PART_DISP:08x}")  # mvz.b PART_DISP, d0
    a.hex("7401e1aa")  # moveq #1,d2; lsl.l d0,d2
    a.hex("207c00095048")  # movea.l #95048, a0
    a.hex("10318800808213808800")  # or into bank+95048
    a.hex("1039100b145e808213c0100b145e")  # or into 100b145e
    # bank flush (same as stock 4000eb20..eb2c)
    a.moveq(1, 0)
    a.movea_imm(BANK_DIRTY, 0)  # a0 = 9b332
    a.hex("23808800")  # move.l d0, (a1, a0.l)
    a.move_l_d_abs(0, UI_DIRTY)  # move.l d0, 100f8598
    a.pop("a1", "a0", "d2", "d0")
    a.rts()
    return a.link()


def build_apply_wrap(after_abs: int) -> bytes:
    """jmp-target: pack old MSC, run stock apply, rts -> after_abs.

    Kept for CODE2 layout; MIDISNd hooks UI jsr sites via build_apply_bridge
    instead so STOCK_APPLY stays stock (Octakit + project-load hang).
    """
    a = Asm()
    # Entry via jmp (not jsr). (sp) = caller return of apply_part.
    a.hex("2017")  # move.l (sp), d0
    a.move_l_d_abs(0, APPLY_RET)
    a.move_l_imm(after_abs, 0)
    a.hex("2e80")  # move.l d0, (sp) — redirect stock rts
    a.jsr(SENT_PACK)
    # Stock prologue (exact bytes from 0x40009094)
    a.hex("4fefff98")  # lea -0x68(sp), sp
    a.hex("48d77cfc")  # movem.l d2-d7/a2-a6, (sp)
    a.jmp(APPLY_CONT)
    return a.link()


def build_after_apply() -> bytes:
    a = Asm()
    # Part index apply_part published into GLOBAL (may lead PART_DISP)
    a.mvz_b_abs(0x80001829, 0)
    a.move_b_d_abs(0, UNPACK_SRC)
    a.jsr(SENT_UNPACK)
    a.movea_abs(APPLY_RET, 0)
    a.hex("4ed0")  # jmp (a0)
    return a.link()


def build_apply_bridge() -> bytes:
    """jsr-target replacing UI jsr STOCK_APPLY: pack → stock apply → unpack+mix.

    STOCK_APPLY head stays stock (project load + Octakit). Hook part-change UI
    sites only — safe to jsr xf_mix here (MIDISNg bricked when mix ran on boot
    paths). Cont matches reload feel: sync PART_DISP + PAT_ACTIVE (80000003)
    so MIDI does not wait for pattern start / first step, then unpack + xf_mix.
    """
    from .emit import emit_force_xf_mix, emit_invalidate_lock_masks

    a = Asm()
    # (sp)=UI ret, 4(sp)=arg1, 8(sp)=arg2
    a.jsr(SENT_PACK)
    a.hex("2017")  # d0 = UI return
    a.move_l_d_abs(0, APPLY_RET)
    a.move_l_imm(SENT_APPLY_BRIDGE_CONT, 0)
    a.hex("2e80")  # (sp) = cont; args remain at 4/8
    a.jmp(STOCK_APPLY)
    # cont — abs patched by build (offset 28 from start)
    a.mvz_b_abs(APPLY_PART, 0)
    a.move_b_d_abs(0, UNPACK_SRC)
    a.move_b_d_abs(0, PART_DISP)
    a.move_b_d_abs(0, 0x80000003)  # PAT_ACTIVE — don't wait for 62148
    a.jsr(SENT_UNPACK)
    emit_invalidate_lock_masks(a)
    emit_force_xf_mix(a)
    a.jsr(SENT_XF_MIX)
    a.movea_abs(APPLY_RET, 0)
    a.hex("4ed0")
    return a.link()


def build_save_ui() -> bytes:
    """Pack live MSC / salvage durable sparse, snapshot CKPT, jmp stock SAVE.

    SAVE_ALL calls this for parts 0..3. Non-current parts must not let empty
    working wipe a good shadow — salvage shadow->working when working lacks MS.
    Pack only when arg==PART_DISP (MSC is that part). Parks working sparse →
    FREEZE_SPARSE_OFF (reboot-durable Part-Save twin) and CKPT/MSC_CKPT (session).
    """
    a = Asm()
    a.push("d0", "d1", "d2", "a0", "a1")
    # 5*4=20 + ret@20; part was @4 -> @0x18
    a.move_l_sp(0x18, 3)
    a.andi(0xF, 3)  # must mask before PART_DISP cmp (MIDISCc forgot → skipped pack)
    a.move_l_dd(3, 2)  # d2 = part

    # salvage: working sparse invalid but shadow has MS -> copy 144B
    a.jsr(SENT_PART_WINDOW)  # a0=window
    a.hex("2248")  # a1 = part base
    a.adda_imm(SPARSE_OFF, 0)
    a.hex("3010")
    a.cmpi(SPARSE_MAGIC, 0)
    a.beq("ensured")
    a.hex("2049")  # a0 = part base
    a.adda_imm(SHADOW_SPARSE_OFF, 0)
    a.hex("3010")
    a.cmpi(SPARSE_MAGIC, 0)
    a.bne("ensured")
    a.adda_imm(SPARSE_OFF, 1)  # a1 = working sparse
    a.move_l_imm(SPARSE_BYTES, 1)
    a.label("cp_sp")
    a.hex("1018")
    a.hex("12c0")
    a.hex("5381")
    a.bne("cp_sp")

    a.label("ensured")
    a.move_l_dd(2, 0)
    a.mvz_b_abs(PART_DISP, 1)
    a.hex("b081")
    a.bne("ckpt")
    a.move_b_d_abs(0, LAST_PART)
    a.jsr(SENT_PACK)

    # working sparse -> CKPT[slot] (backup) + full MSC snapshot (source of truth)
    a.label("ckpt")
    a.move_l_dd(2, 3)
    a.jsr(SENT_PART_WINDOW)
    a.adda_imm(SPARSE_OFF, 0)
    a.hex("2248")  # a1 = working sparse
    a.move_l_dd(2, 0)
    a.andi(0xF, 0)  # CKPT slots 0..15
    a.move_l_dd(0, 3)  # d3 = slot
    a.move_l_imm(SPARSE_BYTES, 1)
    a.muls(0, 1)
    a.movea_imm(CKPT, 0)
    a.adda_d(1, 0)  # a0 = CKPT[slot]
    a.move_l_imm(SPARSE_BYTES, 1)
    a.label("cp_ck")
    a.hex("1019")  # move.b (a1)+, d0
    a.hex("10c0")  # move.b d0, (a0)+
    a.hex("5381")
    a.bne("cp_ck")

    # Full MSC freeze only for the displayed part (MSC is always that part).
    a.move_l_dd(2, 0)
    a.mvz_b_abs(PART_DISP, 1)
    a.hex("b081")
    a.bne("done")

    # MSC → MSC_CKPT[slot]; magic[slot] = MSCK
    a.hex("2f0a")  # push a2
    a.move_l_dd(3, 0)
    a.lsl(8, 0)
    a.lsl(4, 0)  # *4096
    a.movea_imm(MSC_CKPT, 0)
    a.adda_d(0, 0)  # dst
    a.movea_imm(MSC, 1)  # src
    a.movea_imm(MEMCPY, 2)
    a.hex("48781000")
    a.hex("2f09")
    a.hex("2f08")
    a.hex("4e92")
    a.hex("4fef000c")
    a.move_l_dd(3, 0)
    a.lsl(2, 0)
    a.movea_imm(MSC_CKPT_MAGIC, 0)
    a.adda_d(0, 0)
    a.move_l_imm(MSC_CKPT_MAGIC_VAL, 1)
    a.hex("2081")  # move.l d1, (a0)
    a.hex("245f")  # pop a2

    a.label("done")
    # Park Part-Save freeze twin (pack must not touch FREEZE_SPARSE_OFF).
    a.move_l_dd(2, 3)
    a.jsr(SENT_PART_WINDOW)
    a.hex("2248")  # a1 = window
    a.adda_imm(SPARSE_OFF, 1)  # a1 = working sparse
    a.hex("3011")
    a.cmpi(SPARSE_MAGIC, 0)
    a.bne("park_skip")
    a.adda_imm(FREEZE_SPARSE_OFF, 0)  # a0 = freeze alt
    a.move_l_imm(SPARSE_BYTES, 1)
    a.label("cp_fr")
    a.hex("1019")  # (a1)+ → d0
    a.hex("10c0")  # d0 → (a0)+
    a.hex("5381")
    a.bne("cp_fr")
    a.label("park_skip")
    a.pop("a1", "a0", "d2", "d1", "d0")
    a.jmp(STOCK_SAVE)
    return a.link()


def build_reload_ui(after_abs: int) -> bytes:
    """jmp stock RELOAD with rts redirected to unpack (keep part arg at 4(sp))."""
    a = Asm()
    # (sp)=UI return, 4(sp)=part. Do NOT jsr stock — that would skew args.
    a.hex("2017")  # move.l (sp), d0
    a.move_l_d_abs(0, APPLY_RET)  # reuse; apply/reload don't nest
    a.move_l_imm(after_abs, 0)
    a.hex("2e80")  # move.l d0, (sp)
    a.jmp(STOCK_RELOAD)
    return a.link()



def build_clear_part() -> bytes:
    """Part Clear: wipe working + PART_PROJECT sparse + MSC. Keep Part-Save freeze.

    Do NOT wipe CKPT / MSC_CKPT — Part Reload must still restore the last Part Save
    after clear / scene copy-paste-clear. Stock Clear→SAVE updates shadow from
    working (now empty of midisc). Shared z144 helper (bsr). Never CLEAR_CAVE.
    """
    a = Asm()
    a.push("d0", "d1", "d2", "a0", "a1")
    a.move_l_sp(0x18, 3)
    a.andi(0xF, 3)
    a.move_l_dd(3, 2)
    a.jsr(SENT_PART_WINDOW)  # a0=window, d1=stride
    a.hex("2f01")  # push stride
    a.adda_imm(SPARSE_OFF, 0)
    a._fix.append((len(a.b), "z144"))
    a.hex("61000000")
    a.hex("221f")  # pop stride → d1
    a.movea_imm(PART_PROJECT, 0)
    a.adda_d(1, 0)
    a.adda_imm(0x17A2, 0)
    a._fix.append((len(a.b), "z144"))
    a.hex("61000000")
    # NOTE: leave CKPT + MSC_CKPT intact (Part Reload freeze)
    a.move_l_dd(2, 0)
    a.andi(0xFF, 0)
    a.mvz_b_abs(LAST_PART, 1)
    a.andi(0xFF, 1)
    a.hex("b081")
    a.beq("wipe")
    a.mvz_b_abs(PART_DISP, 1)
    a.andi(0xFF, 1)
    a.hex("b081")
    a.bne("skip")
    a.label("wipe")
    a.movea_imm(MSC, 0)
    a.move_l_imm(4096, 1)
    a.label("ff")
    a.hex("10bc00ff")
    a.hex("5288")
    a.hex("5381")
    a.bne("ff")
    a.moveq(0xFF, 0)
    a.move_b_d_abs(0, LAST_PART)
    a.label("skip")
    a.pop("a1", "a0", "d2", "d1", "d0")
    a.jmp(STOCK_CLEAR_PART)
    a.label("z144")
    a.moveq(36, 0)
    a.label("z1")
    a.hex("4298")
    a.hex("5380")
    a.bne("z1")
    a.rts()
    return a.link()

