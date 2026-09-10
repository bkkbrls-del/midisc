# Ghidra findings — MIDI scenes like audio (2026-09-05)

**Projects**
- Your GUI project `C:\Users\l\octatrack re` was **empty** (no imported program) and **locked** by Ghidra.
- Headless twin used for this dump: `C:\Users\l\Desktop\octaHack\ghidra_projects\ot_mainos`
- Full decomp: `docs/ot_scene_ghidra_dump.txt` (also Desktop copy)
- Script: `tools/ghidra_scripts/DumpOtScenePath.java`

Language: `68000:BE:32:Coldfire`, MAIN OS @ `0x40000400`.

---

## What audio does (Ghidra-confirmed)

### Hold + turn (`AUDIO_SCENE_HOLD_EDIT` @ `0x40053498`)

```c
if (MIDI_FLAG) return;                    // stock: MIDI never enters

scene = bank[pat].8ed90;                  // or B via other path
flat  = page*6 + encoder;

// read-modify-write scene cell
cell = bank + pat*0x18b2 + (scene*8 + track)*0x20 + flat + 0x8f3e2;
*cell = new_value;

// working mirror
*(… + 0x100a5530 + …) = new_value;

// optional live audio mirror if this pattern/track is active

_DAT_460d1694 = 1;                        // scene-edit UI mode
_DAT_460d1698 = 1;
func_0x4004d948(0xffffffff);              // full overlay refresh (grey from 8f3e2)
```

### Grey while held (`UI_OVERLAY_REFRESH` @ `0x4004D948`)

When `1694 != 0`, dial grey value is read from **`8f3e2`** (scene cell), not live:

```c
scene = (1694==1) ? 8ed90 : 8ed91;
base  = bank + pat*18b2 + (scene*8 + track)*0x20;
value = *(base + flat + 0x8f3e2);         // <-- audio scene store
```

So audio grey is **not magic** — it is “set edit flag → refresh → read scene store.”

### Scene pads 1–16 (`SCENE_PAD_HAS_LOCKS` @ `0x40031F44`)

For scene `param_1`, scan all 8 tracks × flats in `8f3e2` (and level `903e2`); any byte `!= 0xFF` → green.  
`SCENE_PAD_PAINT` @ `0x40034A44` calls that for scenes 0..15, then marks current A/B red from `8ed90`/`8ed91`.

### Scene apply / morph

- `SCENE_APPLY_COPY` @ `0x400274D0`: copy `8f3e2` → runtime `0x460C8122` for tracks **0..7** only.
- `XF_MORPH_SCENES` @ `0x4003F1B4`: lerp A/B pointers into `8f3e2`, tracks 0..7.

### Unheld MIDI apply (`PARAM_APPLY_UNHELD` @ `0x40055008`)

When `MIDI_FLAG`: write live `8f162` (+ `100a52b0`), fire CC helpers (`9eec8` / `9da20`), then **`4d948`**.  
Forcing `55008` while held already ends in one `4d948` — nesting a second (OTMIDI1.11) hangs.

---

## Why MIDI “CC10” hit delay mix

CTRL2 flats 24–29 ≡ FX2 flats. Dual-write into `8f3e2` with `track&7` aliases MIDI T1 → audio T1.  
Morph/apply then push those cells into audio. **Private bank is mandatory.**

Also: `4d948` hold-grey **reads `8f3e2`**. Dual-write made greys appear while poisoning audio — that is the coupling.

---

## Exact MIDI mirror (architecture)

| Audio | MIDI must do |
|-------|----------------|
| Editor `53498` | Keep force `55008` (stock MIDI live + CC TX) |
| Store `8f3e2` | Store **`MIDI_SCENES`** only (1.14) — never `8f3e2` |
| Mirror `100a5530` | Already via `55008` → `8f162` / `100a52b0` |
| Set `1694`/`1698` | **Do this** after MIDI lock write (audio does) |
| Grey via `4d948`←`8f3e2` | Patch that read to **`MIDI_SCENES` when MIDI_FLAG** (stronger than dial-only hook) |
| Pad scan `31F44` | OR-scan `MIDI_SCENES` (same `!=0xFF` test) |
| Apply `274D0` | On assign: copy `MIDI_SCENES[scene][track][*]` → `8f162` **before** stock refresh |
| XF morph | Later: lerp private bank → MIDI live / CC (not XF_PUB jsr until bisect) |

### Lag

Audio laglessness = one `4d948` per detent after store, with `1694` set so grey reads scene cells.  
MIDI should do the **same shape**: store private → set `1694`/`1698` → allow the **single** trailing `4d948` inside `55008`.  
Never add another `4d948` from the write hook. If still laggy, patch `4d948`’s MIDI+`1694` path to read private bank (avoid thrashing empty/`FF` audio cells).

---

## Build order (when approved)

1. **1.15a** — `31F44`: OR `MIDI_SCENES` → green pads  
2. **1.15b** — after lock write: set `1694`/`1698`; ensure `4d948` scene-edit read uses private bank when MIDI  
3. **1.15c** — assign-path recall: private → `8f162` before stock `4d948`  

Rescue: `OTMIDI1.10.bin`. No XF_PUB / no post-`7cf28` hooks.
