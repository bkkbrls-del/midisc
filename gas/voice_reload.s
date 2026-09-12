| voice_reload -- midisc cave, emitted from tools/midisc/*.py by tools/gas_port.py.
| DO NOT EDIT BY HAND: regenerate with `python3 tools/gas_port.py`, which also
| proves this file assembles to the bytes the Python encoder produces.
| Cross-cave references are linker symbols (see gas_port.py); everything
| else is the firmware's own address and stays literal.
        .text

        .global voice_rel
voice_rel:
        moveq #68,%d0
        muls.l %d4,%d0
        add.l %d6,%d0
        movea.l #0x46c76dc0,%a0
        adda.l %d0,%a0
        mvz.b (%a0),%d2
        rts
