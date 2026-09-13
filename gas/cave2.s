| cave2 -- midisc cave, emitted from tools/midisc/*.py by tools/gas_port.py.
| DO NOT EDIT BY HAND: regenerate with `python3 tools/gas_port.py`, which also
| proves this file assembles to the bytes the Python encoder produces.
| Cross-cave references are linker symbols (see gas_port.py); everything
| else is the firmware's own address and stays literal.
        .text

        .global rebuild
rebuild:
        move.l (0x460d16c8).l,%d5
        andi.l #0x7f,%d5
        .short 0x203c
        .long 0x7f        | move.l #127,%d0 (long form kept)
        sub.l %d5,%d0
        move.l %d0,%d5
        tst.l %d5
        beq.w .Lrebuild_pure
        cmpi.l #0x7f,%d5
        bne.w .Lrebuild_out
.Lrebuild_pure:
        mvz.b (0x100b14cf).l,%d0
        andi.l #0xf,%d0
        move.l #0x18b2,%d6
        muls.l %d0,%d6
        movea.l (0x46c82456).l,%a0
        adda.l %d6,%a0
        adda.l #0x8ed90,%a0
        mvz.b (%a0),%d3
        mvz.b (1,%a0),%d4
        tst.l %d5
        beq.w .Lrebuild_use_a
        move.l %d4,%d3
.Lrebuild_use_a:
        cmpi.l #0xff,%d3
        beq.w .Lrebuild_out
        andi.l #0xf,%d3
        lsl.l #8,%d3
        movea.l #msc,%a2
        adda.l %d3,%a2
        move.l %d7,%d3
        lsl.l #5,%d3
        adda.l %d3,%a2
        moveq #0,%d1
.Lrebuild_lp:
        .byte 0x20, 0x4a
        adda.l %d1,%a0
        mvz.b (%a0),%d5
        cmpi.l #0xff,%d5
        beq.w .Lrebuild_nx
        move.l %d7,%d0
        lsl.l #6,%d0
        move.l %d7,%d4
        lsl.l #2,%d4
        add.l %d4,%d0
        add.l %d1,%d0
        movea.l #0x46c76dc0,%a0
        adda.l %d0,%a0
        mvz.b (%a0),%d0
        .byte 0x20, 0x49
        adda.l %d1,%a0
        move.b %d0,(%a0)
.Lrebuild_nx:
        addq.l #1,%d1
        cmpi.l #0x1e,%d1
        bcs.w .Lrebuild_lp
.Lrebuild_out:
        rts

        .global freeze_alt
freeze_alt:
        move.l %d0,-(%sp)
        move.l %d1,-(%sp)
        move.l %a0,-(%sp)
        move.l %a1,-(%sp)
        move.l %d3,%d0
        andi.l #0xf,%d0
        jsr (part_window).l
        .byte 0x22, 0x48
        adda.l #0x90492,%a0
        .byte 0x30, 0x10
        cmpi.l #0x4d53,%d0
        bne.w .Lfreeze_alt_try_sh
        adda.l #0x90522,%a1
        move.l #0x90,%d1
.Lfreeze_alt_cp_w:
        .byte 0x10, 0x18
        .byte 0x12, 0xc0
        .byte 0x53, 0x81
        bne.w .Lfreeze_alt_cp_w
        bra.w .Lfreeze_alt_done
.Lfreeze_alt_try_sh:
        move.l %d3,%d0
        jsr (part_window).l
        .byte 0x22, 0x48
        adda.l #0x9675c,%a0
        .byte 0x30, 0x10
        cmpi.l #0x4d53,%d0
        bne.w .Lfreeze_alt_done
        adda.l #0x90522,%a1
        move.l #0x90,%d1
.Lfreeze_alt_cp_s:
        .byte 0x10, 0x18
        .byte 0x12, 0xc0
        .byte 0x53, 0x81
        bne.w .Lfreeze_alt_cp_s
.Lfreeze_alt_done:
        move.l (%sp)+,%a1
        move.l (%sp)+,%a0
        move.l (%sp)+,%d1
        move.l (%sp)+,%d0
        rts
