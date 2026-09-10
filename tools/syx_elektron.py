#!/usr/bin/env python3
"""Octatrack ELEK .syx decode/encode — enough to repack a patched MAIN OS section."""
from __future__ import annotations

import struct

SYX_START = 0xF0
SYX_END = 0xF7
SYX_MASK7 = 0x7F
SYX_HIGH_BIT = 0x80
SYX_7IN8_GROUP = 7
SYX_CMD_DATA = 0x7E
SYX_CMD_MARKER = 0x7F
PK_DEV = 3
PK_CMD = 5
LEGACY_THDR = 14
ELEK_DEC_PKT = 63
PREELE_COUNTER = 0x4000

ELEK_SECT_OFF = 0x12
ELEK_VERSION_OFF = 0x0D
DEV_OCTATRACK = 0x05


def _legacy_ck(dev: int, nb: bytes, payload_sum: int) -> int:
    s = dev + sum(nb) + payload_sum
    return ((s >> 4) + s) & 0xF


def decode_payload(dec: bytearray, p: bytes) -> None:
    k = 0
    while k < len(p):
        ms = p[k]
        nd = min(SYX_7IN8_GROUP, len(p) - k - 1)
        for n in range(nd):
            dec.append(p[k + 1 + n] | (((ms >> (SYX_7IN8_GROUP - 1 - n)) & 1) * SYX_HIGH_BIT))
        k += SYX_7IN8_GROUP + 1


def decode_syx_elek(buf: bytes) -> tuple[bytes, int]:
    """Return (ELEK container, device_id)."""
    dec = bytearray()
    dev = 0
    i = 0
    while i < len(buf):
        if buf[i] != SYX_START:
            i += 1
            continue
        j = i + 1
        while j < len(buf) and buf[j] != SYX_END:
            j += 1
        if j >= len(buf):
            break
        m = buf[i + 1 : j]
        mlen = len(m)
        if mlen > PK_DEV and not dev:
            dev = m[PK_DEV]
        if mlen > LEGACY_THDR and m[PK_CMD] == SYX_CMD_DATA:
            before = len(dec)
            decode_payload(dec, m[LEGACY_THDR:])
            # ignore checksum failures — stock repack only needs payload bytes
            _ = before
        i = j + 1
    if dec[:4] != b"ELEK":
        raise ValueError(f"decoded stream does not start with ELEK: {dec[:8]!r}")
    return bytes(dec), dev


def _preele_nib6(v: int) -> bytes:
    return bytes([(v >> (4 * (5 - k))) & 0xF for k in range(6)])


def _encode_8in7(data: bytes) -> bytes:
    out = bytearray()
    i = 0
    while i < len(data):
        nd = min(SYX_7IN8_GROUP, len(data) - i)
        ms = 0
        for n in range(nd):
            if data[i + n] & SYX_HIGH_BIT:
                ms |= 1 << (SYX_7IN8_GROUP - 1 - n)
        out.append(ms)
        for n in range(nd):
            out.append(data[i + n] & SYX_MASK7)
        i += SYX_7IN8_GROUP
    return bytes(out)


def _emit_legacy_data(dev: int, nb: bytes, chunk: bytes) -> bytes:
    mfr = bytes([0x00, 0x20, 0x3C])
    s = sum(chunk) & 0xFFFFFFFF
    C = _legacy_ck(dev, nb, s)
    out = bytearray()
    out.append(SYX_START)
    out += mfr
    out.append(dev)
    out.append(0x00)
    out.append(SYX_CMD_DATA)
    out.append((C >> 4) & 0xF)
    out.append(C & 0xF)
    out += nb
    out += _encode_8in7(chunk)
    out.append(SYX_END)
    return bytes(out)


def encode_syx_elek(container: bytes, dev: int = DEV_OCTATRACK) -> bytes:
    out = bytearray()
    off = 0
    clen = len(container)
    while off < clen:
        n = min(ELEK_DEC_PKT, clen - off)
        nb = _preele_nib6(PREELE_COUNTER + off)
        out += _emit_legacy_data(dev, nb, container[off : off + n])
        off += n
    mfr = bytes([0x00, 0x20, 0x3C])
    out.append(SYX_START)
    out += mfr
    out.append(dev)
    out += bytes([0x00, SYX_CMD_DATA, SYX_END])
    tn = _preele_nib6(clen)
    out.append(SYX_START)
    out += mfr
    out.append(dev)
    out += bytes([0x00, SYX_CMD_MARKER])
    out += tn
    out.append(SYX_END)
    return bytes(out)


def set_elek_version(container: bytearray, version: str) -> None:
    """Write boot splash version — 10-char field @ 0x08, space-padded right-justified."""
    voff = 0x08
    fend = ELEK_SECT_OFF
    cap = fend - voff
    if len(version) > cap:
        raise ValueError(f"version string too long ({len(version)} > {cap})")
    pad = cap - len(version)
    field = (" " * pad + version).encode("ascii")
    container[voff:fend] = field


def replace_elek_section(container: bytearray, packed_section: bytes) -> bytearray:
    """Return new container with section at ELEK_SECT_OFF replaced."""
    stream_len = struct.unpack(">I", container[ELEK_SECT_OFF : ELEK_SECT_OFF + 4])[0]
    old_comp = 8 + stream_len
    sec_end = ELEK_SECT_OFF + old_comp
    nc = bytearray(container[:ELEK_SECT_OFF])
    nc += packed_section
    if sec_end < len(container):
        nc += container[sec_end:]
    return nc
