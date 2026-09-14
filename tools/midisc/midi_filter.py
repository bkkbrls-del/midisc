"""MIDI CONTROL: CC48/55/56 TX enable ticks (checked=ON default).

Live = packed byte @ FILT_CC48 (CLIP+0xC80), bits 0/1/2 = CC48/55/56
(0=ON/checked, 1=OFF). Same DRAM cell MIDISC8 used for CC48 long.

Project key MIDISC_CC_FILT; load/save in D-region pads only.

Safety:
- Gate entered with jmp only.
- Never 0x800000D4 / PERSONALIZE A8/D8/DC.
- Per-row getters (immediate btst) — no shared getters (9c scroll brick).
- Per-row setters (no shared bra.s body).
- Persist caves: 347E / 352D only — never ba8/table zero-gaps.
"""
from __future__ import annotations

import struct

from ot3_asm import Asm

from .memory_map import (
    FILT_BIT_CC48,
    FILT_BIT_CC55,
    FILT_BIT_CC56,
    FILT_CC48,
    FILT_PERSIST_LOAD_CAVE,
    FILT_PERSIST_LOAD_CAVE_END,
    FILT_PERSIST_SAVE_CAVE,
    FILT_PERSIST_SAVE_CAVE_END,
)
from .util import off

GLYPH_ON = 0x400B5E90
GLYPH_OFF = 0x400B5E8E

CTRL_LABELS = 0x400B29E0
CTRL_GETTERS = 0x400B29F0
CTRL_SETTERS = 0x400B2A00
STOCK_ROWS = 4
NEW_ROWS = 7
VIEWPORT = 4

CTRL_LIST = 0x460E4654

FILTER_CAVE = 0x400C4302
FILTER_CAVE_END = 0x400C444C

SCROLL_CAVE = 0x400D51F0
SCROLL_CAVE_END = 0x400D5222

CC_TX_HOOK = 0x40033E5A
CC_TX_HOOK_STOCK = "7008b0816644"
CC_TX_BNE_TGT = 0x40033EA4
CC_TX_EARLY = 0x40033F24

LIST_INIT_COUNT_PEA = 0x4006845C
LIST_INIT_VIEW_PEA = 0x40068460
DRAW_SCROLL_HOOK = 0x4006838A
DRAW_SCROLL_HOOK_STOCK = "4283367c001b"

SETTER_LEA_SITES = (0x400684A2, 0x40068570, 0x4006858A, 0x400685A4)

LOAD_CHAIN_PEA = 0x400877E0
LOAD_CHAIN_PEA_STOCK = "4879400b7cda"
LOAD_CHAIN_CONT = 0x400877E6
LOAD_DONE = 0x40088224
LOAD_PARSE_FAIL = 0x40086D3A
LOAD_NEXT_KEY = 0x400B7CDA

SAVE_CC_OUT_MVS = 0x400887E2
SAVE_CC_OUT_MVS_STOCK = "71398000004a"
SAVE_CC_OUT_CONT = 0x400887E8
SAVE_FAIL = 0x40089638

KEY_NAME = b"MIDISC_CC_FILT\0"
KEY_FMT = b"MIDISC_CC_FILT=%d\r\n\0"

# Entire CC48/55/56 MIDI CONTROL filter (menu + TX gate). Off = stock MIDI CONTROL.
ENABLE_MIDI_CTRL_FILTER = False

# Project load/save hooks brick Project Save (MIDISCN1.0). Do not re-enable
# until a non-settings-path persist design exists (see PERSIST_PLAN.md fallback B).
ENABLE_FILT_PROJECT_PERSIST = False

FILT_BITS = (FILT_BIT_CC48, FILT_BIT_CC55, FILT_BIT_CC56)


def _btst_dn(bit: int, dn: int) -> str:
    return f"{0x0800 + dn:04x}{bit:04x}"


def _checkbox_getter(bit: int) -> bytes:
    """bit clear → checked (ON). Immediate btst — scroll-safe."""
    return bytes.fromhex(
        f"203c{GLYPH_ON:08x}"
        f"1239{FILT_CC48:08x}"
        f"{_btst_dn(bit, 1)}"
        f"6706"
        f"203c{GLYPH_OFF:08x}"
        f"4e75"
    )


