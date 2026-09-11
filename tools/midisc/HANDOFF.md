# midisc 1.40MIDISC5

**Rebuild:** `python tools/build_midisc40.py` (needs your own 1.40C)  
**Output:** `~/Desktop/1.40MIDISC5.bin` · splash `1.40MDISC5`  
**Syx:** `out/OCTATRACK_1.40MIDISC5.syx`

## Working pieces

| Area | Where |
|------|--------|
| ARP clamp `PAGE_MODE==2`, flat−12 | `hold.py` → `SENT_CLAMP` |
| MSC live bank + hold/dial | `hold.py`, `MSC @ 0x400D6600` |
| Persist sparse `+0x90522` / `MS` + durable save | `parts.py` |
| After-project-load CKPT seed | `parts.py` → `PROJECT_CAVE` |
| Bank Site A pack / Site B publish-only | `parts.py` bank_* → `CODE2` / `STUB` |
| Full-B CC lock → VOICE reload `d2` | `morph.py` → `VOICE_RELOAD_CAVE` |
| Solid green LEDs | nop `GREY_ENTER` / `LED_SKIP_B`; addi → rts stubs |
| XF morph / plock | `morph.py` |
| Hook list + caves | `docs/TECH.md`, `memory_map.py`, `build.py` |

Do not redistribute built images.
