| seam -- midisc cave, emitted from tools/midisc/*.py by tools/gas_port.py.
| DO NOT EDIT BY HAND: regenerate with `python3 tools/gas_port.py`, which also
| proves this file assembles to the bytes the Python encoder produces.
| Cross-cave references are linker symbols (see gas_port.py); everything
| else is the firmware's own address and stays literal.
        .text

        .global part_window
part_window:
        andi.l #0xff,%d3
        move.l %d3,%d0
        move.l #0x18b2,%d1
        muls.l %d0,%d1
        movea.l (0x46c82456).l,%a0
        adda.l %d1,%a0
        rts
