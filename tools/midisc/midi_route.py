"""MIDI CHAN T1–T8: internal route MIDI-track note/CC out → audio-track MIDI in.

CHAN values 17–24 = T1–T8. Stock TX still builds the 3-byte MIDI buffer, but
FUN_40010bc8 is diverted to call note-on / note-off / CC IN with TRIG CH forced
to the destination audio track (no DIN/USB).
"""
from __future__ import annotations

import struct

from ot3_asm import Asm

from .memory_map import CLIP
from .util import jmp_abs, off

ENABLE_MIDI_T_ROUTE = False  # HW brick on encoder/trig (2026-09-15); keep code, do not enable

# HW report (disabled build): bricks on encoder turns and trigs. NOTE SETUP T1–T8
# draw wrong; main UI shows CH:17 for T1 (separate formatter, not CHAN_FMT_PTR).
# Suspects: UART_SEND trampoline / rebuild hook / inject @ 0x4010C350.

NOTE_E = 0x400D3E06
CHAN_COUNT_ADDR = NOTE_E + 0xD2 + 6 * 4
CHAN_COUNT_STOCK = 17
CHAN_COUNT_NEW = 25
CHAN_FMT_PTR = NOTE_E + 0x11A
CHAN_FMT_STOCK = 0x4003C770

T_STRINGS = 0x400A740E
OFF_STRING = 0x400B4E78
PCT_D = 0x400B465D
SPRINTF = 0x40013A08

NOTE_CHAN_HOOK = 0x4009E9EC
NOTE_CHAN_STOCK = "79906700018a"
NOTE_CHAN_CONT = 0x4009E9F8
NOTE_CHAN_OFF = 0x4009EB7A

CC_CHAN_HOOK = 0x4009EF2E
CC_CHAN_STOCK = "6700034c2800"
CC_CHAN_CONT = 0x4009EF3A
CC_CHAN_OFF = 0x4009F27C

REBUILD_CHAN_HOOK = 0x400018AE
REBUILD_CHAN_STOCK = "719067165380"
REBUILD_CHAN_CONT = 0x400018B8
REBUILD_CHAN_OFF = 0x400018C8

UART_SEND = 0x40010BC8
UART_SEND_STOCK8 = "4fefffec48d7043c"
UART_SEND_CONT = 0x40010BD0

NOTE_ON = 0x4000E018
NOTE_OFF = 0x4000DB98
CC_IN = 0x4000E79C

TRIG_CH = 0x8000003F
AUTO_CH = 0x80000047
AUDIO_NOTE_IN = 0x8000004B
AUDIO_CC_IN = 0x80000049

ROUTE_FLAG = CLIP + 0xC84
ROUTE_TRACK = CLIP + 0xC85
TRIG_SAVE = CLIP + 0xC86

ROUTE_CAVE = 0x400C4302
ROUTE_CAVE_END = 0x400C444C
# Larger zero pad for inject body (hooks stay in ROUTE_CAVE)
INJECT_CAVE = 0x4010C350
INJECT_CAVE_END = 0x4010C57E


def _bls(a: Asm, name: str) -> Asm:
    return a._br("63", name)


def build_chan_formatter() -> bytes:
    """Match stock 0x4003c770 ABI: 4(sp)=dest, 8(sp)=value."""
    a = Asm()
    a.hex("222f0004")  # move.l 4(sp), d1
    a.hex("202f0008")  # move.l 8(sp), d0
    a.tst_d(0)
    a.beq("off")
    a.cmpi(16, 0)
    _bls(a, "num")

    a.addi(0xFFFFFFEF, 0)  # d0 -= 17
    a.move_l_dd(0, 2)
    a.lsl(1, 0)
    a.move_l_dd(2, 3)
    a.lsl(2, 3)
    a.add_dd(3, 0)
    a.movea_imm(T_STRINGS, 0)
    a.adda_d(0, 0)
    a.move_a_d(0, 0)
    a.hex("2f400008")  # move.l d0, 8(sp)
    a.jmp(SPRINTF)

    a.label("off")
    a.move_l_imm(OFF_STRING, 0)
    a.hex("2f400008")
    a.jmp(SPRINTF)

    a.label("num")
    a.hex("2f00")
    a.hex(f"4879{PCT_D:08x}")
    a.hex("2f01")
    a.jsr(SPRINTF)
    a.hex("4fef000c")
    a.rts()
    return a.link()


def build_note_chan_hook() -> bytes:
    a = Asm()
    a.hex("7990")  # mvz.b (a0), d4
    a.beq("off")
    a.cmpi(16, 4)
    _bls(a, "ext")
    a.move_l_dd(4, 0)
    a.addi(0xFFFFFFEF, 0)
    a.move_b_d_abs(0, ROUTE_TRACK)
    a.moveq(1, 0)
    a.move_b_d_abs(0, ROUTE_FLAG)
    a.moveq(1, 4)
    a.label("ext")
    a.hex("5384")
    a.hex("343c000f")
    a.hex("c882")
    a.jmp(NOTE_CHAN_CONT)
    a.label("off")
    a.jmp(NOTE_CHAN_OFF)
    return a.link()


