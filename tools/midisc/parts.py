"""midisc — Octatrack 1.40C MIDI scenes OS patch."""
from __future__ import annotations

from ot3_asm import Asm

from .memory_map import *  # noqa: F403
def build_pack() -> bytes:
    """MSC -> working sparse, then durable like stock Part Save + Reload.

    working->shadow->PART_STAGING, then shadow->PART_PROJECT (Reload half)
    so edits after Part Paste refresh Project Save CF source. No faf0/fbb4.
    Unsaved edits never survived reboot; Part Save did. SAVE's durable work is
    memcpy working→shadow→100ab196 and set 9b312 — not just sparse bytes.
    Keep asterisk (dirty() still marks project). LAST==0xFF → rts.
    """
    a = Asm()
    a.mvz_b_abs(LAST_PART, 3)
    a.cmpi(0xFF, 3)
    a.beq("skip")
    a.push("d0", "d1", "d2", "d3", "d4", "d5", "a0", "a1")
    a.hex("2f0a2f0b")  # push a2, a3
    a.andi(0xF, 3)
    a.move_l_dd(3, 4)  # d4 = part
    a.move_l_dd(3, 0)
    a.move_l_imm(0x18B2, 1)
    a.muls(0, 1)
    a.move_l_dd(1, 5)  # d5 = part*0x18b2
    a.movea_abs(BANK_PTR, 0)
    a.adda_d(1, 0)
    a.adda_imm(SPARSE_OFF, 0)
    a.hex("2248")  # a1 = working sparse
    a.hex("2f09")  # push sparse base (count must land at header+2)
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
    a.hex("225f")  # pop sparse base → a1
    a.hex("13430002")  # count @ header+2

    # Full STOCK_SAVE durable half (working→shadow→staging + 9b312).
    # Sparse-only dual-write was not enough on HW; Part Save does this.
    a.movea_abs(BANK_PTR, 0)
    a.hex("2008")  # d0 = bank
    a.add_dd(5, 0)  # bank+part*18b2
    a.move_l_dd(0, 2)
    a.addi(0x9504A, 2)  # d2 = shadow base
    a.move_l_dd(0, 1)
    a.addi(0x8ED80, 1)  # d1 = working base
    a.movea_imm(MEMCPY, 3)
    a.hex("487818b2")
    a.hex("2f01")
    a.hex("2f02")
    a.hex("4e93")
    a.hex("4fef000c")
    a.hex("487818b2")
    a.hex("2f02")  # src shadow
    a.move_l_imm(PART_STAGING, 0)
    a.add_dd(5, 0)
    a.hex("2f00")  # dst staging
    a.hex("4e93")
    a.hex("4fef000c")
    # Stock Reload second half: shadow -> PART_PROJECT (Project Save CF source)
    a.hex("487818b2")
    a.hex("2f02")  # src shadow
    a.move_l_imm(PART_PROJECT, 0)
    a.add_dd(5, 0)
    a.hex("2f00")  # dst PART_PROJECT
    a.hex("4e93")
    a.hex("4fef000c")
    a.movea_abs(BANK_PTR, 0)
    a.adda_imm(PART_SAVED, 0)
    a.adda_d(4, 0)
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
    a.andi(0xF, 3)
    a.moveq(0xFF, 0)
    a.move_b_d_abs(0, UNPACK_SRC)
    a.label("try")
    a.move_l_dd(3, 0)
    a.move_l_imm(0x18B2, 1)
    a.muls(0, 1)
    a.movea_abs(BANK_PTR, 0)
    a.adda_d(1, 0)
    a.adda_d(2, 0)
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
    a.move_l_dd(3, 0)
    a.move_l_imm(0x18B2, 1)
    a.muls(0, 1)
    a.movea_abs(BANK_PTR, 0)
    a.adda_d(1, 0)
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



