| stub -- midisc cave, emitted from tools/midisc/*.py by tools/gas_port.py.
| DO NOT EDIT BY HAND: regenerate with `python3 tools/gas_port.py`, which also
| proves this file assembles to the bytes the Python encoder produces.
| Cross-cave references are linker symbols (see gas_port.py); everything
| else is the firmware's own address and stays literal.
        .text

        .global xf1
xf1:
        mvz.b (last_part).l,%d0
        mvz.b (0x100b14cf).l,%d1
        .byte 0xb0, 0x81
        beq.w .Lxf1_ok
        jsr (unpack).l
.Lxf1_ok:
        jsr (xf_mix).l
        .byte 0x71, 0x39, 0x80, 0x00, 0x00, 0x4a
        jmp (0x40061e7e).l

        .global hold_a
hold_a:
        tst.l (0x80000012).l
        beq.w .Lhold_a_audio
        mvz.b (last_part).l,%d0
        mvz.b (0x100b14cf).l,%d1
        .byte 0xb0, 0x81
        beq.w .Lhold_a_hold_sync
        jsr (unpack).l
.Lhold_a_hold_sync:
        move.l (0x460d1684).l,%d0
        move.l %d0,%d5
        lsl.l #3,%d5
        add.l %d0,%d0
        sub.l %d0,%d5
        add.l %d3,%d5
        andi.l #0x1f,%d5
        mvz.b (0x100b14cf).l,%d0
        move.l #0x18b2,%d1
        muls.l %d0,%d1
        movea.l (0x46c82456).l,%a0
        adda.l %d1,%a0
        adda.l #0x8ed90,%a0
        mvz.b (%a0),%d4
        cmpi.l #0xff,%d4
        beq.w .Lhold_a_bail
        andi.l #0xf,%d4
        move.l %d4,%d2
        lsl.l #8,%d2
        mvz.b (0x100b14cc).l,%d0
        andi.l #0x7,%d0
        lsl.l #5,%d0
        add.l %d0,%d2
        add.l %d5,%d2
        movea.l #msc,%a0
        adda.l %d2,%a0
        .byte 0x22, 0x48
        mvz.b (%a0),%d1
        cmpi.l #0xff,%d1
        bne.w .Lhold_a_have_val
        mvz.b (0x100b14cf).l,%d0
        move.l #0x18b2,%d1
        muls.l %d0,%d1
        mvz.b (0x100b14cc).l,%d0
        andi.l #0x7,%d0
        lsl.l #5,%d0
        add.l %d0,%d1
        add.l %d5,%d1
        movea.l (0x46c82456).l,%a0
        adda.l %d1,%a0
        adda.l #0x8f162,%a0
        mvz.b (%a0),%d1
.Lhold_a_have_val:
        add.l %d6,%d1
        jsr (clamp).l
        move.b %d1,(%a1)
        mvz.b (0x100b14cf).l,%d0
        move.b %d0,(last_part).l
        jsr (pack).l
        jsr (dirty).l
        .byte 0x42, 0xb9, 0x46, 0x0c, 0x9e, 0x44
        moveq #-1,%d0
        move.b %d0,(0x460c9eb9).l
        jsr (xf_mix).l
        jmp (0x40053a36).l
.Lhold_a_bail:
        jmp (0x40053a5c).l
.Lhold_a_audio:
        jmp (0x400534d8).l

        .global hold_b
hold_b:
        tst.l (0x80000012).l
        beq.w .Lhold_b_audio
        mvz.b (last_part).l,%d0
        mvz.b (0x100b14cf).l,%d1
        .byte 0xb0, 0x81
        beq.w .Lhold_b_hold_sync
        jsr (unpack).l
.Lhold_b_hold_sync:
        move.l (0x460d1684).l,%d0
        move.l %d0,%d5
        lsl.l #3,%d5
        add.l %d0,%d0
        sub.l %d0,%d5
        add.l %d3,%d5
        andi.l #0x1f,%d5
        mvz.b (0x100b14cf).l,%d0
        move.l #0x18b2,%d1
        muls.l %d0,%d1
        movea.l (0x46c82456).l,%a0
        adda.l %d1,%a0
        adda.l #0x8ed90,%a0
        mvz.b (1,%a0),%d4
        cmpi.l #0xff,%d4
        beq.w .Lhold_b_bail
        andi.l #0xf,%d4
        move.l %d4,%d2
        lsl.l #8,%d2
        mvz.b (0x100b14cc).l,%d0
        andi.l #0x7,%d0
        lsl.l #5,%d0
        add.l %d0,%d2
        add.l %d5,%d2
        movea.l #msc,%a0
        adda.l %d2,%a0
        .byte 0x22, 0x48
        mvz.b (%a0),%d1
        cmpi.l #0xff,%d1
        bne.w .Lhold_b_have_val
        mvz.b (0x100b14cf).l,%d0
        move.l #0x18b2,%d1
        muls.l %d0,%d1
        mvz.b (0x100b14cc).l,%d0
        andi.l #0x7,%d0
        lsl.l #5,%d0
        add.l %d0,%d1
        add.l %d5,%d1
        movea.l (0x46c82456).l,%a0
        adda.l %d1,%a0
        adda.l #0x8f162,%a0
        mvz.b (%a0),%d1
.Lhold_b_have_val:
        add.l %d6,%d1
        jsr (clamp).l
        move.b %d1,(%a1)
        mvz.b (0x100b14cf).l,%d0
        move.b %d0,(last_part).l
        jsr (pack).l
        jsr (dirty).l
        .byte 0x42, 0xb9, 0x46, 0x0c, 0x9e, 0x44
        moveq #-1,%d0
        move.b %d0,(0x460c9eb9).l
        jsr (xf_mix).l
        jmp (0x40053464).l
.Lhold_b_bail:
        jmp (0x4005348c).l
.Lhold_b_audio:
        jmp (0x40052ed8).l

        .global dial
dial:
        move.l (0x460d169c).l,%d2
        tst.l %d2
        beq.w .Ldial_live
        move.l %d1,-(%sp)
        move.l %d2,-(%sp)
        move.l %d3,-(%sp)
        move.l %a0,-(%sp)
        move.l %a1,-(%sp)
        mvz.b (last_part).l,%d0
        mvz.b (0x100b14cf).l,%d1
        .byte 0xb0, 0x81
        beq.w .Ldial_dial_sync
        jsr (unpack).l
.Ldial_dial_sync:
        mvz.b (0x100b14cf).l,%d0
        move.l #0x18b2,%d1
        muls.l %d0,%d1
        movea.l (0x46c82456).l,%a0
        adda.l %d1,%a0
        .byte 0x22, 0x48
        adda.l #0x8ed90,%a0
        cmpi.l #0x1,%d2
        beq.w .Ldial_sel_a
        cmpi.l #0x2,%d2
        bne.w .Ldial_fallback
        mvz.b (1,%a0),%d1
        bra.w .Ldial_got_scene
.Ldial_sel_a:
        mvz.b (%a0),%d1
.Ldial_got_scene:
        cmpi.l #0xff,%d1
        beq.w .Ldial_fallback
        andi.l #0xf,%d1
        lsl.l #8,%d1
        movea.l #msc,%a0
        .byte 0x20, 0x08
        add.l %d1,%d0
        mvz.b (0x100b14cc).l,%d3
        andi.l #0x7,%d3
        lsl.l #5,%d3
        add.l %d3,%d0
        move.l (0x460d1684).l,%d2
        move.l %d2,%d1
        lsl.l #3,%d1
        add.l %d2,%d2
        sub.l %d2,%d1
        add.l %d1,%d0
        .byte 0xd0, 0x8c
        .byte 0x20, 0x40
        .byte 0x71, 0x10
        cmpi.l #0xff,%d0
        beq.w .Ldial_fallback
        cmpi.l #0x80,%d0
        bcc.w .Ldial_fallback
        moveq #1,%d1
        or.l %d1,%d5
        move.l (%sp)+,%a1
        move.l (%sp)+,%a0
        move.l (%sp)+,%d3
        move.l (%sp)+,%d2
        move.l (%sp)+,%d1
        jmp (0x4004e382).l
.Ldial_fallback:
        move.l (%sp)+,%a1
        move.l (%sp)+,%a0
        move.l (%sp)+,%d3
        move.l (%sp)+,%d2
        move.l (%sp)+,%d1
.Ldial_live:
        .byte 0x71, 0xb9, 0x10, 0x0b, 0x14, 0xcc, 0x24, 0x39, 0x46, 0x0d, 0x16, 0x84, 0x73, 0xb9, 0x10, 0x0b, 0x14, 0xcf, 0xeb, 0x88, 0x36, 0x3c, 0x18, 0xb2, 0x4c, 0x03, 0x18, 0x00, 0xd0, 0x81, 0x22, 0x02, 0xe7, 0x89, 0xd4, 0x82, 0x92, 0x82, 0xd0, 0x81, 0xd0, 0xb9, 0x46, 0xc8, 0x24, 0x56, 0xd0, 0x8c, 0x20, 0x40, 0xd1, 0xfc, 0x00, 0x08, 0xf1, 0x62, 0x71, 0x90
        jmp (0x4004e382).l

        .global taddi
taddi:
        tst.l (0x80000012).l
        beq.w .Ltaddi_aud
        move.l %d1,-(%sp)
        move.l %d2,-(%sp)
        mvz.b (0x100b14cf).l,%d1
        move.l #0x18b2,%d2
        muls.l %d1,%d2
        sub.l %d2,%d0
        move.l (0x46c82456).l,%d1
        sub.l %d1,%d0
        addi.l #msc,%d0
        move.l (%sp)+,%d2
        move.l (%sp)+,%d1
        rts
.Ltaddi_aud:
        addi.l #0x8f3e2,%d0
        rts

        .global paddi
paddi:
        tst.l (0x80000012).l
        beq.w .Lpaddi_aud
        move.l %d0,-(%sp)
        move.l %d2,-(%sp)
        mvz.b (0x100b14cf).l,%d0
        move.l #0x18b2,%d2
        muls.l %d0,%d2
        sub.l %d2,%d1
        move.l (0x46c82456).l,%d0
        sub.l %d0,%d1
        addi.l #msc,%d1
        move.l (%sp)+,%d2
        move.l (%sp)+,%d0
        rts
.Lpaddi_aud:
        addi.l #0x8f3e2,%d1
        rts

        .global pad
pad:
        .byte 0x4f, 0xef, 0xff, 0xe4
        .byte 0x48, 0xd7, 0x04, 0xfc
        mvz.b (last_part).l,%d0
        mvz.b (0x100b14cf).l,%d1
        .byte 0xb0, 0x81
        beq.w .Lpad_pad_sync
        jsr (unpack).l
.Lpad_pad_sync:
        move.l (32,%sp),%d2
        move.l %d2,%d0
        andi.l #0xf,%d0
        lsl.l #8,%d0
        movea.l #msc,%a0
        adda.l %d0,%a0
        move.l #0x100,%d1
.Lpad_loop:
        mvz.b (%a0),%d0
        cmpi.l #0xff,%d0
        bne.w .Lpad_hit
        .byte 0x52, 0x88
        .byte 0x53, 0x81
        bne.w .Lpad_loop
        move.l (32,%sp),%d0
        jmp (0x40031f4c).l
.Lpad_hit:
        moveq #1,%d0
        .byte 0x4c, 0xd7, 0x04, 0xfc
        .byte 0x4f, 0xef, 0x00, 0x1c
        rts

        .global press
press:
        jsr (0x400418e0).l
        tst.l (0x80000012).l
        beq.w .Lpress_done
        mvz.b (last_part).l,%d0
        mvz.b (0x100b14cf).l,%d1
        .byte 0xb0, 0x81
        beq.w .Lpress_press_sync
        jsr (unpack).l
.Lpress_press_sync:
        .byte 0x48, 0x78, 0xff, 0xff
        jsr (0x4004d948).l
        .byte 0x58, 0x8f
.Lpress_done:
        .byte 0x24, 0x1f
        jmp (0x4007e8d8).l

        .global release
release:
        .byte 0x42, 0xb9, 0x46, 0x0d, 0x16, 0x94
        .byte 0x42, 0xb9, 0x46, 0x0d, 0x16, 0x9c
        .byte 0x48, 0x78, 0xff, 0xff
        jsr (0x4004d948).l
        jsr (0x400418e0).l
        .byte 0x50, 0x8f
        jmp (0x4007cf28).l

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

        .global clr_sc
clr_sc:
        jsr (unpack).l
        move.l %d0,-(%sp)
        move.l %d1,-(%sp)
        move.l %d2,-(%sp)
        move.l %a0,-(%sp)
        move.l (20,%sp),%d0
        andi.l #0xf,%d0
        lsl.l #8,%d0
        movea.l #msc,%a0
        adda.l %d0,%a0
        move.l #0x100,%d1
.Lclr_sc_ff:
        .byte 0x10, 0xbc, 0x00, 0xff
        .byte 0x52, 0x88
        .byte 0x53, 0x81
        bne.w .Lclr_sc_ff
        mvz.b (0x100b14cf).l,%d2
        andi.l #0xf,%d2
        move.l %d2,%d0
        move.l #0x18b2,%d1
        muls.l %d0,%d1
        movea.l (0x46c82456).l,%a0
        adda.l %d1,%a0
        adda.l #0x90522,%a0
        .byte 0x42, 0x50
        movea.l (0x46c82456).l,%a0
        adda.l %d1,%a0
        adda.l #0x967ec,%a0
        .byte 0x42, 0x50
        move.l (%sp)+,%a0
        move.l (%sp)+,%d2
        move.l (%sp)+,%d1
        move.l (%sp)+,%d0
        mvz.b (0x100b14cf).l,%d0
        move.b %d0,(last_part).l
        jsr (pack).l
        jsr (dirty).l
        .byte 0x42, 0xb9, 0x46, 0x0c, 0x9e, 0x44
        moveq #-1,%d0
        move.b %d0,(0x460c9eb9).l
        jsr (xf_mix).l
        jmp (0x40038c30).l

        .global cpy_sc
cpy_sc:
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
        movea.l #0x460c9a00,%a1
        move.l #0x100,%d1
.Lcpy_sc_cp:
        .byte 0x10, 0x18
        .byte 0x12, 0xc0
        .byte 0x53, 0x81
        bne.w .Lcpy_sc_cp
        move.l (%sp)+,%a1
        move.l (%sp)+,%a0
        move.l (%sp)+,%d1
        move.l (%sp)+,%d0
        jmp (0x400274cc).l

        .global morph
morph:
        mvz.b (last_part).l,%d0
        mvz.b (0x100b14cf).l,%d1
        .byte 0xb0, 0x81
        beq.w .Lmorph_go
        jsr (unpack).l
.Lmorph_go:
        jmp (0x4003577c).l

        .global bank_pub
bank_pub:
        .byte 0x4f, 0xef, 0xff, 0xc4
        .byte 0x48, 0xd7, 0x7f, 0xfe
        move.l %d0,(0x46c82456).l
        jsr (unpack).l
        .byte 0x4c, 0xd7, 0x7f, 0xfe
        .byte 0x4f, 0xef, 0x00, 0x3c
        rts
