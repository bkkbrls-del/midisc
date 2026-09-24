| seam_bank -- midisc cave, emitted from tools/midisc/*.py by tools/gas_port.py.
| DO NOT EDIT BY HAND: regenerate with `python3 tools/gas_port.py`, which also
| proves this file assembles to the bytes the Python encoder produces.
| Cross-cave references are linker symbols (see gas_port.py); everything
| else is the firmware's own address and stays literal.
        .text

        .global bank_sw
bank_sw:
        .byte 0x4f, 0xef, 0xff, 0xc4
        .byte 0x48, 0xd7, 0x7f, 0xfe
        .byte 0x2f, 0x00
        mvz.b (0x460ca68c).l,%d1
        tst.l %d1
        bne.w .Lbank_sw_kits
        jsr (pack).l
        .byte 0x20, 0x1f
        move.l %d0,(0x46c82456).l
        jsr (unpack).l
        bra.w .Lbank_sw_done
.Lbank_sw_kits:
        .byte 0x20, 0x1f
        move.l %d0,(0x46c82456).l
.Lbank_sw_done:
        .byte 0x4c, 0xd7, 0x7f, 0xfe
        .byte 0x4f, 0xef, 0x00, 0x3c
        rts

        .global bank_inv
bank_inv:
        .byte 0x4f, 0xef, 0xff, 0xc4
        .byte 0x48, 0xd7, 0x7f, 0xfe
        move.l %d0,(0x46c82456).l
        mvz.b (0x460ca68c).l,%d1
        tst.l %d1
        bne.w .Lbank_inv_done
        moveq #-1,%d1
        move.b %d1,(last_part).l
        movea.l #0x460c9c00,%a0
        .short 0x243c
        .long 0xf        | move.l #15,%d2 (long form kept)
.Lbank_inv_zck:
        .byte 0x42, 0x50
        adda.l #0x90,%a0
        .byte 0x53, 0x82
        bpl.w .Lbank_inv_zck
        movea.l #0x460db000,%a0
        .short 0x243c
        .long 0xf        | move.l #15,%d2 (long form kept)
.Lbank_inv_zmk:
        .byte 0x42, 0x90
        adda.l #0x4,%a0
        .byte 0x53, 0x82
        bpl.w .Lbank_inv_zmk
.Lbank_inv_done:
        .byte 0x4c, 0xd7, 0x7f, 0xfe
        .byte 0x4f, 0xef, 0x00, 0x3c
        rts
