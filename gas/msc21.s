| MIDISC2.2 glue: playback follow + KITS msc_follow.
| Exact MIDISC4.0 engine (midisc21). Do not edit by hand.


        .text
        .globl  engine_follow, msc_follow

        .set    PLAY_BANK, msc21_b+(0x400d6d60-0x400d24d0)
        .set    PLAY_PART, msc21_b+(0x400d6d64-0x400d24d0)
        .set    XF_CONTEXT_VALID, msc21_b+(0x400d68b8-0x400d24d0)

| 0x400a4ba0: while playing, his play bank/part are the engine latch
| 0x80001828/29, not the pattern's Part; then his playback_step.
engine_follow:
        lea     %sp@(-12),%sp
        moveml  %d0-%d2,%sp@
        moveq   #1,%d0
        cmpl    0x800065b8,%d0
        bne.s   9f
        moveq   #0,%d0
        moveb   0x80001828,%d0
        cmpil   #15,%d0
        bhi.s   9f
        moveq   #0,%d1
        moveb   0x80001829,%d1
        cmpil   #3,%d1
        bhi.s   9f
        movel   #0x9b340,%d2
        mulsl   %d2,%d0
        addil   #0x400e21e0,%d0
        cmpl    PLAY_BANK,%d0
        bne.s   1f
        cmpl    PLAY_PART,%d1
        beq.s   9f
1:      movel   %d0,PLAY_BANK
        movel   %d1,PLAY_PART
        clrl    XF_CONTEXT_VALID
9:      moveml  %sp@,%d0-%d2
        lea     %sp@(12),%sp
        jmp     playback_step

| KITS, at the moment an engine takes the switched Part (d0 = Part 0..3,
| d1 = bank 0..15; registers kept): his play bank/part follow it there,
| and his next playback_step rebuilds the scenes -- not at the sequencer's
| pattern commit a step earlier (his 8.20 sync, dropped: it played the old
| pattern's last step with the new Part's scenes).
msc_follow:
        lea     %sp@(-12),%sp
        moveml  %d0-%d2,%sp@
        cmpil   #3,%d0
        bhi.s   9f
        cmpil   #15,%d1
        bhi.s   9f
        movel   #0x9b340,%d2
        mulsl   %d2,%d1
        addil   #0x400e21e0,%d1
        cmpl    PLAY_BANK,%d1
        bne.s   1f
        cmpl    PLAY_PART,%d0
        beq.s   9f
1:      movel   %d1,PLAY_BANK
        movel   %d0,PLAY_PART
        clrl    XF_CONTEXT_VALID
9:      moveml  %sp@,%d0-%d2
        lea     %sp@(12),%sp
        rts
