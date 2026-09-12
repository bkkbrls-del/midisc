| The four state words build.py used to keep just past the STUB.
        .text
        .global last_part, unpack_src, last_bank, apply_ret
last_part:  .byte 0xff
unpack_src: .byte 0xff
last_bank:  .byte 0xff
            .byte 0
apply_ret:  .long 0