def build_cc_chan_hook() -> bytes:
    a = Asm()
    a.beq("off")
    a.cmpi(16, 0)
    _bls(a, "ext")
    a.move_l_dd(0, 1)
    a.addi(0xFFFFFFEF, 1)
    a.move_b_d_abs(1, ROUTE_TRACK)
    a.moveq(1, 1)
    a.move_b_d_abs(1, ROUTE_FLAG)
    a.moveq(1, 0)
    a.label("ext")
    a.hex("2800")
    a.hex("5384")
    a.hex("343c000f")
    a.hex("c882")
    a.jmp(CC_CHAN_CONT)
    a.label("off")
    a.jmp(CC_CHAN_OFF)
    return a.link()


def build_rebuild_chan_hook() -> bytes:
    a = Asm()
    a.hex("7190")
    a.beq("off")
    a.cmpi(16, 0)
    a.bhi("off")
    a.hex("5380")
    a.hex("720f")
    a.hex("c081")
    a.jmp(REBUILD_CHAN_CONT)
    a.label("off")
    a.jmp(REBUILD_CHAN_OFF)
    return a.link()


def build_inject() -> bytes:
    """a0 = 3-byte MIDI msg, d7 = audio track 0..7."""
    a = Asm()
    a.push("d0", "d1", "d2", "d3", "a1")
    a.hex("2f0a")  # move.l a2, -(sp)
    a.hex("2448")  # a2 = msg

    # save TRIG[8] + AUTO + NOTE_IN + CC_IN
    a.movea_imm(TRIG_SAVE, 1)
    a.moveq(0, 3)
    a.label("sv")
    a.movea_imm(TRIG_CH, 0)
    a.adda_d(3, 0)
    a.mvz_b_ind(0, 0)
    a.move_b_d_ind(0, 1)
    a.hex("5289")  # addq.l #1, a1
    a.addq(1, 3)
    a.cmpi(8, 3)
    a.bcs("sv")
    a.move_b_abs_d(AUTO_CH, 0)
    a.move_b_d_ind(0, 1)
    a.hex("5289")
    a.move_b_abs_d(AUDIO_NOTE_IN, 0)
    a.move_b_d_ind(0, 1)
    a.hex("5289")
    a.move_b_abs_d(AUDIO_CC_IN, 0)
    a.move_b_d_ind(0, 1)

    # only track d7 listens on ch 0; enable NOTE/CC IN
    a.moveq(0, 3)
    a.label("clr")
    a.movea_imm(TRIG_CH, 0)
    a.adda_d(3, 0)
    a.moveq(0xFF, 0)
    a.hex("b683")  # cmp.l d3, d7
    a.bne("notme")
    a.moveq(0, 0)
    a.label("notme")
    a.move_b_d_ind(0, 0)
    a.addq(1, 3)
    a.cmpi(8, 3)
    a.bcs("clr")
    a.moveq(0xFF, 0)
    a.move_b_d_abs(0, AUTO_CH)
    a.moveq(1, 0)
    a.move_b_d_abs(0, AUDIO_NOTE_IN)
    a.move_b_d_abs(0, AUDIO_CC_IN)

    # status channel nibble → 0
    a.mvz_b_ind(2, 0)
    a.andi(0xF0, 0)
    a.move_b_d_ind(0, 2)

    a.mvz_b_ind(2, 0)
    a.asr(4, 0)
    a.cmpi(0x9, 0)
    a.beq("non")
    a.cmpi(0x8, 0)
    a.beq("noff")
    a.cmpi(0xB, 0)
    a.beq("cc")
    a.bra("restore")

    a.label("non")
    a.hex("42a7")
    a.hex("2f0a")
    a.jsr(NOTE_ON)
    a.hex("4fef0008")
    a.bra("restore")

    a.label("noff")
    a.hex("42a7")
    a.hex("2f0a")
    a.jsr(NOTE_OFF)
    a.hex("4fef0008")
    a.bra("restore")

    a.label("cc")
    a.hex("42a7")
    a.hex("2f0a")
    a.jsr(CC_IN)
    a.hex("4fef0008")

    a.label("restore")
    a.movea_imm(TRIG_SAVE, 1)
    a.moveq(0, 3)
    a.label("rs")
    a.movea_imm(TRIG_CH, 0)
    a.adda_d(3, 0)
    a.mvz_b_ind(1, 0)
    a.move_b_d_ind(0, 0)
    a.hex("5289")
    a.addq(1, 3)
    a.cmpi(8, 3)
    a.bcs("rs")
    a.mvz_b_ind(1, 0)
    a.move_b_d_abs(0, AUTO_CH)
    a.hex("5289")
    a.mvz_b_ind(1, 0)
    a.move_b_d_abs(0, AUDIO_NOTE_IN)
    a.hex("5289")
    a.mvz_b_ind(1, 0)
    a.move_b_d_abs(0, AUDIO_CC_IN)

    a.hex("245f")  # movea.l (sp)+, a2
    a.pop("a1", "d3", "d2", "d1", "d0")
    a.rts()
    return a.link()


