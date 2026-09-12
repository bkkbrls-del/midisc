| cave2 -- midisc cave, emitted from tools/midisc/*.py by tools/gas_port.py.
| DO NOT EDIT BY HAND: regenerate with `python3 tools/gas_port.py`, which also
| proves this file assembles to the bytes the Python encoder produces.
| Cross-cave references are linker symbols (see gas_port.py); everything
| else is the firmware's own address and stays literal.
        .text

        .global rebuild
rebuild:
        .byte 0x2f, 0x07
        .byte 0x2f, 0x09
        moveq #0,%d6
        movea.l (0x46c82456).l,%a0
        move.l %a0,%d0
        tst.l %d0
        beq.w .Lrebuild_abort
        movea.l #0x460c9e49,%a0
        moveq #8,%d1
.Lrebuild_zt:
        .byte 0x42, 0x10
        .byte 0x52, 0x88
        .byte 0x53, 0x81
        bne.w .Lrebuild_zt
        mvz.b (0x100b14cf).l,%d0
        andi.l #0xf,%d0
        move.l #0x18b2,%d1
        muls.l %d0,%d1
        movea.l (0x46c82456).l,%a0
        adda.l %d1,%a0
        adda.l #0x8ed90,%a0
        mvz.b (%a0),%d3
        mvz.b (1,%a0),%d5
        moveq #0,%d4
.Lrebuild_tr:
        movea.l #0x460c9e51,%a0
        adda.l %d4,%a0
        move.b %d6,(%a0)
        moveq #0,%d1
.Lrebuild_fl:
        moveq #-1,%d0
        cmpi.l #0xff,%d3
        beq.w .Lrebuild_va_d
        move.l %d3,%d2
        andi.l #0xf,%d2
        lsl.l #8,%d2
        movea.l #msc,%a0
        adda.l %d2,%a0
        move.l %d4,%d2
        lsl.l #5,%d2
        adda.l %d2,%a0
        adda.l %d1,%a0
        mvz.b (%a0),%d0
.Lrebuild_va_d:
        moveq #-1,%d2
        cmpi.l #0xff,%d5
        beq.w .Lrebuild_vb_d
        move.l %d5,%d7
        andi.l #0xf,%d7
        lsl.l #8,%d7
        movea.l #msc,%a0
        adda.l %d7,%a0
        move.l %d4,%d7
        lsl.l #5,%d7
        adda.l %d7,%a0
        adda.l %d1,%a0
        mvz.b (%a0),%d2
.Lrebuild_vb_d:
        cmpi.l #0xff,%d0
        bne.w .Lrebuild_keep
        cmpi.l #0xff,%d2
        beq.w .Lrebuild_nxf
.Lrebuild_keep:
        cmpi.l #0x20,%d6
        bcc.w .Lrebuild_fin
        move.l %d4,%d7
        lsl.l #5,%d7
        or.l %d1,%d7
        .byte 0x2f, 0x02
        movea.l #0x460c9e59,%a0
        move.l %d6,%d2
        add.l %d2,%d2
        add.l %d6,%d2
        adda.l %d2,%a0
        .byte 0x10, 0xc7
        .byte 0x10, 0xc0
        .byte 0x24, 0x1f
        .byte 0x10, 0xc2
        addq.l #1,%d6
        movea.l #0x460c9e49,%a0
        adda.l %d4,%a0
        .byte 0x52, 0x10
.Lrebuild_nxf:
        addq.l #1,%d1
        cmpi.l #0x1e,%d1
        bcs.w .Lrebuild_fl
        addq.l #1,%d4
        cmpi.l #0x8,%d4
        bcs.w .Lrebuild_tr
.Lrebuild_fin:
        move.b %d6,(0x460c9e48).l
        move.l #0x4d53434c,%d0
        move.l %d0,(0x460c9e44).l
        .byte 0x22, 0x5f
        .byte 0x2e, 0x1f
        rts
.Lrebuild_abort:
        .byte 0x22, 0x5f
        .byte 0x2e, 0x1f
        rts
