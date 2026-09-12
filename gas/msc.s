| MSC -- 16 scenes x 8 tracks x 32 flat locks, one byte each; 0xff = no lock.
| Placed by the linker; every cave reaches it through the `msc` symbol.
        .text
        .global msc
msc:    .fill 4096,1,0xff