def build_reload_after() -> bytes:
    """After stock RELOAD: restore Part-Save CKPT if MS magic present, else shadow.

    Edits pack into shadow, so stock shadow->working alone cannot undo midisc.
    Part Save snapshots working sparse -> CKPT; on hit, CKPT -> working, unpack,
    then pack so shadow/staging/PART_PROJECT match the saved MSC again.
    Part index from stack (reload arg), not PART_DISP.
    """
    a = Asm()
    a.hex("2f00")  # push d0 — stock success/fail; part at 4(sp)
    a.push("d1", "d2", "d3", "a0", "a1")
    # 1*4 + 5*4 = 24; part was @4 -> @0x18
    a.move_l_sp(0x18, 3)
    a.andi(0xF, 3)
    a.move_l_dd(3, 0)
    a.move_l_imm(SPARSE_BYTES, 1)
    a.muls(0, 1)
    a.movea_imm(CKPT, 0)
    a.adda_d(1, 0)  # a0 = CKPT[part]
    a.hex("3010")  # move.w (a0), d0
    a.cmpi(SPARSE_MAGIC, 0)
    a.bne("use_shadow")
    a.hex("2f08")  # push a0 (CKPT src)
    a.move_l_dd(3, 0)
    a.move_l_imm(0x18B2, 1)
    a.muls(0, 1)
    a.movea_abs(BANK_PTR, 0)
    a.adda_d(1, 0)
    a.adda_imm(SPARSE_OFF, 0)
    a.hex("2248")  # a1 = working dest
    a.hex("205f")  # pop a0 = CKPT src
    a.move_l_imm(SPARSE_BYTES, 2)
    a.label("ck_to_w")
    a.hex("1018")
    a.hex("12c0")
    a.hex("5382")
    a.bne("ck_to_w")
    a.move_l_dd(3, 0)
    a.move_b_d_abs(0, UNPACK_SRC)
    a.bra("do_unp")
    a.label("use_shadow")
    a.moveq(0xFE, 0)
    a.move_b_d_abs(0, UNPACK_SRC)
    a.label("do_unp")
    a.pop("a1", "a0", "d3", "d2", "d1")
    a.jsr(SENT_UNPACK)
    # Republish durable from restored MSC (shadow was dirty from edit-time pack)
    a.jsr(SENT_PACK)
    a.jsr(PRESS_UI)
    a.hex("201f")  # pop d0
    a.movea_abs(APPLY_RET, 0)
    a.hex("4ed0")
    return a.link()


def build_bank_switch() -> bytes:
    """d0=new BANK_PTR. Pack, publish, unpack. Site A only (0x400622aa).

    Guarded path: BANK_ID still old; pack while old bank is current, then
    publish. Part1 after-faf0 unpack is build_after_project_load. Preserve
    d1-d7/a0-a6 (sample load).
    """
    a = Asm()
    a.hex("4fefffc4")  # lea -0x3c(sp),sp  ; 15 regs
    a.hex("48d77ffe")  # movem.l d1-d7/a0-a6,(sp)
    a.hex("2f00")  # push d0
    a.jsr(SENT_PACK)
    a.hex("201f")  # pop d0
    a.move_l_d_abs(0, BANK_PTR)
    a.jsr(SENT_UNPACK)
    a.hex("4cd77ffe")  # movem.l (sp),d1-d7/a0-a6
    a.hex("4fef003c")  # lea 0x3c(sp),sp
    a.rts()
    return a.link()


