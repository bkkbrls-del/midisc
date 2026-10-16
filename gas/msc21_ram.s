| MIDISC2.2 private RAM (12 arena pages). Linker-owned.
| Exact MIDISC4.0 engine (midisc21).

        .text
        .balign 16
        .globl msc21_ram
msc21_ram:
        .fill 4096,1,0xff
        .fill 69632,1,0
