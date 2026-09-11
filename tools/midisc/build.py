"""midisc — Octatrack 1.40C MIDI scenes OS patch."""
from __future__ import annotations

import struct
import subprocess
import sys

from .memory_map import *  # noqa: F403
from .util import ensure_stock, fix_jsr, jmp_abs, jsr_abs, off
from .parts import (
    build_after_apply, build_apply_wrap, build_bank_invalidate,
    build_after_project_load, build_bank_publish, build_bank_switch, build_clear_part, build_dirty, build_pack,
    build_reload_after, build_reload_ui, build_save_ui, build_unpack,
)
from .hold import (
    build_addi_d0, build_addi_d1, build_dial, build_enc_press_hook,
    build_enc_unlock, build_hold_store, build_press_refresh,
    build_scene_lock_clamp,
)
from .scene_ui import (
    build_clear_scene, build_copy_scene, build_pad_has_locks,
    build_paste_scene, build_release_mix,
)
from .morph import (
    build_morph, build_rebuild_lock_mask, build_scene_after_plock,
    build_scene_applied, build_voice_reload_d2, build_write_remixed, build_xf_after, build_xf_mix_out,
)

def main() -> None:
    stock = ensure_stock()
    img = bytearray(stock)

    for site, want in (
        (GATE_A, GATE_A_STOCK),
        (GATE_B, GATE_B_STOCK),
        (DISP, DISP_STOCK),
        (WRITE_HOOK, WRITE_STOCK),
        (DIAL_HOOK, DIAL_STOCK),
        (TRACK_GATE, GATE_TST_STOCK),
        (PAGE_GATE, GATE_TST_STOCK),
        (TRACK_ADDI, TRACK_ADDI_STOCK),
        (PAGE_ADDI, PAGE_ADDI_STOCK),
        (PAD_HOOK, PAD_HOOK_STOCK),
        (PRESS_HOOK, PRESS_HOOK_STOCK),
        (RELEASE_HOOK, RELEASE_HOOK_STOCK),
        (GREY_ENTER, GREY_ENTER_STOCK),
        (LED_SKIP_B, LED_SKIP_B_STOCK),
        (LED_ADDI_A, TRACK_ADDI_STOCK),
        (LED_ADDI_B, TRACK_ADDI_STOCK),
        (GREY_CELL, GREY_CELL_STOCK),
        (RECALL_A, RECALL_STOCK),
        (RECALL_B, RECALL_STOCK),
        (SCENE_DONE_A, SCENE_DONE_STOCK),
        (SCENE_DONE_B, SCENE_DONE_STOCK),
        (MORPH_EXIT, MORPH_EXIT_STOCK),
        (XF_AFTER1, XF_AFTER1_STOCK),
        (XF_AFTER2, XF_AFTER2_STOCK),
        (PLOCK_DONE, PLOCK_DONE_STOCK),
        (UI_CLEAR_SCENE, "4eb940038c30"),
        (UI_COPY_SCENE, "4eb9400274cc"),
        (UI_PASTE_SCENE, "4eb940027578"),
        (UI_CLEAR_PART, "4eb94004a9d0"),
        (APPLY_BNE_SAVE, APPLY_BNE_STOCK),
        (APPLY_BNE_CLEAR, APPLY_BNE_STOCK),
        (SAVE_UI, "4eb94004a908"),
        (RELOAD_UI, "4eb94004aab4"),
        (RELOAD_UI_B, "4eb94004aab4"),
        (STOCK_APPLY, "4fefff9848d77cfc"),
        (BANK_WR_SWITCH_A, BANK_WR_STOCK),
        (BANK_WR_SWITCH_B, BANK_WR_STOCK),
        (BANK_WR_INIT_A, BANK_WR_STOCK),
        (BANK_WR_INIT_B, BANK_WR_STOCK),
        (AFTER_PROJECT_LOAD, AFTER_PROJECT_LOAD_STOCK),
    ):
        got = bytes(img[off(site) : off(site) + len(want) // 2]).hex()
        if got != want:
            sys.exit(f"{site:#x}: want {want}, got {got}")

    if bytes(img[off(XF_PUB1) : off(XF_PUB1) + 6]).hex() != XF_JSR_STOCK:
        sys.exit("XF_PUB1 not stock")
    if bytes(img[off(XF_PUB2) : off(XF_PUB2) + 6]).hex() != XF_JSR_STOCK:
        sys.exit("XF_PUB2 not stock")
    if any(img[off(CODE2) : off(0x400D7C30)]):
        sys.exit("cave not empty")
    if any(img[off(SAFE_CAVE) : off(SAFE_CAVE_END)]):
        sys.exit("safe cave not empty")
    # Clear unused FF pad D7C3C..D7C4F (vector table starts D7C50)
    img[off(0x400D7C3C) : off(0x400D7C50)] = bytes(0x400D7C50 - 0x400D7C3C)

    pack_b = build_pack()
    unpack_b = build_unpack()
    dirty_b = build_dirty()
    clear_pt_b = build_clear_part()
    save_b = build_save_ui()
    reload_after_b = build_reload_after()
    xf_mix_b = build_xf_mix_out()

    # PROJECT_CAVE: clear_part + after_project_load (NOT xf2 — that hangs boot).
    if any(img[off(PROJECT_CAVE) : off(PROJECT_CAVE_END)]):
        sys.exit("PROJECT_CAVE not empty")
    after_proj_b = bytearray(build_after_project_load(AFTER_PROJECT_LOAD_CONT))
    need_proj = len(clear_pt_b) + len(after_proj_b)
    if need_proj > PROJECT_CAVE_END - PROJECT_CAVE:
        sys.exit(f"PROJECT_CAVE overrun {need_proj}")
    abs_clr_pt = PROJECT_CAVE
    abs_after_proj = PROJECT_CAVE + len(clear_pt_b)
    print(
        f"PROJECT_CAVE clear {len(clear_pt_b)} @ {abs_clr_pt:#x} "
        f"after_proj {len(after_proj_b)} @ {abs_after_proj:#x}"
    )

    # SAFE_CAVE: dirty + clamp + pack + unpack + save + reload_after + xf_mix + xf2 + plock
    sc = bytearray()
    abs_dirty = SAFE_CAVE + len(sc)
    sc += dirty_b
    abs_clamp = SAFE_CAVE + len(sc)
    sc += build_scene_lock_clamp()
    abs_pack = SAFE_CAVE + len(sc)
    sc += pack_b
    abs_unpack = SAFE_CAVE + len(sc)
    sc += unpack_b
    abs_save = SAFE_CAVE + len(sc)
    sc += save_b
    abs_reload_after = SAFE_CAVE + len(sc)
    sc += reload_after_b
    abs_xf_mix = SAFE_CAVE + len(sc)
    sc += xf_mix_b
    abs_xf2 = SAFE_CAVE + len(sc)
    sc += build_xf_after(XF_AFTER2_CONT, XF_AFTER2_STOCK)
    abs_plock = SAFE_CAVE + len(sc)
    sc += build_scene_after_plock()
    if SAFE_CAVE + len(sc) > SAFE_CAVE_END:
        sys.exit(f"SAFE_CAVE overrun {len(sc)} (need xf2 in SAFE; do not move to PROJECT)")
    if not (SAFE_CAVE <= abs_xf2 < SAFE_CAVE_END):
        sys.exit(f"xf2 must live in SAFE_CAVE, got {abs_xf2:#x}")
    print(f"SAFE_CAVE {len(sc)} @ {SAFE_CAVE:#x} free {SAFE_CAVE_END - SAFE_CAVE - len(sc)}")
    print(f"  dirty={abs_dirty:#x} clamp={abs_clamp:#x} pack={abs_pack:#x} unpack={abs_unpack:#x}")
    print(f"  save={abs_save:#x} rel_after={abs_reload_after:#x} xf_mix={abs_xf_mix:#x}")
    print(f"  xf2={abs_xf2:#x} plock={abs_plock:#x}")

    c2b = bytearray()
    abs_rebuild = CAVE2 + len(c2b)
    c2b += build_rebuild_lock_mask()
    if CAVE2 + len(c2b) > CAVE2_END:
        sys.exit(f"CAVE2 overrun {len(c2b)}")
    if any(img[off(CAVE2) : off(CAVE2_END)]):
        sys.exit("CAVE2 not empty")
    print(f"CAVE2 {len(c2b)} @ {CAVE2:#x} rebuild={abs_rebuild:#x}")
    if fix_jsr(after_proj_b, SENT_UNPACK, abs_unpack) != 1:
        sys.exit("after_project_load unpack sentinel")

    voice_rel_b = bytearray(build_voice_reload_d2())
    if any(img[off(VOICE_RELOAD_CAVE) : off(VOICE_RELOAD_CAVE_END)]):
        sys.exit("VOICE_RELOAD_CAVE not empty")
    if len(voice_rel_b) > VOICE_RELOAD_CAVE_END - VOICE_RELOAD_CAVE:
        sys.exit(f"VOICE_RELOAD_CAVE overrun {len(voice_rel_b)}")
    abs_voice_rel = VOICE_RELOAD_CAVE
    print(f"VOICE_RELOAD {len(voice_rel_b)} @ {abs_voice_rel:#x}")

    # CODE2: apply/reload-ui/bank + scene-done/write remix
    after_b = build_after_apply()
    bank_sw_b = build_bank_switch()
    bank_inv_b = build_bank_invalidate()
    c2 = bytearray()
    abs_after = CODE2 + len(c2)
    c2 += after_b
    abs_apply = CODE2 + len(c2)
    c2 += build_apply_wrap(abs_after)
    abs_reload = CODE2 + len(c2)
    c2 += build_reload_ui(abs_reload_after)
    abs_bank_sw = CODE2 + len(c2)
    c2 += bank_sw_b
    abs_bank_inv = CODE2 + len(c2)
    c2 += bank_inv_b
    abs_scene_done = CODE2 + len(c2)
    c2 += build_scene_applied()
    abs_write_mix = CODE2 + len(c2)
    c2 += build_write_remixed()

    if len(c2) > CODE2_END - CODE2:
        sys.exit(f"CODE2 overrun {len(c2)}")

    print(f"CODE2 {len(c2)} free {CODE2_END - CODE2 - len(c2)}")
    print(f"  after={abs_after:#x} apply={abs_apply:#x} reload={abs_reload:#x}")
    print(f"  bank_sw={abs_bank_sw:#x} bank_inv={abs_bank_inv:#x}")
    print(f"  scene_done={abs_scene_done:#x} write_mix={abs_write_mix:#x}")

    core = {
        "xf1": build_xf_after(XF_AFTER1_CONT, XF_AFTER1_STOCK),
        "hold_a": build_hold_store("a"),
        "hold_b": build_hold_store("b"),
        "dial": build_dial(),
        "taddi": build_addi_d0(),
        "paddi": build_addi_d1(),
        "pad": build_pad_has_locks(),
        "press": build_press_refresh(),
        "release": build_release_mix(),
    }
    life = {
        "pst_sc": build_paste_scene(CLIP),
        "clr_sc": build_clear_scene(),
        "cpy_sc": build_copy_scene(CLIP),
    }
    pieces = {**core, **life}
    blob = bytearray()
    addrs: dict[str, int] = {}
    for name, piece in pieces.items():
        addrs[name] = STUB + len(blob)
        blob += piece
    abs_morph = STUB + len(blob)
    blob += build_morph()
    addrs["morph"] = abs_morph
    # Bam Site B: publish+unpack only (no pack) — fits STUB free
    abs_bank_pub = STUB + len(blob)
    bank_pub_b = bytearray(build_bank_publish())
    blob += bank_pub_b
    addrs["plock"] = abs_plock
    addrs["pack"] = abs_pack
    addrs["unpack"] = abs_unpack
    addrs["rebuild"] = abs_rebuild
    abs_xf1 = addrs["xf1"]
    if STUB + len(blob) > STUB_END:
        sys.exit(f"stub overrun {STUB + len(blob):#x} > {STUB_END:#x} ({len(blob)} bytes)")

    print(f"stub {len(blob)} free {STUB_END - STUB - len(blob)}")
    print(f"  bank_pub={abs_bank_pub:#x} ({len(bank_pub_b)}B Bam Site B)")
    if SENT_PACK.to_bytes(4, "big") in bank_pub_b:
        sys.exit("bank_pub must not call pack")

    n_pack = fix_jsr(blob, SENT_PACK, addrs["pack"])
    n_clamp = fix_jsr(blob, SENT_CLAMP, abs_clamp)
    if n_clamp < 2:
        sys.exit(f"stub clamp sentinels {n_clamp}")
    n_unp = fix_jsr(blob, SENT_UNPACK, addrs["unpack"])
    n_dirt = fix_jsr(blob, SENT_DIRTY, abs_dirty)
    if n_unp < 2:
        sys.exit(f"stub unpack sentinels {n_unp} (need morph+bank_pub)")
    n_rel_mix = fix_jsr(blob, SENT_XF_MIX, abs_xf_mix)
    n_rb_stub = fix_jsr(blob, SENT_REBUILD_MASK, addrs["rebuild"])
    # rebuild only from plock (SAFE); stubs must not call it (H-safe scene/hold)
    if n_rb_stub != 0:
        sys.exit(f"stub must not call rebuild ({n_rb_stub})")
    if n_pack == 0 or n_unp == 0:
        sys.exit(f"sentinel miss pack={n_pack} unpack={n_unp}")
    if n_dirt == 0:
        sys.exit("no dirty sentinel in stub")
    if n_rel_mix < 3:
        sys.exit(f"stub xf_mix sentinel count {n_rel_mix} (holdx2+clear; paste no mix)")

    n2 = fix_jsr(c2, SENT_PACK, addrs["pack"])
    n2 += fix_jsr(c2, SENT_UNPACK, addrs["unpack"])
    n2 += fix_jsr(c2, SENT_XF_MIX, abs_xf_mix)
    n2 += fix_jsr(c2, SENT_REBUILD_MASK, addrs["rebuild"])  # expect 0
    if fix_jsr(c2, SENT_VOICE_RELOAD, abs_voice_rel) != 1:
        sys.exit("CODE2 missing voice_reload")
    if n2 < 2:
        sys.exit(f"CODE2 sentinel miss ({n2})")

    # pack/unpack/morph/xf live in SAFE_CAVE
    fix_jsr(sc, SENT_PACK, addrs["pack"])
    n_sc_unp = fix_jsr(sc, SENT_UNPACK, addrs["unpack"])
    n_sc_mix = fix_jsr(sc, SENT_XF_MIX, abs_xf_mix)
    n_sc_dirt = fix_jsr(sc, SENT_DIRTY, abs_dirty)
    n_sc_rb = fix_jsr(sc, SENT_REBUILD_MASK, addrs["rebuild"])
    if n_sc_unp < 1:
        sys.exit(f"SAFE_CAVE unpack sentinels {n_sc_unp}")
    # xf2 lives in SAFE_CAVE (M5 boot layout)
    if n_sc_rb != 0:
        sys.exit(f"SAFE_CAVE rebuild sentinels {n_sc_rb} (need 0; plock must not rebuild)")

    # morph is in SAFE_CAVE; unpack sentinel fixed via n_sc_unp

    img[off(SAFE_CAVE) : off(SAFE_CAVE) + len(sc)] = bytes(sc)
    img[off(PROJECT_CAVE) : off(PROJECT_CAVE) + len(clear_pt_b)] = bytes(clear_pt_b)
    img[off(abs_after_proj) : off(abs_after_proj) + len(after_proj_b)] = bytes(after_proj_b)
    img[off(VOICE_RELOAD_CAVE) : off(VOICE_RELOAD_CAVE) + len(voice_rel_b)] = bytes(voice_rel_b)
    unlock_b = build_enc_unlock()
    abs_unlock = ENC_UNLOCK_CAVE
    hook_a_b = build_enc_press_hook(ENC_PRESS_A_CONT, ENC_PRESS_A_BAIL, abs_unlock)
    abs_hook_a = ENC_UNLOCK_CAVE + len(unlock_b)
    hook_b_b = build_enc_press_hook(ENC_PRESS_B_CONT, ENC_PRESS_B_BAIL, abs_unlock)
    abs_hook_b = abs_hook_a + len(hook_a_b)
    enc_blob = bytearray(unlock_b + hook_a_b + hook_b_b)
    if ENC_UNLOCK_CAVE + len(enc_blob) > ENC_UNLOCK_CAVE_END:
        sys.exit(f"ENC_UNLOCK_CAVE overrun {len(enc_blob)}")
    if any(img[off(ENC_UNLOCK_CAVE) : off(ENC_UNLOCK_CAVE) + len(enc_blob)]):
        sys.exit("ENC_UNLOCK_CAVE not empty")
    n_eu = fix_jsr(enc_blob, SENT_PACK, abs_pack)
    n_eu += fix_jsr(enc_blob, SENT_DIRTY, abs_dirty)
    n_eu += fix_jsr(enc_blob, SENT_XF_MIX, abs_xf_mix)
    n_eu += fix_jsr(enc_blob, SENT_UNPACK, abs_unpack)
    if n_eu < 4:
        sys.exit(f"enc_unlock sentinel fixups {n_eu}")
    img[off(ENC_UNLOCK_CAVE) : off(ENC_UNLOCK_CAVE) + len(enc_blob)] = bytes(enc_blob)
    print(f"  enc_unlock={abs_unlock:#x} hooks={abs_hook_a:#x}/{abs_hook_b:#x} ({len(enc_blob)}B)")
    img[off(CAVE2) : off(CAVE2) + len(c2b)] = bytes(c2b)
    img[off(CODE2) : off(CODE2) + len(c2)] = bytes(c2)
    img[off(MSC) : off(MSC) + MSC_LEN] = b"\xff" * MSC_LEN
    img[off(STUB) : off(STUB) + len(blob)] = bytes(blob)
    img[off(LAST_PART)] = 0xFF
    img[off(UNPACK_SRC)] = 0xFF
    img[off(LAST_BANK)] = 0xFF
    struct.pack_into(">I", img, off(APPLY_RET), 0)

    img[off(GATE_A) : off(GATE_A) + GATE_A_LEN] = jmp_abs(addrs["hold_a"]) + b"\x4e\x71\x4e\x71"
    img[off(GATE_B) : off(GATE_B) + GATE_B_LEN] = jmp_abs(addrs["hold_b"]) + b"\x4e\x71\x4e\x71"
    img[off(DIAL_HOOK) : off(DIAL_HOOK) + DIAL_LEN] = jmp_abs(addrs["dial"])
    img[off(TRACK_GATE) : off(TRACK_GATE) + 6] = jmp_abs(TRACK_AUDIO)
    img[off(PAGE_GATE) : off(PAGE_GATE) + 6] = jmp_abs(PAGE_AUDIO)
    img[off(TRACK_ADDI) : off(TRACK_ADDI) + 6] = jsr_abs(addrs["taddi"])
    img[off(PAGE_ADDI) : off(PAGE_ADDI) + 6] = jsr_abs(addrs["paddi"])
    # MIDI A/B lock LEDs: fall into audio scan + MSC addi (solid green on lock hit)
    img[off(GREY_ENTER) : off(GREY_ENTER) + len(GREY_ENTER_NOP) // 2] = bytes.fromhex(GREY_ENTER_NOP)
    img[off(LED_SKIP_B) : off(LED_SKIP_B) + len(LED_SKIP_B_NOP) // 2] = bytes.fromhex(LED_SKIP_B_NOP)
    img[off(LED_ADDI_A) : off(LED_ADDI_A) + 6] = jsr_abs(addrs["taddi"])
    img[off(LED_ADDI_B) : off(LED_ADDI_B) + 6] = jsr_abs(addrs["taddi"])
    img[off(PAD_HOOK) : off(PAD_HOOK) + PAD_HOOK_LEN] = jmp_abs(addrs["pad"]) + b"\x4e\x71"
    img[off(PRESS_HOOK) : off(PRESS_HOOK) + PRESS_HOOK_LEN] = jmp_abs(addrs["press"])
    img[off(RELEASE_HOOK) : off(RELEASE_HOOK) + RELEASE_HOOK_LEN] = jmp_abs(addrs["release"])

    img[off(UI_CLEAR_SCENE) : off(UI_CLEAR_SCENE) + 6] = jsr_abs(addrs["clr_sc"])
    img[off(UI_COPY_SCENE) : off(UI_COPY_SCENE) + 6] = jsr_abs(addrs["cpy_sc"])
    img[off(UI_PASTE_SCENE) : off(UI_PASTE_SCENE) + 6] = jsr_abs(addrs["pst_sc"])
    img[off(UI_CLEAR_PART) : off(UI_CLEAR_PART) + 6] = jsr_abs(abs_clr_pt)
    # Never apply_part after Part Save / Part Clear (instant clear; no MSC churn)
    if bytes(img[off(APPLY_BNE_SAVE) : off(APPLY_BNE_SAVE) + 2]).hex() != APPLY_BNE_STOCK:
        sys.exit("APPLY_BNE_SAVE stock mismatch")
    if bytes(img[off(APPLY_BNE_CLEAR) : off(APPLY_BNE_CLEAR) + 2]).hex() != APPLY_BNE_STOCK:
        sys.exit("APPLY_BNE_CLEAR stock mismatch")
    img[off(APPLY_BNE_SAVE) : off(APPLY_BNE_SAVE) + 2] = bytes.fromhex(APPLY_BNE_SKIP)
    img[off(APPLY_BNE_CLEAR) : off(APPLY_BNE_CLEAR) + 2] = bytes.fromhex(APPLY_BNE_SKIP)

    # Scene+encoder press: MIDI unlock instead of stock bail
    if not bytes(img[off(ENC_PRESS_A) : off(ENC_PRESS_A) + 6]).hex().startswith("4ab980000012"):
        sys.exit("ENC_PRESS_A stock mismatch")
    if not bytes(img[off(ENC_PRESS_B) : off(ENC_PRESS_B) + 6]).hex().startswith("4ab980000012"):
        sys.exit("ENC_PRESS_B stock mismatch")
    img[off(ENC_PRESS_A) : off(ENC_PRESS_A) + 10] = jmp_abs(abs_hook_a) + b"\x4e\x71\x4e\x71"
    img[off(ENC_PRESS_B) : off(ENC_PRESS_B) + 10] = jmp_abs(abs_hook_b) + b"\x4e\x71\x4e\x71"
    img[off(MORPH_EXIT) : off(MORPH_EXIT) + 6] = jmp_abs(abs_morph)
    img[off(XF_AFTER1) : off(XF_AFTER1) + 6] = jmp_abs(abs_xf1)
    img[off(XF_AFTER2) : off(XF_AFTER2) + 6] = jmp_abs(abs_xf2)
    img[off(SCENE_DONE_A) : off(SCENE_DONE_A) + 6] = jmp_abs(abs_scene_done)
    img[off(SCENE_DONE_B) : off(SCENE_DONE_B) + 6] = jmp_abs(abs_scene_done)
    img[off(WRITE_HOOK) : off(WRITE_HOOK) + WRITE_LEN] = jmp_abs(abs_write_mix) + b"\x4e\x71"
    img[off(PLOCK_DONE) : off(PLOCK_DONE) + PLOCK_DONE_LEN] = jmp_abs(addrs["plock"]) + b"\x4e\x71\x4e\x71"

    img[off(STOCK_APPLY) : off(STOCK_APPLY) + 8] = jmp_abs(abs_apply) + b"\x4e\x71"
    img[off(SAVE_UI) : off(SAVE_UI) + 6] = jsr_abs(abs_save)
    img[off(RELOAD_UI) : off(RELOAD_UI) + 6] = jsr_abs(abs_reload)
    img[off(RELOAD_UI_B) : off(RELOAD_UI_B) + 6] = jsr_abs(abs_reload)

    img[off(BANK_WR_SWITCH_A) : off(BANK_WR_SWITCH_A) + 6] = jsr_abs(abs_bank_sw)
    img[off(BANK_WR_SWITCH_B) : off(BANK_WR_SWITCH_B) + 6] = jsr_abs(abs_bank_pub)
    img[off(BANK_WR_INIT_A) : off(BANK_WR_INIT_A) + 6] = jsr_abs(abs_bank_inv)
    img[off(BANK_WR_INIT_B) : off(BANK_WR_INIT_B) + 6] = jsr_abs(abs_bank_inv)
    img[off(AFTER_PROJECT_LOAD) : off(AFTER_PROJECT_LOAD) + 6] = jsr_abs(abs_after_proj)

    save_all_lea = bytes.fromhex("45f94004a908")
    if bytes(img[off(SAVE_ALL) + 4 : off(SAVE_ALL) + 10]) != save_all_lea:
        sys.exit(f"SAVE_ALL lea mismatch: {bytes(img[off(SAVE_ALL)+4:off(SAVE_ALL)+10]).hex()}")
    img[off(SAVE_ALL) + 4 : off(SAVE_ALL) + 10] = bytes.fromhex("45f9") + abs_save.to_bytes(4, "big")

    spans = [
        (off(MSC), off(MSC) + MSC_LEN),
        (off(CODE2), off(CODE2) + len(c2)),
        (off(STUB), off(STUB) + len(blob)),
        (off(SAFE_CAVE), off(SAFE_CAVE) + len(sc)),
        (off(PROJECT_CAVE), off(PROJECT_CAVE) + len(clear_pt_b) + len(after_proj_b)),
        (off(VOICE_RELOAD_CAVE), off(VOICE_RELOAD_CAVE) + len(voice_rel_b)),
        (off(CAVE2), off(CAVE2) + len(c2b)),
        (off(0x400D7C3C), off(0x400D7C50)),
        (off(LAST_PART), off(APPLY_RET) + 4),
        (off(GATE_A), off(GATE_A) + GATE_A_LEN),
        (off(GATE_B), off(GATE_B) + GATE_B_LEN),
        (off(DIAL_HOOK), off(DIAL_HOOK) + DIAL_LEN),
        (off(TRACK_GATE), off(TRACK_GATE) + 6),
        (off(PAGE_GATE), off(PAGE_GATE) + 6),
        (off(TRACK_ADDI), off(TRACK_ADDI) + 6),
        (off(PAGE_ADDI), off(PAGE_ADDI) + 6),
        (off(GREY_ENTER), off(GREY_ENTER) + len(GREY_ENTER_NOP) // 2),
        (off(LED_SKIP_B), off(LED_SKIP_B) + len(LED_SKIP_B_NOP) // 2),
        (off(LED_ADDI_A), off(LED_ADDI_A) + 6),
        (off(LED_ADDI_B), off(LED_ADDI_B) + 6),
        (off(PAD_HOOK), off(PAD_HOOK) + PAD_HOOK_LEN),
        (off(PRESS_HOOK), off(PRESS_HOOK) + PRESS_HOOK_LEN),
        (off(RELEASE_HOOK), off(RELEASE_HOOK) + RELEASE_HOOK_LEN),
        (off(UI_CLEAR_SCENE), off(UI_CLEAR_SCENE) + 6),
        (off(UI_COPY_SCENE), off(UI_COPY_SCENE) + 6),
        (off(UI_PASTE_SCENE), off(UI_PASTE_SCENE) + 6),
        (off(UI_CLEAR_PART), off(UI_CLEAR_PART) + 6),
        (off(APPLY_BNE_SAVE), off(APPLY_BNE_SAVE) + 2),
        (off(APPLY_BNE_CLEAR), off(APPLY_BNE_CLEAR) + 2),
        (off(ENC_UNLOCK_CAVE), off(ENC_UNLOCK_CAVE) + len(enc_blob)),
        (off(ENC_PRESS_A), off(ENC_PRESS_A) + 10),
        (off(ENC_PRESS_B), off(ENC_PRESS_B) + 10),
        (off(MORPH_EXIT), off(MORPH_EXIT) + 6),
        (off(XF_AFTER1), off(XF_AFTER1) + 6),
        (off(XF_AFTER2), off(XF_AFTER2) + 6),
        (off(SCENE_DONE_A), off(SCENE_DONE_A) + 6),
        (off(SCENE_DONE_B), off(SCENE_DONE_B) + 6),
        (off(WRITE_HOOK), off(WRITE_HOOK) + WRITE_LEN),
        (off(PLOCK_DONE), off(PLOCK_DONE) + PLOCK_DONE_LEN),
        (off(STOCK_APPLY), off(STOCK_APPLY) + 8),
        (off(SAVE_UI), off(SAVE_UI) + 6),
        (off(RELOAD_UI), off(RELOAD_UI) + 6),
        (off(RELOAD_UI_B), off(RELOAD_UI_B) + 6),
        (off(BANK_WR_SWITCH_A), off(BANK_WR_SWITCH_A) + 6),
        (off(BANK_WR_SWITCH_B), off(BANK_WR_SWITCH_B) + 6),
        (off(BANK_WR_INIT_A), off(BANK_WR_INIT_A) + 6),
        (off(BANK_WR_INIT_B), off(BANK_WR_INIT_B) + 6),
        (off(AFTER_PROJECT_LOAD), off(AFTER_PROJECT_LOAD) + 6),
        (off(SAVE_ALL) + 4, off(SAVE_ALL) + 10),
    ]
    stray = [
        i for i, (x, y) in enumerate(zip(stock, img)) if x != y and not any(lo <= i < hi for lo, hi in spans)
    ]
    if stray:
        sys.exit(f"stray {[hex(BASE + i) for i in stray[:8]]}")

    for site, want in (
        (DISP, DISP_STOCK),
        (RECALL_A, RECALL_STOCK),
        (RECALL_B, RECALL_STOCK),
        (GREY_CELL, GREY_CELL_STOCK),
    ):
        if bytes(img[off(site) : off(site) + len(want) // 2]).hex() != want:
            sys.exit(f"{site:#x} must stay stock")
    if bytes(img[off(GREY_ENTER) : off(GREY_ENTER) + len(GREY_ENTER_NOP) // 2]).hex() != GREY_ENTER_NOP:
        sys.exit("GREY_ENTER must nop MIDI lock-LED skip")
    if bytes(img[off(LED_SKIP_B) : off(LED_SKIP_B) + len(LED_SKIP_B_NOP) // 2]).hex() != LED_SKIP_B_NOP:
        sys.exit("LED_SKIP_B must nop MIDI lock-LED skip")
    if bytes(img[off(LED_ADDI_A) : off(LED_ADDI_A) + 6]) != jsr_abs(addrs["taddi"]):
        sys.exit("LED_ADDI_A must jsr taddi")
    if bytes(img[off(LED_ADDI_B) : off(LED_ADDI_B) + 6]) != jsr_abs(addrs["taddi"]):
        sys.exit("LED_ADDI_B must jsr taddi")
    if bytes(img[off(TRACK_ADDI) : off(TRACK_ADDI) + 6]) != jsr_abs(addrs["taddi"]):
        sys.exit("TRACK_ADDI must jsr taddi")
    if bytes(img[off(WRITE_HOOK) : off(WRITE_HOOK) + 6]) != jmp_abs(abs_write_mix):
        sys.exit("WRITE_HOOK must jmp write_remixed")
    if WRITE_LEN != 8 or WRITE_CONT != 0x40055392:
        sys.exit("WRITE_HOOK must cover full move.l #0x18b2 (cont 55392)")
    if SENT_VOICE_RELOAD.to_bytes(4, "big") in c2:
        sys.exit("voice_reload sentinel unresolved")
    if bytes(img[off(SCENE_DONE_A) : off(SCENE_DONE_A) + 6]) != jmp_abs(abs_scene_done):
        sys.exit("SCENE_DONE_A must jmp scene_applied")
    if bytes(img[off(SCENE_DONE_B) : off(SCENE_DONE_B) + 6]) != jmp_abs(abs_scene_done):
        sys.exit("SCENE_DONE_B must jmp scene_applied")
    if bytes(img[off(RELEASE_HOOK) : off(RELEASE_HOOK) + 6]) != jmp_abs(addrs["release"]):
        sys.exit("RELEASE_HOOK must jmp release_mix")
    if bytes(img[off(PLOCK_DONE) : off(PLOCK_DONE) + 6]) != jmp_abs(addrs["plock"]):
        sys.exit("PLOCK_DONE must jmp scene_after_plock")

    if bytes(img[off(MORPH_EXIT) : off(MORPH_EXIT) + 6]) != jmp_abs(abs_morph):
        sys.exit("MORPH_EXIT must jmp morph")
    if bytes(img[off(XF_AFTER1) : off(XF_AFTER1) + 6]) != jmp_abs(abs_xf1):
        sys.exit("XF_AFTER1 must jmp xf1")
    if bytes(img[off(XF_AFTER2) : off(XF_AFTER2) + 6]) != jmp_abs(abs_xf2):
        sys.exit("XF_AFTER2 must jmp xf2")
    if bytes(img[off(AFTER_PROJECT_LOAD) : off(AFTER_PROJECT_LOAD) + 6]) != jsr_abs(abs_after_proj):
        sys.exit("AFTER_PROJECT_LOAD must jsr after_proj")
    if bytes(img[off(BANK_WR_SWITCH_A) : off(BANK_WR_SWITCH_A) + 6]) != jsr_abs(abs_bank_sw):
        sys.exit("BANK_WR_SWITCH_A must jsr bank_switch")
    if bytes(img[off(BANK_WR_SWITCH_B) : off(BANK_WR_SWITCH_B) + 6]) != jsr_abs(abs_bank_pub):
        sys.exit("BANK_WR_SWITCH_B must jsr bank_publish (Bam: no pack)")
    if bytes(img[off(0x400622b2) : off(0x400622b8)]) != bytes.fromhex("4eb94000faf0"):
        sys.exit("stock jsr faf0 must stay intact")
    if bytes(img[off(XF_PUB1) : off(XF_PUB1) + 6]).hex() != XF_JSR_STOCK:
        sys.exit("XF_PUB1 must stay stock")
    if bytes(img[off(XF_PUB2) : off(XF_PUB2) + 6]).hex() != XF_JSR_STOCK:
        sys.exit("XF_PUB2 must stay stock")

    if img[off(STOCK_CLEAR_PART) : off(STOCK_CLEAR_PART) + 0x20] != stock[
        off(STOCK_CLEAR_PART) : off(STOCK_CLEAR_PART) + 0x20
    ]:
        sys.exit("STOCK_CLEAR_PART body must stay stock")

    from _dis_ot3 import Dis

    dis = Dis(bytes(img))
    for region, size in (
        (STUB, len(blob)),
        (CODE2, len(c2)),
        (SAFE_CAVE, len(sc)),
        (PROJECT_CAVE, len(clear_pt_b) + len(after_proj_b)),
        (VOICE_RELOAD_CAVE, len(voice_rel_b)),
        (CAVE2, len(c2b)),
    ):
        a = region
        end = region + size
        while a < end:
            txt, n = dis.one(a)
            if n <= 0 or any(k in txt for k in (".word", "dc.w", ".byte", "???")):
                sys.exit(f"bad {a:#x}: {txt}")
            a += n

    cave = bytes(blob) + bytes(c2) + bytes(sc) + bytes(c2b)
    hold = pieces["hold_a"] + pieces["hold_b"]
    if bytes.fromhex("40055008") in hold or bytes.fromhex("40055008") in cave:
        sys.exit("must not contain 55008")
    if b"\x4e\xb9\x40\x04\xd9\x48" in hold:
        sys.exit("hold must not nested-jsr 4d948")
    if b"\x4e\xb9\x40\x04\xd9\x48" not in pieces["press"]:
        sys.exit("press stub must jsr 4d948")
    if bytes.fromhex("401087e4") in cave or bytes.fromhex("4010cdd1") in cave:
        sys.exit("must not reference unsafe 1.22 caves")
    if bytes.fromhex("80000002") in cave:
        sys.exit("must not use 80000002 as part index (use 100b14cf)")
    # Morph: sinks + CC; 8f162 only as behind READ (no store to UI).
    # H listen via VOICE; behind READ; never SOUND (sticky unlockeds) / never LFO.
    if bytes.fromhex(f"{MIDI_SOUND:08x}") in xf_mix_b:
        sys.exit("xf_mix must NOT write MIDI_SOUND (aliases unlocked; sticky reboot)")
    if bytes.fromhex(f"{MIDI_VOICE:08x}") not in xf_mix_b:
        sys.exit("xf_mix must write MIDI_VOICE")
    if bytes.fromhex(f"{MIDI_BEHIND:08x}") not in xf_mix_b:
        sys.exit("xf_mix must read 8f162 as behind")
    if bytes.fromhex(f"{LFO_BASE:08x}") in xf_mix_b:
        sys.exit("xf_mix must not write LFO_BASE (Y plock owns trigxscene)")
    live_adda = bytes.fromhex(f"d1fc{MIDI_BEHIND:08x}")
    i = 0
    while True:
        j = xf_mix_b.find(live_adda, i)
        if j < 0:
            break
        nxt = xf_mix_b[j + 6 : j + 8]
        if nxt and nxt[0] == 0x10:
            sys.exit("xf_mix must not store into 8f162")
        i = j + 1

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_bytes(bytes(img))
    r = subprocess.run(
        [
            sys.executable,
            str(ROOT / "tools" / "repack_140fx.py"),
            "-m",
            str(OUT),
            "--bin",
            str(DESKTOP),
            "-V",
            VER,  # splash <=10 (1.40MDISC2)
            "-o",
            str(ROOT / "out" / f"OCTATRACK_{DESKTOP.stem}.syx"),
        ],
        cwd=str(ROOT),
    )
    if r.returncode:
        sys.exit("repack failed")

    print(f"Flash: {DESKTOP} ({VER})")
    print(f"  SAFE_CAVE={SAFE_CAVE:#x} CAVE2={CAVE2:#x} xf_mix={abs_xf_mix:#x} morph={abs_morph:#x}")
    print(f"  CLIP={CLIP:#x}; CODE2={CODE2:#x}")
    print(f"  stubs {[f'{k}={v:#x}' for k, v in addrs.items()]}")


if __name__ == "__main__":
    main()
