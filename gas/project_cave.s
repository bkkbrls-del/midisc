| project_cave -- midisc cave, emitted from tools/midisc/*.py by tools/gas_port.py.
| DO NOT EDIT BY HAND: regenerate with `python3 tools/gas_port.py`, which also
| proves this file assembles to the bytes the Python encoder produces.
| Cross-cave references are linker symbols (see gas_port.py); everything
| else is the firmware's own address and stays literal.
        .text

        .global clr_pt
clr_pt:
        move.l %d0,-(%sp)
        move.l %d1,-(%sp)
        move.l %d2,-(%sp)
        move.l %a0,-(%sp)
        move.l %a1,-(%sp)
        move.l (24,%sp),%d0
        andi.l #0xf,%d0
        move.l %d0,%d2
        move.l #0x18b2,%d1
        muls.l %d0,%d1
        movea.l (0x46c82456).l,%a0
        adda.l %d1,%a0
        adda.l #0x90522,%a0
        bsr.w .Lclr_pt_z144
        movea.l #0x100a4ece,%a0
        adda.l %d1,%a0
        adda.l #0x17a2,%a0
        bsr.w .Lclr_pt_z144
        move.l %d2,%d0
        move.l #0x90,%d1
        muls.l %d0,%d1
        movea.l #0x460c9c00,%a0
        adda.l %d1,%a0
        bsr.w .Lclr_pt_z144
        move.l %d2,%d0
        mvz.b (last_part).l,%d1
        andi.l #0xf,%d1
        .byte 0xb0, 0x81
        beq.w .Lclr_pt_wipe
        mvz.b (0x100b14cf).l,%d1
        .byte 0xb0, 0x81
        bne.w .Lclr_pt_skip
.Lclr_pt_wipe:
        movea.l #msc,%a0
        move.l #0x1000,%d1
.Lclr_pt_ff:
        .byte 0x10, 0xbc, 0x00, 0xff
        .byte 0x52, 0x88
        .byte 0x53, 0x81
        bne.w .Lclr_pt_ff
        moveq #-1,%d0
        move.b %d0,(last_part).l
.Lclr_pt_skip:
        move.l (%sp)+,%a1
        move.l (%sp)+,%a0
        move.l (%sp)+,%d2
        move.l (%sp)+,%d1
        move.l (%sp)+,%d0
        jmp (0x4004a9d0).l
.Lclr_pt_z144:
        moveq #36,%d0
.Lclr_pt_z1:
        .byte 0x42, 0x98
        .byte 0x53, 0x80
        bne.w .Lclr_pt_z1
        rts

        .global after_proj
after_proj:
        move.l %d0,-(%sp)
        move.l %d1,-(%sp)
        move.l %d2,-(%sp)
        move.l %d3,-(%sp)
        move.l %a0,-(%sp)
        move.l %a1,-(%sp)
        .byte 0x2f, 0x0a
        movea.l #0x40020898,%a2
        moveq #0,%d3
.Lafter_proj_lp:
        move.l %d3,%d0
        move.l #0x18b2,%d1
        muls.l %d0,%d1
        movea.l #0x100a4ece,%a1
        adda.l %d1,%a1
        adda.l #0x17a2,%a1
        move.l %d3,%d0
        move.l #0x90,%d1
        muls.l %d0,%d1
        movea.l #0x460c9c00,%a0
        adda.l %d1,%a0
        .byte 0x48, 0x78, 0x00, 0x90
        .byte 0x2f, 0x09
        .byte 0x2f, 0x08
        .byte 0x4e, 0x92
        .byte 0x4f, 0xef, 0x00, 0x0c
        addq.l #1,%d3
        cmpi.l #0x4,%d3
        bcs.w .Lafter_proj_lp
        .byte 0x24, 0x5f
        move.l (%sp)+,%a1
        move.l (%sp)+,%a0
        move.l (%sp)+,%d3
        move.l (%sp)+,%d2
        move.l (%sp)+,%d1
        move.l (%sp)+,%d0
        jsr (unpack).l
        jmp (0x400418e0).l
