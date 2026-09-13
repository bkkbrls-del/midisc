| code2 -- midisc cave, emitted from tools/midisc/*.py by tools/gas_port.py.
| DO NOT EDIT BY HAND: regenerate with `python3 tools/gas_port.py`, which also
| proves this file assembles to the bytes the Python encoder produces.
| Cross-cave references are linker symbols (see gas_port.py); everything
| else is the firmware's own address and stays literal.
        .text

        .global after
after:
        mvz.b (0x80001829).l,%d0
        move.b %d0,(unpack_src).l
        jsr (unpack).l
        movea.l (apply_ret).l,%a0
        .byte 0x4e, 0xd0

        .global apply
apply:
        .byte 0x20, 0x17
        move.l %d0,(apply_ret).l
        move.l #after,%d0
        .byte 0x2e, 0x80
        jsr (pack).l
        .byte 0x4f, 0xef, 0xff, 0x98
        .byte 0x48, 0xd7, 0x7c, 0xfc
        jmp (0x4000909c).l

        .global reload
reload:
        .byte 0x20, 0x17
        move.l %d0,(apply_ret).l
        move.l #rel_after,%d0
        .byte 0x2e, 0x80
        jmp (0x4004aab4).l

        .global scene_done
scene_done:
        mvz.b (last_part).l,%d0
        mvz.b (0x100b14cf).l,%d1
        .byte 0xb0, 0x81
        beq.w .Lscene_done_ok
        jsr (unpack).l
.Lscene_done_ok:
        .byte 0x42, 0xb9, 0x46, 0x0c, 0xa5, 0x04
        moveq #-1,%d0
        move.b %d0,(0x460ca579).l
        jsr (xf_mix).l
        jmp (0x4007e8d8).l

        .global write_mix
write_mix:
        .byte 0x1a, 0x82, 0x22, 0x3c, 0x00, 0x00, 0x18, 0xb2
        jsr (xf_mix).l
        jsr (voice_rel).l
        jmp (0x40055392).l

        .global cc_gate
cc_gate:
        cmpi.l #0x30,%d3
        beq.w .Lcc_gate_c48
        cmpi.l #0x37,%d3
        beq.w .Lcc_gate_c55
        cmpi.l #0x38,%d3
        beq.w .Lcc_gate_c56
.Lcc_gate_pass:
        moveq #8,%d0
        .byte 0xb0, 0x81
        beq.w .Lcc_gate_eq8
        jmp (0x40033ea4).l
.Lcc_gate_eq8:
        jmp (0x40033e60).l
.Lcc_gate_c48:
        tst.l (0x460ca680).l
        beq.w .Lcc_gate_pass
        bra.w .Lcc_gate_block
.Lcc_gate_c55:
        tst.l (0x460ca684).l
        beq.w .Lcc_gate_pass
        bra.w .Lcc_gate_block
.Lcc_gate_c56:
        tst.l (0x460ca688).l
        beq.w .Lcc_gate_pass
.Lcc_gate_block:
        jmp (0x40033f24).l
