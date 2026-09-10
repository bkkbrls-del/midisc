#!/usr/bin/env python3
"""Elektron aPLib-variant codec (Octatrack OS sections). Port of vendor/elektron-firmware-tool."""
from __future__ import annotations

APLIB_OFFSET_BIAS = 767
APLIB_REUSE_GAMMA = 2
APLIB_FAR_THRESHOLD = 3328
APLIB_MIN_MATCH = 2
APLIB_SECT_HDR = 8
APLIB_LIT_BITS = 9
MAX_CHAIN = 64
MAX_MATCH = 2048
HSIZE = 1 << 17
COST_INF = 0xFFFFFFFF


class BitState:
    __slots__ = ("src", "ip", "iend", "tag", "err")

    def __init__(self, src: bytes):
        self.src = src
        self.ip = APLIB_SECT_HDR
        self.iend = len(src)
        self.tag = 0
        self.err = False


def _gb_read(b: BitState) -> int:
    if b.ip >= b.iend:
        b.err = True
        return 0
    v = b.src[b.ip]
    b.ip += 1
    return v


def getbit(b: BitState) -> int:
    b.tag <<= 1
    if (b.tag & 0xFF) == 0:
        by = _gb_read(b)
        b.tag = (by << 1) | 1
        return (by >> 7) & 1
    return (b.tag >> 8) & 1


def getgamma(b: BitState) -> int:
    v = 1
    while True:
        v = (v << 1) + getbit(b)
        if getbit(b):
            break
        if b.err or v > 0x02000000:
            break
    return v


def ap_depack(src: bytes, outcap: int | None = None, allow_trunc: bool = True) -> bytes:
    b = BitState(src)
    out = bytearray()
    oend = outcap if outcap is not None else len(src) * 8
    last_off = 1

    while True:
        if b.err:
            if allow_trunc:
                break
            raise ValueError("depack bit error")
        if getbit(b):
            if len(out) >= oend:
                raise ValueError("depack output overflow")
            if b.ip >= b.iend:
                if allow_trunc:
                    break
                raise ValueError("depack truncated literal")
            out.append(b.src[b.ip])
            b.ip += 1
            continue
        g = getgamma(b)
        if g == APLIB_REUSE_GAMMA:
            off = last_off
        else:
            off = (g << 8) + _gb_read(b)
            if b.err:
                if allow_trunc:
                    break
                raise ValueError("depack truncated match")
            if off == APLIB_OFFSET_BIAS:
                break
            off -= APLIB_OFFSET_BIAS
            last_off = off
        ba = getbit(b)
        bb = getbit(b)
        sl = 2 * ba + bb
        if sl:
            L = sl
        else:
            L = getgamma(b) + 2
        if b.err:
            if allow_trunc:
                break
            raise ValueError("depack truncated length")
        if off > APLIB_FAR_THRESHOLD:
            L += 1
        n = L + 1
        if off == 0 or len(out) < off:
            raise ValueError(f"depack bad offset {off} at {len(out)}")
        if len(out) + n > oend:
            raise ValueError("depack match overflow")
        start = len(out) - off
        for _ in range(n):
            out.append(out[start])
            start += 1

    if not out and not allow_trunc:
        raise ValueError("depack empty output")
    return bytes(out)


class Packer:
    def __init__(self, outcap: int):
        self.o = bytearray(outcap)
        self.cap = outcap
        self.n = APLIB_SECT_HDR
        self.tagpos = -1
        self.tagbits = 0
        self.err = False

    def put_bit(self, bit: int):
        if self.tagbits == 0:
            if self.n >= self.cap:
                self.err = True
                return
            self.tagpos = self.n
            self.o[self.n] = 0
            self.n += 1
            self.tagbits = 8
        if bit:
            self.o[self.tagpos] |= 1 << (self.tagbits - 1)
        self.tagbits -= 1

    def put_byte(self, v: int):
        if self.n >= self.cap:
            self.err = True
            return
        self.o[self.n] = v & 0xFF
        self.n += 1

    def put_gamma(self, v: int):
        nb = 0
        t = v
        while t:
            nb += 1
            t >>= 1
        for i in range(nb - 2, -1, -1):
            self.put_bit((v >> i) & 1)
            self.put_bit(1 if i == 0 else 0)

    def put_literal(self, b: int):
        self.put_bit(1)
        self.put_byte(b)

    def put_match(self, off: int, matchlen: int, last_off: list[int]):
        self.put_bit(0)
        if off == last_off[0]:
            self.put_gamma(APLIB_REUSE_GAMMA)
        else:
            raw = off + APLIB_OFFSET_BIAS
            self.put_gamma(raw >> 8)
            self.put_byte(raw & 0xFF)
            last_off[0] = off
        bonus = 1 if off > APLIB_FAR_THRESHOLD else 0
        Lbase = matchlen - 1 - bonus
        if Lbase <= 3:
            self.put_bit(Lbase >> 1)
            self.put_bit(Lbase & 1)
        else:
            self.put_bit(0)
            self.put_bit(0)
            self.put_gamma(Lbase - 2)


def _gamma_cost(v: int) -> int:
    nb = 0
    while v:
        nb += 1
        v >>= 1
    return 2 * (nb - 1)


def _match_cost(off: int, L: int, last_off: int) -> int:
    b = 1 + (2 if off == last_off else _gamma_cost((off + APLIB_OFFSET_BIAS) >> 8) + 8)
    Lb = L - 1 - (1 if off > APLIB_FAR_THRESHOLD else 0)
    b += 2 if Lb <= 3 else 2 + _gamma_cost(Lb - 2)
    return b


def _hash2(d: bytes, i: int) -> int:
    return (((d[i] << 8) ^ d[i + 1]) & (HSIZE - 1))


def _match_run(data: bytes, a: int, b: int, cap: int) -> int:
    l = 0
    while l < cap and data[a + l] == data[b + l]:
        l += 1
    return l


def ap_pack(data: bytes) -> bytes:
    """Greedy aPLib-variant packer (fast; slightly larger than optimal DP)."""
    length = len(data)
    outcap = length + length // 2 + 256
    p = Packer(outcap)
    if length == 0:
        return bytes(8)

    last_off = [1]
    i = 0
    while i < length:
        best_off, best_len = 0, 0
        start = max(0, i - 512)
        for j in range(i - 1, start - 1, -1):
            off = i - j
            if off > i:
                continue
            cap = min(length - i, MAX_MATCH)
            l = _match_run(data, j, i, cap)
            mn = APLIB_MIN_MATCH + 1 if off > APLIB_FAR_THRESHOLD else APLIB_MIN_MATCH
            if l >= mn and l > best_len:
                best_off, best_len = off, l
                if best_len >= 64:
                    break
        if best_len >= (APLIB_MIN_MATCH + 1 if best_off > APLIB_FAR_THRESHOLD else APLIB_MIN_MATCH):
            p.put_match(best_off, best_len, last_off)
            i += best_len
        else:
            p.put_literal(data[i])
            i += 1
        if p.err:
            raise RuntimeError("ap_pack overflow during greedy emit")

    p.put_bit(0)
    p.put_gamma(0x1000002)
    p.put_byte(0xFF)
    if p.err:
        raise RuntimeError("ap_pack overflow at EOS")

    out = p.o[: p.n]
    stream = len(out) - APLIB_SECT_HDR
    ssum = sum(out[APLIB_SECT_HDR:])
    hdr = stream.to_bytes(4, "big") + ssum.to_bytes(4, "big")
    return hdr + out[APLIB_SECT_HDR:]
