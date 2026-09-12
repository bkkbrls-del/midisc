| enc_unlock -- midisc cave, emitted from tools/midisc/*.py by tools/gas_port.py.
| DO NOT EDIT BY HAND: regenerate with `python3 tools/gas_port.py`, which also
| proves this file assembles to the bytes the Python encoder produces.
| Cross-cave references are linker symbols (see gas_port.py); everything
| else is the firmware's own address and stays literal.
        .text

        .global unlock
unlock:
        move.l %d0,-(%sp)
        move.l %d1,-(%sp)
        move.l %d2,-(%sp)
        move.l %d3,-(%sp)
        move.l %d5,-(%sp)
        move.l %a0,-(%sp)
        move.l %a1,-(%sp)
        move.l %d4,%d3
        addi.l #0xffffffc8,%d3
        cmpi.l #0x5,%d3
        bhi.w .Lunlock_out
        move.l (0x460d1684).l,%d0
        move.l %d0,%d5
        lsl.l #3,%d5
        add.l %d0,%d0
        sub.l %d0,%d5
        add.l %d3,%d5
        andi.l #0x1f,%d5
        mvz.b (last_part).l,%d0
        mvz.b (0x100b14cf).l,%d1
        .byte 0xb0, 0x81
        beq.w .Lunlock_ul_sync
        jsr (unpack).l
.Lunlock_ul_sync:
        move.l (0x460d169c).l,%d2
        mvz.b (0x100b14cf).l,%d0
        move.l #0x18b2,%d3
        muls.l %d0,%d3
        movea.l (0x46c82456).l,%a0
        adda.l %d3,%a0
        adda.l #0x8ed90,%a0
        cmpi.l #0x1,%d2
        beq.w .Lunlock_sc_a
        mvz.b (1,%a0),%d2
        bra.w .Lunlock_got_sc
.Lunlock_sc_a:
        mvz.b (%a0),%d2
.Lunlock_got_sc:
        cmpi.l #0xff,%d2
        beq.w .Lunlock_out
        andi.l #0xf,%d2
        lsl.l #8,%d2
        mvz.b (0x100b14cc).l,%d0
        andi.l #0x7,%d0
        lsl.l #5,%d0
        add.l %d0,%d2
        add.l %d5,%d2
        movea.l #msc,%a0
        adda.l %d2,%a0
        moveq #-1,%d1
        move.b %d1,(%a0)
        mvz.b (0x100b14cf).l,%d0
        move.b %d0,(last_part).l
        jsr (pack).l
        jsr (dirty).l
        .byte 0x42, 0xb9, 0x46, 0x0c, 0x9e, 0x44
        moveq #-1,%d0
        move.b %d0,(0x460c9eb9).l
        jsr (xf_mix).l
        .byte 0x48, 0x78, 0xff, 0xff
        jsr (0x4004d948).l
        .byte 0x58, 0x8f
.Lunlock_out:
        move.l (%sp)+,%a1
        move.l (%sp)+,%a0
        move.l (%sp)+,%d5
        move.l (%sp)+,%d3
        move.l (%sp)+,%d2
        move.l (%sp)+,%d1
        move.l (%sp)+,%d0
        rts

        .global hook_a
hook_a:
        tst.l (0x80000012).l
        beq.w .Lhook_a_audio
        move.l (0x460d169c).l,%d0
        tst.l %d0
        beq.w .Lhook_a_bail
        jsr (unlock).l
.Lhook_a_bail:
        jmp (0x40054350).l
.Lhook_a_audio:
        jmp (0x40053aa8).l

        .global hook_b
hook_b:
        tst.l (0x80000012).l
        beq.w .Lhook_b_audio
        move.l (0x460d169c).l,%d0
        tst.l %d0
        beq.w .Lhook_b_bail
        jsr (unlock).l
.Lhook_b_bail:
        jmp (0x40054c52).l
.Lhook_b_audio:
        jmp (0x4005439c).l