def _build_shared_setters() -> tuple[bytes, list[int]]:
    """Shared RMW body first, then three entry stubs (backward bra.s).

    HW-ok on MIDISC9 (only shared *getters* bricked scroll). Bit in d2.
    """
    body = bytearray()
    body += bytes.fromhex(f"1039{FILT_CC48:08x}")
    body += bytes.fromhex("2200")
    body += bytes.fromhex("e4a9")
    body += bytes.fromhex("028100000001")
    body += bytes.fromhex("d2af0004")
    body += bytes.fromhex("028100000001")
    body += bytes.fromhex("0580")
    body += bytes.fromhex("4a816702")
    body += bytes.fromhex("05c0")
    body += bytes.fromhex(f"13c0{FILT_CC48:08x}")
    body += bytes.fromhex("4e75")

    blob = bytearray(body)
    shared_off = 0
    entry_offs = []
    for bit in FILT_BITS:
        entry_offs.append(len(blob))
        blob += bytes.fromhex(f"74{bit:02x}")
        bra_at = len(blob)
        blob += bytes.fromhex("6000")
        disp = shared_off - (bra_at + 2)
        if not -128 <= disp <= 127:
            raise SystemExit(f"setter bra.s out of range {disp}")
        if disp == 0:
            raise SystemExit("setter bra.s +0 would spin")
        blob[bra_at + 1] = disp & 0xFF
    return bytes(blob), entry_offs


def build_cc_tx_gate() -> bytes:
    """jmp-entered; bit clear → pass (ON). Reads packed FILT_CC48."""
    p = FILT_CC48
    code = bytearray()
    labels: dict[str, int] = {}
    fixups: list[tuple[int, str]] = []

    def beq_s(name: str) -> None:
        code.extend(bytes.fromhex("6700"))
        fixups.append((len(code) - 1, name))

    def bra_s(name: str) -> None:
        code.extend(bytes.fromhex("6000"))
        fixups.append((len(code) - 1, name))

    def lab(name: str) -> None:
        labels[name] = len(code)

    code.extend(bytes.fromhex("0c8300000030"))
    beq_s("c48")
    code.extend(bytes.fromhex("0c8300000037"))
    beq_s("c55")
    code.extend(bytes.fromhex("0c8300000038"))
    beq_s("c56")
    lab("pass")
    code.extend(bytes.fromhex("7008b081"))
    beq_s("eq8")
    code.extend(bytes.fromhex(f"4ef9{CC_TX_BNE_TGT:08x}"))
    lab("eq8")
    code.extend(bytes.fromhex(f"4ef9{CC_TX_HOOK + 6:08x}"))
    lab("c48")
    code.extend(bytes.fromhex(f"1039{p:08x}{_btst_dn(0, 0)}"))
    beq_s("pass")
    bra_s("block")
    lab("c55")
    code.extend(bytes.fromhex(f"1039{p:08x}{_btst_dn(1, 0)}"))
    beq_s("pass")
    bra_s("block")
    lab("c56")
    code.extend(bytes.fromhex(f"1039{p:08x}{_btst_dn(2, 0)}"))
    beq_s("pass")
    lab("block")
    code.extend(bytes.fromhex(f"4ef9{CC_TX_EARLY:08x}"))

    for at, name in fixups:
        disp = labels[name] - (at + 1)
        if not -128 <= disp <= 127:
            raise SystemExit(f"gate short branch to {name} out of range ({disp})")
        code[at] = disp & 0xFF
    return bytes(code)


def ctrl_scroll_cave_bytes() -> bytes:
    last = VIEWPORT - 1
    return bytes.fromhex(
        f"41f9{CTRL_LIST:08x}"
        f"70{VIEWPORT:02x}"
        f"2140000c70"
        f"{NEW_ROWS:02x}"
        f"214000102028000872"
        f"{last:02x}"
        f"429021400004b2806c0890812080214100044283367c001b4e75"
    )


def build_filt_persist_load(key_addr: int) -> bytes:
    a = Asm()
    a.hex(f"4879{key_addr:08x}")
    a.hex("2f03")
    a.hex("4e93")
    a.hex("508f")
    a.tst_d(0)
    a.bne("miss")
    a.tst_d(2)
    a.beq("fail")
    a.hex("2f02")
    a.hex("4e94")
    a.hex("588f")
    a.hex("4aaf003a")
    a.bne("done")
    a.andi(7, 0)
    a.move_b_d_abs(0, FILT_CC48)
    a.label("done")
    a.jmp(LOAD_DONE)
    a.label("fail")
    a.jmp(LOAD_PARSE_FAIL)
    a.label("miss")
    a.hex(f"4879{LOAD_NEXT_KEY:08x}")
    a.jmp(LOAD_CHAIN_CONT)
    return a.link()


