"""MIDI CONTROL: CC48/55/56 TX enable ticks (checked=ON default).

Safety (from MIDSg/MIDSk):
- Gate entered with jmp only (jsr + jmp exits bricked LFO SPD/DEP).
- Flags in private DRAM after TRIG_SNAP — never 0x800000A8/D4/D8.
- Setter andi.l #1 only (no andi.b garbage).
"""
from __future__ import annotations

import struct

from ot3_asm import Asm

from .memory_map import FILT_CC48, FILT_CC55, FILT_CC56
from .util import off

GLYPH_ON = 0x400B5E90   # checked
GLYPH_OFF = 0x400B5E8E  # unchecked

CTRL_LABELS = 0x400B29E0
CTRL_GETTERS = 0x400B29F0
CTRL_SETTERS = 0x400B2A00
STOCK_ROWS = 4
NEW_ROWS = 7
VIEWPORT = 4

CTRL_LIST = 0x460E4654

# Stock zero island (same as MIDISCb). Ptr table @400ba8fa names this range;
# do not put Part-Clear here — filter UI/gate only.
FILTER_CAVE = 0x400C4302
FILTER_CAVE_END = 0x400C444C

SCROLL_CAVE = 0x400D51F0
SCROLL_CAVE_END = 0x400D5222

# FUN_40033e3c after AUDIO CC OUT bit1 check; d1=track, d3=CC
CC_TX_HOOK = 0x40033E5A
CC_TX_HOOK_STOCK = "7008b0816644"
CC_TX_BNE_TGT = 0x40033EA4
CC_TX_EARLY = 0x40033F24

LIST_INIT_COUNT_PEA = 0x4006845C
LIST_INIT_VIEW_PEA = 0x40068460
DRAW_SCROLL_HOOK = 0x4006838A
DRAW_SCROLL_HOOK_STOCK = "4283367c001b"

SETTER_LEA_SITES = (0x400684A2, 0x40068570, 0x4006858A, 0x400685A4)


def _checkbox_getter(flag: int) -> bytes:
    """flag==0 → checked (CC ON); flag!=0 → unchecked (CC OFF). DRAM boots 0."""
    return bytes.fromhex(
        f"203c{GLYPH_ON:08x}"  # move.l #checked,d0
        f"4ab9{flag:08x}"  # tst.l flag
        f"6706203c{GLYPH_OFF:08x}"  # beq.s +6; else move.l #unchecked,d0
        f"4e75"  # rts
    )


def _checkbox_setter(flag: int) -> bytes:
    """PERSONALIZE ABI: 4(sp)=delta (+1 YES/arrow). (flag+delta)&1.

    flag==0 checked/ON; YES toggles to 1=unchecked/OFF. Never treat stack as abs 0/1.
    """
    return bytes.fromhex(
        f"2039{flag:08x}"  # move.l flag,d0
        f"d0af0004"  # add.l 4(sp),d0
        f"028000000001"  # andi.l #1,d0
        f"23c0{flag:08x}"  # move.l d0,flag
        f"4e75"
    )


def build_cc_tx_gate() -> bytes:
    """Inline replacement for moveq #8 / cmp / bne at CC_TX_HOOK.

    Must be entered with jmp (not jsr): pass paths jmp into the stock
    function; a jsr would leave a return address and desync the epilogue
    (LFO SPD/DEP brick).

    flag==0 → pass (CC ON); flag!=0 → block (CC OFF).
    """
    a = Asm()
    a.cmpi(48, 3)
    a.beq("c48")
    a.cmpi(55, 3)
    a.beq("c55")
    a.cmpi(56, 3)
    a.beq("c56")
    a.label("pass")
    a.moveq(8, 0)
    a.hex("b081")  # cmp.l d1,d0
    a.beq("eq8")
    a.jmp(CC_TX_BNE_TGT)
    a.label("eq8")
    a.jmp(CC_TX_HOOK + 6)
    a.label("c48")
    a.tst_abs(FILT_CC48)
    a.beq("pass")
    a.bra("block")
    a.label("c55")
    a.tst_abs(FILT_CC55)
    a.beq("pass")
    a.bra("block")
    a.label("c56")
    a.tst_abs(FILT_CC56)
    a.beq("pass")
    a.label("block")
    a.jmp(CC_TX_EARLY)
    return a.link()


def ctrl_scroll_cave_bytes() -> bytes:
    """Force CONTROL viewport/count/scroll from selected, then stock loop setup.

    Peas alone do not scroll (same lesson as SRC SETUP).
    """
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


def apply_midi_ctrl_filter(img: bytearray, gate_addr: int) -> None:
    """UI tables in FILTER_CAVE; TX gate placed by caller (jmp entry)."""
    if bytes(img[off(CC_TX_HOOK) : off(CC_TX_HOOK) + 6]).hex() != CC_TX_HOOK_STOCK:
        raise SystemExit(f"CC_TX_HOOK not stock: {bytes(img[off(CC_TX_HOOK):off(CC_TX_HOOK)+6]).hex()}")
    if any(img[off(FILTER_CAVE) : off(FILTER_CAVE_END)]):
        raise SystemExit("FILTER_CAVE not empty")
    if any(img[off(SCROLL_CAVE) : off(SCROLL_CAVE_END)]):
        raise SystemExit("SCROLL_CAVE not empty")
    if bytes(img[off(DRAW_SCROLL_HOOK) : off(DRAW_SCROLL_HOOK) + 6]).hex() != DRAW_SCROLL_HOOK_STOCK:
        raise SystemExit(
            f"DRAW_SCROLL_HOOK not stock: {bytes(img[off(DRAW_SCROLL_HOOK):off(DRAW_SCROLL_HOOK)+6]).hex()}"
        )

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
    for f in (FILT_CC48, FILT_CC55, FILT_CC56):
        getters.append(here())
        cave += _checkbox_getter(f)
    setters = []
    for f in (FILT_CC48, FILT_CC55, FILT_CC56):
        setters.append(here())
        cave += _checkbox_setter(f)

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

    img[off(CC_TX_HOOK) : off(CC_TX_HOOK) + 6] = bytes.fromhex(f"4ef9{gate_addr:08x}")  # jmp gate

    print(
        f"MIDI CONTROL filter +CC48/55/56 @ {FILTER_CAVE:#x} ({len(cave)}B) "
        f"gate={gate_addr:#x} (jmp); scroll @ {SCROLL_CAVE:#x} "
        f"viewport={VIEWPORT} count={NEW_ROWS}"
    )
