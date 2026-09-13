| scene_paste -- midisc cave, emitted from tools/midisc/*.py by tools/gas_port.py.
| DO NOT EDIT BY HAND: regenerate with `python3 tools/gas_port.py`, which also
| proves this file assembles to the bytes the Python encoder produces.
| Cross-cave references are linker symbols (see gas_port.py); everything
| else is the firmware's own address and stays literal.
        .text

        .global pst_sc
pst_sc:
        move.l (0x460d0ffa).l,%d0
        cmpi.l #0x10,%d0
        bne.w .Lpst_sc_stock
        jsr (unpack).l
        move.l %d0,-(%sp)
        move.l %d1,-(%sp)
        move.l %a0,-(%sp)
        move.l %a1,-(%sp)
        move.l (24,%sp),%d0
        andi.l #0xf,%d0
        lsl.l #8,%d0
        movea.l #msc,%a0
        adda.l %d0,%a0
        .byte 0x22, 0x48
        movea.l #0x460c9a00,%a0
        move.l #0x100,%d1
.Lpst_sc_ps:
        .byte 0x10, 0x18
        .byte 0x12, 0xc0
        .byte 0x53, 0x81
        bne.w .Lpst_sc_ps
        move.l (%sp)+,%a1
        move.l (%sp)+,%a0
        move.l (%sp)+,%d1
        move.l (%sp)+,%d0
        mvz.b (0x100b14cf).l,%d0
        move.b %d0,(last_part).l
        jsr (pack).l
        jsr (dirty).l
.Lpst_sc_stock:
        jmp (0x40027578).l