def build_uart_hook(inject_addr: int) -> bytes:
    a = Asm()
    a.hex(f"4a39{ROUTE_FLAG:08x}")
    a.beq("stock")
    a.hex(f"4239{ROUTE_FLAG:08x}")
    a.hex("206f000c")  # movea.l 12(sp), a0
    a.mvz_b_abs(ROUTE_TRACK, 7)
    a.jsr(inject_addr)
    a.rts()
    a.label("stock")
    a.hex(UART_SEND_STOCK8)
    a.jmp(UART_SEND_CONT)
    return a.link()


def apply_midi_t_route(img: bytearray) -> dict[str, int]:
    if not ENABLE_MIDI_T_ROUTE:
        return {}

    got = struct.unpack(">I", bytes(img[off(CHAN_COUNT_ADDR) : off(CHAN_COUNT_ADDR) + 4]))[0]
    if got != CHAN_COUNT_STOCK:
        raise SystemExit(f"CHAN count want {CHAN_COUNT_STOCK}, got {got}")
    img[off(CHAN_COUNT_ADDR) : off(CHAN_COUNT_ADDR) + 4] = struct.pack(">I", CHAN_COUNT_NEW)

    fmt_got = struct.unpack(">I", bytes(img[off(CHAN_FMT_PTR) : off(CHAN_FMT_PTR) + 4]))[0]
    if fmt_got != CHAN_FMT_STOCK:
        raise SystemExit(f"CHAN fmt ptr want {CHAN_FMT_STOCK:#x}, got {fmt_got:#x}")

    for site, stock in (
        (NOTE_CHAN_HOOK, NOTE_CHAN_STOCK),
        (CC_CHAN_HOOK, CC_CHAN_STOCK),
        (REBUILD_CHAN_HOOK, REBUILD_CHAN_STOCK),
    ):
        if bytes(img[off(site) : off(site) + 6]).hex() != stock:
            raise SystemExit(
                f"{site:#x} want {stock}, got {bytes(img[off(site):off(site)+6]).hex()}"
            )
    if bytes(img[off(UART_SEND) : off(UART_SEND) + 8]).hex() != UART_SEND_STOCK8:
        raise SystemExit("UART_SEND prologue mismatch")

    cave = bytearray()
    addrs: dict[str, int] = {}

    def place(name: str, blob: bytes) -> int:
        addr = ROUTE_CAVE + len(cave)
        cave.extend(blob)
        addrs[name] = addr
        return addr

    abs_fmt = place("fmt", build_chan_formatter())
    abs_note = place("note_chan", build_note_chan_hook())
    abs_cc = place("cc_chan", build_cc_chan_hook())
    abs_reb = place("rebuild", build_rebuild_chan_hook())
    inj = build_inject()
    if len(inj) > INJECT_CAVE_END - INJECT_CAVE:
        raise SystemExit(f"INJECT_CAVE overrun {len(inj)}")
    if any(img[off(INJECT_CAVE) : off(INJECT_CAVE_END)]):
        raise SystemExit("INJECT_CAVE not empty")
    abs_inj = INJECT_CAVE
    addrs["inject"] = abs_inj
    abs_uart = place("uart", build_uart_hook(abs_inj))

    if ROUTE_CAVE + len(cave) > ROUTE_CAVE_END:
        raise SystemExit(f"ROUTE_CAVE overrun {len(cave)}")
    if any(img[off(ROUTE_CAVE) : off(ROUTE_CAVE_END)]):
        raise SystemExit("ROUTE_CAVE not empty (CC filter cave in use?)")

    img[off(ROUTE_CAVE) : off(ROUTE_CAVE) + len(cave)] = bytes(cave)
    img[off(INJECT_CAVE) : off(INJECT_CAVE) + len(inj)] = inj
    img[off(CHAN_FMT_PTR) : off(CHAN_FMT_PTR) + 4] = abs_fmt.to_bytes(4, "big")
    img[off(NOTE_CHAN_HOOK) : off(NOTE_CHAN_HOOK) + 6] = jmp_abs(abs_note)
    img[off(CC_CHAN_HOOK) : off(CC_CHAN_HOOK) + 6] = jmp_abs(abs_cc)
    img[off(REBUILD_CHAN_HOOK) : off(REBUILD_CHAN_HOOK) + 6] = jmp_abs(abs_reb)
    img[off(UART_SEND) : off(UART_SEND) + 6] = jmp_abs(abs_uart)

    addrs["cave_len"] = len(cave)
    addrs["inject_len"] = len(inj)
    print(
        f"MIDI T-route hooks {len(cave)}B @ {ROUTE_CAVE:#x} inject {len(inj)}B @ {INJECT_CAVE:#x} "
        f"fmt={abs_fmt:#x} note={abs_note:#x} cc={abs_cc:#x} "
        f"reb={abs_reb:#x} inj={abs_inj:#x} uart={abs_uart:#x}"
    )
    return addrs
