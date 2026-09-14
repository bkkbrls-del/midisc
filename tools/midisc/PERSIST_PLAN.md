# Persist investigation (no build) — from MIDISC8 golden

**Base:** `c:\Users\l\Desktop\GOLDEN SUNDAY\1.40MIDISC8.bin` (unpacked OK)  
**Goal:** CC48/55/56 ticks retain **UI + TX** across Project Save + reboot, without YES/USB/scroll bricks.  
**Status:** report only — not built.

## What MIDISC8 already has (keep)

| Item | Detail |
|------|--------|
| UI rows CC48/55/56 | FILTER `@0x400C4302` (240B / 330B, **90B free**) |
| Live bits | DRAM `0x460CA680 / 684 / 688` (CLIP+`0xC80`) — **one long each**, `0`=ON/checked, `1`=OFF |
| Getter | `tst.l` that long (per-bit, **not** shared) — scroll-safe |
| Setter | `andi.l #1` into that long (PERSONALIZE delta ABI) |
| TX gate | jmp `@0x400D65A0`, `tst.l` same DRAM |
| Project load/save | **stock** pea `@0x400877E0` / mvs `@0x400887E2` — no `MIDISC_CC_FILT` |

Session ticks work; reboot clears DRAM → all ON. That is the only gap.

## Yesterday’s brick map (do not repeat)

| Failure | Cause |
|---------|--------|
| YES / USB / project change | Persist **code in ba8 pads / table zero-gaps** (`0x400C14D5`, `0x400EC8BC`, …) |
| Scroll to CC48 | **Shared getters** (`btst.l d2,d1` / `0e81`) in 9c |
| `0x800000D4` / PERSONALIZE A8/D8/DC | Already banned |

Reboot persist **did** work when hooks ran (9) — the problem was **where** the trampoline lived and later the getter change, not the key idea.

## Recommended design (minimal delta on MIDISC8)

**Do not change** MIDISC8 getters / setters / gate / DRAM live model.

**Add only** project-settings key I/O (same pattern as stock AUDIO CC IN):

1. **Key** `MIDISC_CC_FILT=%d` — one byte, bits 0/1/2 = CC48/55/56 (`0`=ON, `1`=OFF), matching the three DRAM longs.
2. **Load trampoline** `@0x400D347E` (81B D-region pad; VOICE/RELOAD class). On hit: unpack byte → `460CA680/684/688`, then stock `LOAD_DONE`. On miss: pea next key → stock continue.
3. **Save trampoline** `@0x400D352D` (66B pad next to it) **or** FILTER tail if short key. Pack three DRAM longs → byte, write key, then stock `move.b 0x8000004A` path.
4. **Hooks** (only these two sites): replace pea `@0x400877E0` and mvs `@0x400887E2` with `jmp` to those trampolines — same ABI as 9 (HW-proven for retain).
5. **Strings** in FILTER free (90B) or with save cave — full key name fits if save is in `352D`; if save stays in FILTER use short key `MCCF` (74B ≤ 90B).

### Why this is the safest of the options that can actually persist

- Live path stays byte-identical to golden 8 → no CC48 scroll regression from getter rewrites.
- Trampolines only in **D-region CODE pads** + FILTER island already used by midisc — not ba8 / table gaps.
- File format matches how Elektron already persists AUDIO CC (text settings key).

### Still must HW-prove (hooks never validated with *only* D-pads)

Order:

1. Scroll MIDI CONTROL through CC48/55/56  
2. Toggle + confirm TX follows  
3. **Project Save** → reboot → UI + TX still match  
4. USB DISK YES, project-change YES  

If (4) bricks again with this cave layout → kill hooks immediately and fall back (below).

## Alternatives (if YES still bricks)

| Approach | Pros | Cons |
|----------|------|------|
| **B. Bank/project binary byte** via existing pack / after_project_load | Never touches settings parser / YES path | Need a stock-safe offset; global MIDI setting in bank is awkward |
| **C. Hook settings fn entry/exit only** | Might avoid mid-chain | Unproven; still on settings path if USB calls it |
| **D. Pack into `0x80000049`** | No new key | Stock `move.b` 0/1 **wipes** the byte — unsafe |

**B** is the fallback if D-pad hooks still upset YES.

## Explicit non-goals for first build

- No shared getters/setters  
- No `0x100B14B5` / `0x80000057` migration (optional later; 8’s DRAM is enough)  
- No caves at `C14D5` / `EC8BC` / `E6E5B` / `C1153`  
- No build until you say go  

## Suggested ship name when approved

`1.40MIDISC8p` / splash `1.40MDIS8p` — MIDISC8 + persist only.