def build_bank_publish() -> bytes:
    """d0=new BANK_PTR. Publish, then unpack ONLY IF THE BANK CHANGED.

    Site B (0x40087d44): BANK_ID already published. Pack here = Bam emu bug
    (durable SAVE mid bank-load → wrong pattern). Publish + unpack only.
    Octakit: kits keep part layout/offsets; midisc DRAM stays at CLIP/CKPT
    (0x460C9A00+) — never 0x47fc7410..0x47fd910f boot temp.

    Guard (Bam, 12 Sep 2026): stock's other site, 0x400622aa, is wrapped in
    a cmpl/beqs that skips unless BANK_PTR actually changes; this site is
    stock's unconditional clamp-and-set path and fires during PROJECT LOAD
    with the part index still at the default bank. unpack's shadow→working
    sync then lands 144 bytes in the wrong bank's part record -- harmless
    only when the saved bank IS the default, which is "bank 1 reloads
    clean, every other bank corrupts". Mirror stock's own guard: keep the
    store (stock semantics), skip it and the unpack when old == new. The port
    bisected the symptom to this one site; the guard itself is untested
    there -- a save on bank 3 + reload is the test.
    """
    a = Asm()
    a.hex("4fefffc4")  # lea -0x3c(sp),sp
    a.hex("48d77ffe")  # movem.l d1-d7/a0-a6,(sp)
    a.hex(f"b0b9{BANK_PTR:08x}")  # cmp.l (BANK_PTR).l,d0 -- old vs new
    a.hex("670c")  # beq.s same: unchanged, so the store is a no-op too
    a.move_l_d_abs(0, BANK_PTR)  # publish (the store stock made here)
    a.jsr(SENT_UNPACK)
    a.label("same")
    a.hex("4cd77ffe")
    a.hex("4fef003c")
    a.rts()
    return a.link()


def build_after_project_load(cont: int = 0x400418E0) -> bytes:
    """After faf0: seed CKPT from PART_PROJECT sparse, unpack, jmp cont.

    Project CF lands in PART_PROJECT/staging; DRAM CKPT does not. Seeding CKPT
    makes Part Reload restore project-saved midisc without a re-Part-Save.
    Do NOT merely wipe CKPT — edits pack into shadow, so Reload would look like
    autosave (MS1 regression). Preserves d2. Lives in PROJECT_CAVE after clear.
    """
    a = Asm()
    a.push("d0", "d1", "d2", "d3", "a0", "a1")
    a.hex("2f0a")  # push a2
    a.movea_imm(MEMCPY, 2)
    a.moveq(0, 3)
    a.label("lp")
    a.move_l_dd(3, 0)
    a.move_l_imm(0x18B2, 1)
    a.muls(0, 1)
    a.movea_imm(PART_PROJECT, 1)
    a.adda_d(1, 1)
    a.adda_imm(0x17A2, 1)  # src = PP sparse
    a.move_l_dd(3, 0)
    a.move_l_imm(SPARSE_BYTES, 1)
    a.muls(0, 1)
    a.movea_imm(CKPT, 0)
    a.adda_d(1, 0)  # dst = CKPT[part]
    a.hex("48780090")  # pea 144
    a.hex("2f09")  # src
    a.hex("2f08")  # dst
    a.hex("4e92")  # jsr (a2) MEMCPY
    a.hex("4fef000c")
    a.addq(1, 3)
    a.cmpi(4, 3)
    a.bcs("lp")
    a.hex("245f")  # pop a2
    a.pop("a1", "a0", "d3", "d2", "d1", "d0")
    a.jsr(SENT_UNPACK)
    a.jmp(cont)
    return a.link()



def build_bank_invalidate() -> bytes:
    """d0=new BANK_PTR. Publish, clear CKPTs. Preserve d1-d7/a0-a6 (sample load)."""
    a = Asm()
    a.hex("4fefffc4")  # lea -0x3c(sp),sp
    a.hex("48d77ffe")  # movem.l d1-d7/a0-a6,(sp)
    a.move_l_d_abs(0, BANK_PTR)
    a.moveq(0xFF, 1)
    a.move_b_d_abs(1, LAST_PART)
    # wipe CKPT magics so Reload won't restore DRAM garbage after bank load
    a.movea_imm(CKPT, 0)
    a.moveq(3, 2)
    a.label("zck")
    a.hex("4250")  # clr.w (a0)
    a.adda_imm(SPARSE_BYTES, 0)
    a.hex("5382")  # subq.l #1, d2
    a.bpl("zck")
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
    """jmp-target: pack old MSC, run stock apply, rts -> after_abs."""
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


