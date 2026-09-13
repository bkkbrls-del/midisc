| reload_cave -- midisc cave, emitted from tools/midisc/*.py by tools/gas_port.py.
| DO NOT EDIT BY HAND: regenerate with `python3 tools/gas_port.py`, which also
| proves this file assembles to the bytes the Python encoder produces.
| Cross-cave references are linker symbols (see gas_port.py); everything
| else is the firmware's own address and stays literal.
        .text

        .global rel_after
rel_after:
        .byte 0x2f, 0x00
        move.l %d1,-(%sp)
        move.l %d2,-(%sp)
        move.l %d3,-(%sp)
        move.l %a0,-(%sp)
        move.l %a1,-(%sp)
        .byte 0x2f, 0x0a
        move.l (28,%sp),%d3
        andi.l #0xf,%d3
        move.l %d3,%d0
        lsl.l #2,%d0
        movea.l #0x460db000,%a0
        adda.l %d0,%a0
        .byte 0x20, 0x10
        cmpi.l #0x4d53434b,%d0
        bne.w .Lrel_after_no_msc
        move.l %d3,%d0
        lsl.l #8,%d0
        lsl.l #4,%d0
        movea.l #0x460cb000,%a1
        adda.l %d0,%a1
        movea.l #msc,%a0
        movea.l #0x40020898,%a2
        .byte 0x48, 0x78, 0x10, 0x00
        .byte 0x2f, 0x09
        .byte 0x2f, 0x08
        .byte 0x4e, 0x92
        .byte 0x4f, 0xef, 0x00, 0x0c
        move.l %d3,%d0
        move.b %d0,(last_part).l
        bra.w .Lrel_after_ok
.Lrel_after_no_msc:
        jsr (freeze_alt).l
        move.l %d3,%d0
        move.b %d0,(unpack_src).l
        jsr (unpack).l
.Lrel_after_ok:
        jsr (pack).l
        .byte 0x42, 0xb9, 0x46, 0x0c, 0xa5, 0x04
        moveq #-1,%d0
        move.b %d0,(0x460ca579).l
        jsr (xf_mix).l
        .byte 0x24, 0x5f
        move.l (%sp)+,%a1
        move.l (%sp)+,%a0
        move.l (%sp)+,%d3
        move.l (%sp)+,%d2
        move.l (%sp)+,%d1
        .byte 0x20, 0x1f
        movea.l (apply_ret).l,%a0
        .byte 0x4e, 0xd0