def build_filt_persist_save(fmt_addr: int) -> bytes:
    b = Asm()
    b.hex(f"7139{FILT_CC48:08x}")
    b.hex("2f00")
    b.hex(f"4879{fmt_addr:08x}")
    b.hex("2f02")
    b.hex("4e94")
    b.hex("2f02")
    b.hex("4e93")
    b.hex("2f00")
    b.hex("2f02")
    b.hex("2f03")
    b.hex("4e92")
    b.hex("4fef001c")
    b.tst_d(0)
    b.bmi("sfail")
    b.hex(f"7139{0x8000004A:08x}")
    b.jmp(SAVE_CC_OUT_CONT)
    b.label("sfail")
    b.jmp(SAVE_FAIL)
    return b.link()


def apply_midi_ctrl_filter(img: bytearray, gate_addr: int) -> None:
    if bytes(img[off(CC_TX_HOOK) : off(CC_TX_HOOK) + 6]).hex() != CC_TX_HOOK_STOCK:
        raise SystemExit(
            f"CC_TX_HOOK not stock: {bytes(img[off(CC_TX_HOOK):off(CC_TX_HOOK)+6]).hex()}"
        )
    if any(img[off(FILTER_CAVE) : off(FILTER_CAVE_END)]):
        raise SystemExit("FILTER_CAVE not empty")
    if any(img[off(SCROLL_CAVE) : off(SCROLL_CAVE_END)]):
        raise SystemExit("SCROLL_CAVE not empty")
    if bytes(img[off(DRAW_SCROLL_HOOK) : off(DRAW_SCROLL_HOOK) + 6]).hex() != DRAW_SCROLL_HOOK_STOCK:
        raise SystemExit(
            f"DRAW_SCROLL_HOOK not stock: {bytes(img[off(DRAW_SCROLL_HOOK):off(DRAW_SCROLL_HOOK)+6]).hex()}"
        )
    if bytes(img[off(LOAD_CHAIN_PEA) : off(LOAD_CHAIN_PEA) + 6]).hex() != LOAD_CHAIN_PEA_STOCK:
        raise SystemExit("LOAD_CHAIN_PEA not stock")
    if bytes(img[off(SAVE_CC_OUT_MVS) : off(SAVE_CC_OUT_MVS) + 6]).hex() != SAVE_CC_OUT_MVS_STOCK:
        raise SystemExit("SAVE_CC_OUT_MVS not stock")

    if ENABLE_FILT_PROJECT_PERSIST:
        if any(img[off(FILT_PERSIST_LOAD_CAVE) : off(FILT_PERSIST_LOAD_CAVE_END)]):
            raise SystemExit("FILT_PERSIST_LOAD_CAVE not empty")
        if any(img[off(FILT_PERSIST_SAVE_CAVE) : off(FILT_PERSIST_SAVE_CAVE_END)]):
            raise SystemExit("FILT_PERSIST_SAVE_CAVE not empty")

    img[off(CC_TX_HOOK) : off(CC_TX_HOOK) + 6] = bytes.fromhex(f"4ef9{gate_addr:08x}")

    stock_labels = [struct.unpack_from(">I", img, off(CTRL_LABELS) + i * 4)[0] for i in range(STOCK_ROWS)]
    stock_getters = [struct.unpack_from(">I", img, off(CTRL_GETTERS) + i * 4)[0] for i in range(STOCK_ROWS)]
    stock_setters = [struct.unpack_from(">I", img, off(CTRL_SETTERS) + i * 4)[0] for i in range(STOCK_ROWS)]

    base = FILTER_CAVE
    cave = bytearray()

    def here() -> int:
        return base + len(cave)

    s48 = here()
    cave += b"CC48\0"
    s55 = here()
    cave += b"CC55\0"
    s56 = here()
    cave += b"CC56\0"
    if len(cave) & 1:
        cave += b"\0"

    getters = []
    for bit in FILT_BITS:
        getters.append(here())
        cave += _checkbox_getter(bit)

    set_blob, set_offs = _build_shared_setters()
    set_base = here()
    cave += set_blob
    setters = [set_base + o for o in set_offs]

    while len(cave) & 3:
        cave += b"\0"

    labels_addr = here()
    for a in stock_labels + [s48, s55, s56]:
        cave += struct.pack(">I", a)
    getters_addr = here()
    for a in stock_getters + getters:
        cave += struct.pack(">I", a)
    setters_addr = here()
    for a in stock_setters + setters:
        cave += struct.pack(">I", a)

    load_addr = save_addr = 0
    persist_note = "project persist OFF"
    if ENABLE_FILT_PROJECT_PERSIST:
        key_addr = here()
        cave += KEY_NAME
        fmt_addr = here()
        cave += KEY_FMT
        while len(cave) & 1:
            cave += b"\0"

        load_blob = build_filt_persist_load(key_addr)
        save_blob = build_filt_persist_save(fmt_addr)
        if FILT_PERSIST_LOAD_CAVE + len(load_blob) > FILT_PERSIST_LOAD_CAVE_END:
            raise SystemExit(f"FILT_PERSIST_LOAD_CAVE overrun {len(load_blob)}")
        if FILT_PERSIST_SAVE_CAVE + len(save_blob) > FILT_PERSIST_SAVE_CAVE_END:
            raise SystemExit(f"FILT_PERSIST_SAVE_CAVE overrun {len(save_blob)}")

        load_addr = FILT_PERSIST_LOAD_CAVE
        save_addr = FILT_PERSIST_SAVE_CAVE
        img[off(load_addr) : off(load_addr) + len(load_blob)] = load_blob
        img[off(save_addr) : off(save_addr) + len(save_blob)] = save_blob
        img[off(LOAD_CHAIN_PEA) : off(LOAD_CHAIN_PEA) + 6] = bytes.fromhex(f"4ef9{load_addr:08x}")
        img[off(SAVE_CC_OUT_MVS) : off(SAVE_CC_OUT_MVS) + 6] = bytes.fromhex(f"4ef9{save_addr:08x}")
        persist_note = (
            f"load @ {load_addr:#x} ({len(load_blob)}B) "
            f"save @ {save_addr:#x} ({len(save_blob)}B)"
        )

    if base + len(cave) > FILTER_CAVE_END:
        raise SystemExit(f"FILTER_CAVE overrun {len(cave)}")

    scroll = ctrl_scroll_cave_bytes()
    if SCROLL_CAVE + len(scroll) > SCROLL_CAVE_END:
        raise SystemExit(f"SCROLL_CAVE overrun {len(scroll)}")

    img[off(FILTER_CAVE) : off(FILTER_CAVE) + len(cave)] = bytes(cave)
    img[off(SCROLL_CAVE) : off(SCROLL_CAVE) + len(scroll)] = scroll
    img[off(DRAW_SCROLL_HOOK) : off(DRAW_SCROLL_HOOK) + 6] = bytes.fromhex(f"4eb9{SCROLL_CAVE:08x}")

    def patch_imm32(imm_at: int, old: int, new: int) -> None:
        got = struct.unpack_from(">I", img, off(imm_at))[0]
        if got != old:
            raise SystemExit(f"{imm_at:#x}: want {old:#x}, got {got:#x}")
        struct.pack_into(">I", img, off(imm_at), new)

    patch_imm32(0x40068392, CTRL_LABELS, labels_addr)
    patch_imm32(0x4006839E, CTRL_GETTERS, getters_addr)

    for site in SETTER_LEA_SITES:
        if bytes(img[off(site) : off(site) + 2]) != bytes.fromhex("41f9"):
            raise SystemExit(f"{site:#x}: expected lea.l abs,a0")
        patch_imm32(site + 2, CTRL_SETTERS, setters_addr)

    if bytes(img[off(LIST_INIT_COUNT_PEA) : off(LIST_INIT_COUNT_PEA) + 4]) != bytes.fromhex("48780004"):
        raise SystemExit(f"{LIST_INIT_COUNT_PEA:#x}: expected pea #4 (count)")
    if bytes(img[off(LIST_INIT_VIEW_PEA) : off(LIST_INIT_VIEW_PEA) + 4]) != bytes.fromhex("48780004"):
        raise SystemExit(f"{LIST_INIT_VIEW_PEA:#x}: expected pea #4 (viewport)")
    img[off(LIST_INIT_COUNT_PEA) : off(LIST_INIT_COUNT_PEA) + 4] = bytes.fromhex(f"487800{NEW_ROWS:02x}")

    banned = bytes.fromhex("800000d4")
    if banned in cave or banned in build_cc_tx_gate():
        raise SystemExit("filter must not use 0x800000D4")
    if FILT_CC48.to_bytes(4, "big") not in cave:
        raise SystemExit("filter UI missing FILT_CC48")
    if FILT_CC48.to_bytes(4, "big") not in build_cc_tx_gate():
        raise SystemExit("gate missing FILT_CC48")
    if bytes.fromhex("0e81") in cave:
        raise SystemExit("shared getter btst d2,d1 must not appear")

    print(
        f"MIDI CONTROL filter +CC48/55/56 @ {FILTER_CAVE:#x} ({len(cave)}B) "
        f"gate={gate_addr:#x} (jmp); scroll @ {SCROLL_CAVE:#x} "
        f"DRAM_byte={FILT_CC48:#x}; {persist_note}; viewport={VIEWPORT} count={NEW_ROWS}"
    )