def build_save_ui() -> bytes:
    """Pack live MSC / salvage durable sparse, snapshot CKPT, jmp stock SAVE.

    SAVE_ALL calls this for parts 0..3. Non-current parts must not let empty
    working wipe a good shadow — salvage shadow->working when working lacks MS.
    Pack only when arg==PART_DISP (MSC is that part). Always copy working sparse
    -> CKPT[part] so Part Reload can restore midisc after later edits (edits pack
    into shadow; CKPT is the Part-Save freeze).
    """
    a = Asm()
    a.push("d0", "d1", "d2", "a0", "a1")
    # 5*4=20 + ret@20; part was @4 -> @0x18
    a.move_l_sp(0x18, 0)
    a.andi(0xF, 0)
    a.move_l_dd(0, 2)  # d2 = part

    # salvage: working sparse invalid but shadow has MS -> copy 144B
    a.move_l_dd(2, 0)
    a.move_l_imm(0x18B2, 1)
    a.muls(0, 1)
    a.movea_abs(BANK_PTR, 0)
    a.adda_d(1, 0)
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

    # working sparse -> CKPT[part] (Part Reload freeze)
    a.label("ckpt")
    a.move_l_dd(2, 0)
    a.move_l_imm(0x18B2, 1)
    a.muls(0, 1)
    a.movea_abs(BANK_PTR, 0)
    a.adda_d(1, 0)
    a.adda_imm(SPARSE_OFF, 0)
    a.hex("2248")  # a1 = working sparse
    a.move_l_dd(2, 0)
    a.move_l_imm(SPARSE_BYTES, 1)
    a.muls(0, 1)
    a.movea_imm(CKPT, 0)
    a.adda_d(1, 0)  # a0 = CKPT[part]
    a.move_l_imm(SPARSE_BYTES, 1)
    a.label("cp_ck")
    a.hex("1019")  # move.b (a1)+, d0
    a.hex("10c0")  # move.b d0, (a0)+
    a.hex("5381")
    a.bne("cp_ck")

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
    """Part Clear: wipe working + PART_PROJECT + CKPT sparse, jmp stock Clear.

    Stock Clear→SAVE copies working→shadow→staging, so those two follow working.
    PART_PROJECT is Project Save CF source and is not updated by stock SAVE — zero
    it here. Shared z144 helper (bsr). Never CLEAR_CAVE.
    """
    a = Asm()
    a.push("d0", "d1", "d2", "a0", "a1")
    a.move_l_sp(0x18, 0)
    a.andi(0xF, 0)
    a.move_l_dd(0, 2)
    a.move_l_imm(0x18B2, 1)
    a.muls(0, 1)
    a.movea_abs(BANK_PTR, 0)
    a.adda_d(1, 0)
    a.adda_imm(SPARSE_OFF, 0)
    a._fix.append((len(a.b), "z144"))
    a.hex("61000000")
    a.movea_imm(PART_PROJECT, 0)
    a.adda_d(1, 0)
    a.adda_imm(0x17A2, 0)
    a._fix.append((len(a.b), "z144"))
    a.hex("61000000")
    a.move_l_dd(2, 0)
    a.move_l_imm(SPARSE_BYTES, 1)
    a.muls(0, 1)
    a.movea_imm(CKPT, 0)
    a.adda_d(1, 0)
    a._fix.append((len(a.b), "z144"))
    a.hex("61000000")
    a.move_l_dd(2, 0)
    a.mvz_b_abs(LAST_PART, 1)
    a.andi(0xF, 1)
    a.hex("b081")
    a.beq("wipe")
    a.mvz_b_abs(PART_DISP, 1)
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

