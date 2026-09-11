| safe_cave -- midisc cave, emitted from tools/midisc/*.py by tools/gas_port.py.
| DO NOT EDIT BY HAND: regenerate with `python3 tools/gas_port.py`, which also
| proves this file assembles to the bytes the Python encoder produces.
| Cross-cave references are linker symbols (see gas_port.py); everything
| else is the firmware's own address and stays literal.
        .text

        .global dirty
dirty:
        move.l %d0,-(%sp)
        move.l %d2,-(%sp)
        move.l %a0,-(%sp)
        move.l %a1,-(%sp)
        .byte 0x22, 0x79, 0x46, 0xc8, 0x24, 0x56
        .byte 0x71, 0xb9, 0x10, 0x0b, 0x14, 0xcf
        .byte 0x74, 0x01, 0xe1, 0xaa
        .byte 0x20, 0x7c, 0x00, 0x09, 0x50, 0x48
        .byte 0x10, 0x31, 0x88, 0x00, 0x80, 0x82, 0x13, 0x80, 0x88, 0x00
        .byte 0x10, 0x39, 0x10, 0x0b, 0x14, 0x5e, 0x80, 0x82, 0x13, 0xc0, 0x10, 0x0b, 0x14, 0x5e
        moveq #1,%d0
        movea.l #0x9b332,%a0
        .byte 0x23, 0x80, 0x88, 0x00
        move.l %d0,(0x100f8598).l
        move.l (%sp)+,%a1
        move.l (%sp)+,%a0
        move.l (%sp)+,%d2
        move.l (%sp)+,%d0
        rts

        .global clamp
clamp:
        tst.l %d1
        bpl.w .Lclamp_pos
        moveq #0,%d1
        rts
.Lclamp_pos:
        move.l (0x460d1684).l,%d0
        cmpi.l #0x2,%d0
        bne.w .Lclamp_std
        move.l %d5,%d0
        addi.l #0xfffffff4,%d0
        moveq #1,%d2
        cmpi.l #0x1,%d0
        beq.w .Lclamp_cap
        moveq #6,%d2
        cmpi.l #0x2,%d0
        beq.w .Lclamp_cap
        moveq #95,%d2
        cmpi.l #0x3,%d0
        beq.w .Lclamp_cap
        moveq #7,%d2
        cmpi.l #0x4,%d0
        bne.w .Lclamp_std
.Lclamp_cap:
        .byte 0xb2, 0x82
        bhi.w .Lclamp_clip
        bra.w .Lclamp_ok
.Lclamp_clip:
        move.l %d2,%d1
        bra.w .Lclamp_ok
.Lclamp_std:
        cmpi.l #0x80,%d1
        bcs.w .Lclamp_ok
        moveq #127,%d1
.Lclamp_ok:
        rts

        .global pack
pack:
        mvz.b (last_part).l,%d3
        cmpi.l #0xff,%d3
        beq.w .Lpack_skip
        move.l %d0,-(%sp)
        move.l %d1,-(%sp)
        move.l %d2,-(%sp)
        move.l %d3,-(%sp)
        move.l %d4,-(%sp)
        move.l %d5,-(%sp)
        move.l %a0,-(%sp)
        move.l %a1,-(%sp)
        .byte 0x2f, 0x0a, 0x2f, 0x0b
        andi.l #0xf,%d3
        move.l %d3,%d4
        move.l %d3,%d0
        move.l #0x18b2,%d1
        muls.l %d0,%d1
        move.l %d1,%d5
        movea.l (0x46c82456).l,%a0
        adda.l %d1,%a0
        adda.l #0x90522,%a0
        .byte 0x22, 0x48
        .byte 0x2f, 0x09
        move.l #0x4d53,%d0
        .byte 0x32, 0x80
        .byte 0x42, 0x29, 0x00, 0x02
        .byte 0x41, 0xe9, 0x00, 0x04
        movea.l #msc,%a2
        move.l #0x1000,%d2
        moveq #0,%d3
.Lpack_pk_loop:
        .byte 0x71, 0x9a
        cmpi.l #0xff,%d0
        beq.w .Lpack_pk_next
        cmpi.l #0x2e,%d3
        beq.w .Lpack_pk_done
        move.l #0x1000,%d1
        sub.l %d2,%d1
        .byte 0x30, 0xc1
        .byte 0x10, 0xc0
        addq.l #1,%d3
.Lpack_pk_next:
        .byte 0x53, 0x82
        bne.w .Lpack_pk_loop
.Lpack_pk_done:
        .byte 0x22, 0x5f
        .byte 0x13, 0x43, 0x00, 0x02
        movea.l (0x46c82456).l,%a0
        .byte 0x20, 0x08
        add.l %d5,%d0
        move.l %d0,%d2
        addi.l #0x9504a,%d2
        move.l %d0,%d1
        addi.l #0x8ed80,%d1
        movea.l #0x40020898,%a3
        .byte 0x48, 0x78, 0x18, 0xb2
        .byte 0x2f, 0x01
        .byte 0x2f, 0x02
        .byte 0x4e, 0x93
        .byte 0x4f, 0xef, 0x00, 0x0c
        .byte 0x48, 0x78, 0x18, 0xb2
        .byte 0x2f, 0x02
        move.l #0x100ab196,%d0
        add.l %d5,%d0
        .byte 0x2f, 0x00
        .byte 0x4e, 0x93
        .byte 0x4f, 0xef, 0x00, 0x0c
        .byte 0x48, 0x78, 0x18, 0xb2
        .byte 0x2f, 0x02
        move.l #0x100a4ece,%d0
        add.l %d5,%d0
        .byte 0x2f, 0x00
        .byte 0x4e, 0x93
        .byte 0x4f, 0xef, 0x00, 0x0c
        movea.l (0x46c82456).l,%a0
        adda.l #0x9b312,%a0
        adda.l %d4,%a0
        moveq #1,%d1
        .byte 0x10, 0x81
        .byte 0x26, 0x5f, 0x24, 0x5f
        move.l (%sp)+,%a1
        move.l (%sp)+,%a0
        move.l (%sp)+,%d5
        move.l (%sp)+,%d4
        move.l (%sp)+,%d3
        move.l (%sp)+,%d2
        move.l (%sp)+,%d1
        move.l (%sp)+,%d0
.Lpack_skip:
        rts

        .global unpack
unpack:
        move.l %d0,-(%sp)
        move.l %d1,-(%sp)
        move.l %d2,-(%sp)
        move.l %d3,-(%sp)
        move.l %d4,-(%sp)
        move.l %a0,-(%sp)
        move.l %a1,-(%sp)
        movea.l #msc,%a0
        move.l #0x1000,%d1
.Lunpack_uf:
        .byte 0x10, 0xbc, 0x00, 0xff
        .byte 0x52, 0x88
        .byte 0x53, 0x81
        bne.w .Lunpack_uf
        move.l #0x90522,%d2
        mvz.b (unpack_src).l,%d3
        moveq #0,%d4
        cmpi.l #0xfe,%d3
        bne.w .Lunpack_not_sh
        move.l #0x967ec,%d2
        mvz.b (0x100b14cf).l,%d3
        moveq #1,%d4
        bra.w .Lunpack_got
.Lunpack_not_sh:
        cmpi.l #0xff,%d3
        bne.w .Lunpack_got
        mvz.b (0x100b14cf).l,%d3
.Lunpack_got:
        andi.l #0xf,%d3
        moveq #-1,%d0
        move.b %d0,(unpack_src).l
.Lunpack_try:
        move.l %d3,%d0
        move.l #0x18b2,%d1
        muls.l %d0,%d1
        movea.l (0x46c82456).l,%a0
        adda.l %d1,%a0
        adda.l %d2,%a0
        .byte 0x22, 0x48
        .byte 0x30, 0x11
        cmpi.l #0x4d53,%d0
        beq.w .Lunpack_load
        cmpi.l #0x90522,%d2
        bne.w .Lunpack_hit
        move.l #0x967ec,%d2
        moveq #1,%d4
        bra.w .Lunpack_try
.Lunpack_load:
        mvz.b (2,%a1),%d2
        andi.l #0xff,%d2
        beq.w .Lunpack_maybe_sync
        .byte 0x41, 0xe9, 0x00, 0x04
.Lunpack_uloop:
        .byte 0x30, 0x18
        .byte 0x12, 0x18
        movea.l #msc,%a1
        adda.l %d0,%a1
        .byte 0x12, 0x81
        .byte 0x53, 0x82
        bne.w .Lunpack_uloop
.Lunpack_maybe_sync:
        tst.l %d4
        beq.w .Lunpack_hit
        move.l %d3,%d0
        move.l #0x18b2,%d1
        muls.l %d0,%d1
        movea.l (0x46c82456).l,%a0
        adda.l %d1,%a0
        .byte 0x22, 0x48
        adda.l #0x967ec,%a0
        adda.l #0x90522,%a1
        move.l #0x90,%d2
.Lunpack_cp_sp:
        .byte 0x10, 0x18
        .byte 0x12, 0xc0
        .byte 0x53, 0x82
        bne.w .Lunpack_cp_sp
.Lunpack_hit:
        move.l %d3,%d0
        move.b %d0,(last_part).l
        move.l (%sp)+,%a1
        move.l (%sp)+,%a0
        move.l (%sp)+,%d4
        move.l (%sp)+,%d3
        move.l (%sp)+,%d2
        move.l (%sp)+,%d1
        move.l (%sp)+,%d0
        rts

        .global save
save:
        move.l %d0,-(%sp)
        move.l %d1,-(%sp)
        move.l %d2,-(%sp)
        move.l %a0,-(%sp)
        move.l %a1,-(%sp)
        move.l (24,%sp),%d0
        andi.l #0xf,%d0
        move.l %d0,%d2
        move.l %d2,%d0
        move.l #0x18b2,%d1
        muls.l %d0,%d1
        movea.l (0x46c82456).l,%a0
        adda.l %d1,%a0
        .byte 0x22, 0x48
        adda.l #0x90522,%a0
        .byte 0x30, 0x10
        cmpi.l #0x4d53,%d0
        beq.w .Lsave_ensured
        .byte 0x20, 0x49
        adda.l #0x967ec,%a0
        .byte 0x30, 0x10
        cmpi.l #0x4d53,%d0
        bne.w .Lsave_ensured
        adda.l #0x90522,%a1
        move.l #0x90,%d1
.Lsave_cp_sp:
        .byte 0x10, 0x18
        .byte 0x12, 0xc0
        .byte 0x53, 0x81
        bne.w .Lsave_cp_sp
.Lsave_ensured:
        move.l %d2,%d0
        mvz.b (0x100b14cf).l,%d1
        .byte 0xb0, 0x81
        bne.w .Lsave_ckpt
        move.b %d0,(last_part).l
        jsr (pack).l
.Lsave_ckpt:
        move.l %d2,%d0
        move.l #0x18b2,%d1
        muls.l %d0,%d1
        movea.l (0x46c82456).l,%a0
        adda.l %d1,%a0
        adda.l #0x90522,%a0
        .byte 0x22, 0x48
        move.l %d2,%d0
        move.l #0x90,%d1
        muls.l %d0,%d1
        movea.l #0x460c9c00,%a0
        adda.l %d1,%a0
        move.l #0x90,%d1
.Lsave_cp_ck:
        .byte 0x10, 0x19
        .byte 0x10, 0xc0
        .byte 0x53, 0x81
        bne.w .Lsave_cp_ck
        move.l (%sp)+,%a1
        move.l (%sp)+,%a0
        move.l (%sp)+,%d2
        move.l (%sp)+,%d1
        move.l (%sp)+,%d0
        jmp (0x4004a908).l

        .global rel_after
rel_after:
        .byte 0x2f, 0x00
        move.l %d1,-(%sp)
        move.l %d2,-(%sp)
        move.l %d3,-(%sp)
        move.l %a0,-(%sp)
        move.l %a1,-(%sp)
        move.l (24,%sp),%d3
        andi.l #0xf,%d3
        move.l %d3,%d0
        move.l #0x90,%d1
        muls.l %d0,%d1
        movea.l #0x460c9c00,%a0
        adda.l %d1,%a0
        .byte 0x30, 0x10
        cmpi.l #0x4d53,%d0
        bne.w .Lrel_after_use_shadow
        .byte 0x2f, 0x08
        move.l %d3,%d0
        move.l #0x18b2,%d1
        muls.l %d0,%d1
        movea.l (0x46c82456).l,%a0
        adda.l %d1,%a0
        adda.l #0x90522,%a0
        .byte 0x22, 0x48
        .byte 0x20, 0x5f
        move.l #0x90,%d2
.Lrel_after_ck_to_w:
        .byte 0x10, 0x18
        .byte 0x12, 0xc0
        .byte 0x53, 0x82
        bne.w .Lrel_after_ck_to_w
        move.l %d3,%d0
        move.b %d0,(unpack_src).l
        bra.w .Lrel_after_do_unp
.Lrel_after_use_shadow:
        moveq #-2,%d0
        move.b %d0,(unpack_src).l
.Lrel_after_do_unp:
        move.l (%sp)+,%a1
        move.l (%sp)+,%a0
        move.l (%sp)+,%d3
        move.l (%sp)+,%d2
        move.l (%sp)+,%d1
        jsr (unpack).l
        jsr (pack).l
        jsr (0x400418e0).l
        .byte 0x20, 0x1f
        movea.l (apply_ret).l,%a0
        .byte 0x4e, 0xd0

        .global xf_mix
xf_mix:
        move.l %d0,-(%sp)
        move.l %d1,-(%sp)
        move.l %d2,-(%sp)
        move.l %d3,-(%sp)
        move.l %d4,-(%sp)
        move.l %d5,-(%sp)
        move.l %d6,-(%sp)
        move.l %d7,-(%sp)
        move.l %a0,-(%sp)
        move.l %a1,-(%sp)
        .byte 0x2f, 0x0a
        .byte 0x2f, 0x0b
        movea.l (0x46c82456).l,%a0
        move.l %a0,%d0
        tst.l %d0
        beq.w .Lxf_mix_out
        mvz.b (0x100b14cf).l,%d0
        andi.l #0xf,%d0
        move.l #0x18b2,%d7
        muls.l %d0,%d7
        move.l (0x460d16c8).l,%d5
        andi.l #0x7f,%d5
        .short 0x203c
        .long 0x7f        | move.l #127,%d0 (long form kept)
        sub.l %d5,%d0
        move.l %d0,%d5
        movea.l (0x46c82456).l,%a0
        adda.l %d7,%a0
        adda.l #0x8ed90,%a0
        mvz.b (%a0),%d3
        mvz.b (1,%a0),%d1
        movea.l #0x0,%a2
        cmpi.l #0xff,%d3
        beq.w .Lxf_mix_no_a
        andi.l #0xf,%d3
        lsl.l #8,%d3
        movea.l #msc,%a2
        adda.l %d3,%a2
.Lxf_mix_no_a:
        movea.l #0x0,%a3
        cmpi.l #0xff,%d1
        beq.w .Lxf_mix_no_b
        andi.l #0xf,%d1
        lsl.l #8,%d1
        movea.l #msc,%a3
        adda.l %d1,%a3
.Lxf_mix_no_b:
        .short 0x2c3c
        .long 0x0        | move.l #0,%d6 (long form kept)
.Lxf_mix_tr:
        .short 0x223c
        .long 0x0        | move.l #0,%d1 (long form kept)
.Lxf_mix_pr:
        move.l %d6,%d0
        lsl.l #5,%d0
        add.l %d1,%d0
        move.l %a2,%d4
        tst.l %d4
        beq.w .Lxf_mix_va_ff
        .byte 0x20, 0x4a
        adda.l %d0,%a0
        mvz.b (%a0),%d3
        bra.w .Lxf_mix_va_got
.Lxf_mix_va_ff:
        moveq #-1,%d3
.Lxf_mix_va_got:
        move.l %d6,%d0
        lsl.l #5,%d0
        add.l %d1,%d0
        move.l %a3,%d4
        tst.l %d4
        beq.w .Lxf_mix_vb_ff
        .byte 0x20, 0x4b
        adda.l %d0,%a0
        mvz.b (%a0),%d4
        bra.w .Lxf_mix_vb_got
.Lxf_mix_vb_ff:
        moveq #-1,%d4
.Lxf_mix_vb_got:
        cmpi.l #0xff,%d3
        bne.w .Lxf_mix_a_ok
        cmpi.l #0xff,%d4
        bne.w .Lxf_mix_b_only
        move.l %d6,%d0
        lsl.l #5,%d0
        add.l %d1,%d0
        movea.l (0x46c82456).l,%a0
        adda.l %d7,%a0
        adda.l %d0,%a0
        adda.l #0x8f162,%a0
        mvz.b (%a0),%d0
        bra.w .Lxf_mix_write_ui
.Lxf_mix_b_only:
        move.l %d6,%d0
        lsl.l #5,%d0
        add.l %d1,%d0
        movea.l #0x460c9ec0,%a0
        adda.l %d0,%a0
        mvz.b (%a0),%d3
        cmpi.l #0xff,%d3
        bne.w .Lxf_mix_mix
        move.l %d6,%d0
        lsl.l #5,%d0
        add.l %d1,%d0
        movea.l (0x46c82456).l,%a0
        adda.l %d7,%a0
        adda.l %d0,%a0
        adda.l #0x8f162,%a0
        mvz.b (%a0),%d3
        bra.w .Lxf_mix_mix
.Lxf_mix_a_ok:
        cmpi.l #0xff,%d4
        bne.w .Lxf_mix_mix
        move.l %d6,%d0
        lsl.l #5,%d0
        add.l %d1,%d0
        movea.l #0x460c9ec0,%a0
        adda.l %d0,%a0
        mvz.b (%a0),%d4
        cmpi.l #0xff,%d4
        bne.w .Lxf_mix_mix
        move.l %d6,%d0
        lsl.l #5,%d0
        add.l %d1,%d0
        movea.l (0x46c82456).l,%a0
        adda.l %d7,%a0
        adda.l %d0,%a0
        adda.l #0x8f162,%a0
        mvz.b (%a0),%d4
.Lxf_mix_mix:
        tst.l %d5
        beq.w .Lxf_mix_use_a
        cmpi.l #0x7f,%d5
        bne.w .Lxf_mix_lerp
        move.l %d4,%d0
        bra.w .Lxf_mix_write_morph
.Lxf_mix_use_a:
        move.l %d3,%d0
        bra.w .Lxf_mix_write_morph
.Lxf_mix_lerp:
        move.l %d4,%d0
        sub.l %d3,%d0
        muls.l %d5,%d0
        asr.l #7,%d0
        add.l %d3,%d0
.Lxf_mix_write_ui:
        andi.l #0x7f,%d0
        move.l %d0,%d2
        move.l %d6,%d0
        lsl.l #6,%d0
        move.l %d6,%d3
        lsl.l #2,%d3
        add.l %d3,%d0
        add.l %d1,%d0
        movea.l #0x46c76dc0,%a0
        adda.l %d0,%a0
        move.b %d2,(%a0)
        bra.w .Lxf_mix_ctrl
.Lxf_mix_write_morph:
        andi.l #0x7f,%d0
        move.l %d0,%d2
        move.l %d6,%d0
        lsl.l #6,%d0
        move.l %d6,%d3
        lsl.l #2,%d3
        add.l %d3,%d0
        add.l %d1,%d0
        movea.l #0x46c76dc0,%a0
        adda.l %d0,%a0
        mvz.b (%a0),%d3
        move.b %d2,(%a0)
        .byte 0xb6, 0x82
        beq.w .Lxf_mix_ctrl
        move.l %d1,-(%sp)
        move.l %d2,-(%sp)
        move.l %d5,-(%sp)
        move.l %d6,-(%sp)
        move.l %d7,-(%sp)
        .byte 0x2f, 0x0a, 0x2f, 0x0b
        .byte 0x42, 0xa7
        .byte 0x2f, 0x02
        .byte 0x2f, 0x01
        .byte 0x2f, 0x06
        jsr (0x4009eec8).l
        .byte 0x4f, 0xef, 0x00, 0x10
        .byte 0x26, 0x5f, 0x24, 0x5f
        move.l (%sp)+,%d7
        move.l (%sp)+,%d6
        move.l (%sp)+,%d5
        move.l (%sp)+,%d2
        move.l (%sp)+,%d1
.Lxf_mix_ctrl:
        move.l %a2,%d0
        tst.l %d0
        beq.w .Lxf_mix_lb
        .byte 0x20, 0x4a
        adda.l %d1,%a0
        mvz.b (%a0),%d0
        cmpi.l #0xff,%d0
        bne.w .Lxf_mix_wl
.Lxf_mix_lb:
        move.l %a3,%d0
        tst.l %d0
        beq.w .Lxf_mix_nxc
        .byte 0x20, 0x4b
        adda.l %d1,%a0
        mvz.b (%a0),%d0
        cmpi.l #0xff,%d0
        beq.w .Lxf_mix_nxc
.Lxf_mix_wl:
        move.l %d6,%d0
        lsl.l #5,%d0
        add.l %d1,%d0
        movea.l #0x46c78960,%a0
        adda.l %d0,%a0
        move.b %d2,(%a0)
.Lxf_mix_nxc:
        cmpi.l #0x12,%d1
        bcs.w .Lxf_mix_next
        cmpi.l #0x1e,%d1
        bcc.w .Lxf_mix_next
        move.l %d6,%d0
        lsl.l #2,%d0
        movea.l %d0,%a0
        adda.l #0x800064d0,%a0
        moveq #1,%d0
        lsl.l %d1,%d0
        .byte 0x46, 0x80
        .byte 0xc1, 0xa8, 0x01, 0x7e
.Lxf_mix_next:
        addq.l #1,%d1
        cmpi.l #0x1e,%d1
        bcs.w .Lxf_mix_pr
        addq.l #1,%d6
        cmpi.l #0x8,%d6
        bcs.w .Lxf_mix_tr
.Lxf_mix_out:
        .byte 0x26, 0x5f
        .byte 0x24, 0x5f
        move.l (%sp)+,%a1
        move.l (%sp)+,%a0
        move.l (%sp)+,%d7
        move.l (%sp)+,%d6
        move.l (%sp)+,%d5
        move.l (%sp)+,%d4
        move.l (%sp)+,%d3
        move.l (%sp)+,%d2
        move.l (%sp)+,%d1
        move.l (%sp)+,%d0
        rts

        .global xf2
xf2:
        mvz.b (last_part).l,%d0
        mvz.b (0x100b14cf).l,%d1
        .byte 0xb0, 0x81
        beq.w .Lxf2_ok
        jsr (unpack).l
.Lxf2_ok:
        jsr (xf_mix).l
        .byte 0x71, 0xb9, 0x80, 0x00, 0x00, 0x03
        jmp (0x40062c38).l

        .global plock
plock:
        .byte 0x93, 0xfc, 0x00, 0x00, 0x00, 0x20
        move.l %a1,%d0
        move.l %a5,%d1
        sub.l %d1,%d0
        asr.l #5,%d0
        move.l %d0,%d7
        cmpi.l #0x8,%d7
        bcc.w .Lplock_stock
        .byte 0x2f, 0x09
        move.l %d7,%d0
        lsl.l #5,%d0
        movea.l #0x460c9ec0,%a0
        adda.l %d0,%a0
        .byte 0x22, 0x57
        .byte 0x20, 0xd9
        .byte 0x20, 0xd9
        .byte 0x20, 0xd9
        .byte 0x20, 0xd9
        .byte 0x20, 0xd9
        .byte 0x20, 0xd9
        .byte 0x20, 0xd9
        .byte 0x20, 0xd9
        .byte 0x22, 0x5f
        mvz.b (0x100b14cf).l,%d0
        andi.l #0xf,%d0
        move.l #0x18b2,%d6
        muls.l %d0,%d6
        movea.l (0x46c82456).l,%a0
        adda.l %d6,%a0
        adda.l #0x8ed90,%a0
        mvz.b (%a0),%d3
        mvz.b (1,%a0),%d4
        cmpi.l #0xff,%d3
        bne.w .Lplock_sc
        cmpi.l #0xff,%d4
        beq.w .Lplock_stock
.Lplock_sc:
        jsr (xf_mix).l
        jsr (rebuild).l
.Lplock_stock:
        .byte 0x4c, 0xd7, 0x3c, 0xfc, 0x4f, 0xef, 0x00, 0x28, 0x4e, 0x75
