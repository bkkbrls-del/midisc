# midisc technical map (`1.40MIDISC5`)

Facts the shipped patch relies on. Base image: stock **1.40C** MAIN OS
(`BASE = 0x40000400`). All addresses in `tools/midisc/memory_map.py`.

Splash field is ≤10 chars: **`1.40MDISC5`**. Flash filename: **`1.40MIDISC5.bin`**.

---

## MIDI pages and flats

`PAGE_MODE` = `0x460D1684` (u32).  
Flat index used everywhere: **`PAGE_MODE * 6 + encoder`** (encoder 0…5).

Resolver `FUN_40031da4(track, page_kind)` for MIDI tracks (`track ≥ 8`):

| PAGE_MODE | Page | Flats |
|-----------|------|-------|
| 0 | NOTE | 0–5 |
| 1 | LFO | 6–11 |
| **2** | **ARP** | **12–17** |
| 3 | CTRL1 | 18–23 |
| 4 | CTRL2 | 24–29 |

ARP order: TRAN, LEG, MODE, SPD, RNGE, NLEN.  
Stock ARP descriptor counts: LEG=2, MODE=7, SPD=96, RNGE=8 → max values
0–1 / 0–6 / 0–95 / 0–7.

### ARP scene-lock clamp (working)

In `hold.py` `build_scene_lock_clamp` (called after hold delta via `SENT_CLAMP`):

- Gate: **`PAGE_MODE == 2`** (not 0/1 — those are NOTE/LFO)
- `encoder = flat - 12`
- Cap enc 1…4 to LEG/MODE/SPD/RNGE maxes; else 0…127

HW-confirmed on ARP under A-hold.

---

## Working MSC bank

| | |
|--|--|
| Live bank | `MSC = 0x400D6600`, length `16 × 8 × 32` (scene × track × flat) |
| Empty cell | `0xFF` |
| Index | `scene*256 + track*32 + flat` (track 0…7 MIDI) |
| Held scene | `SCENE_HELD = 0x460D169C` |
| MIDI mode | `MIDI_FLAG = 0x80000012` |
| Scene assign in part | `SCENE_ASSIGN = +0x8ED90` from part base |
| Bank pointer | `BANK_PTR = 0x46C82456` |
| Part / track UI | `PART_DISP = 0x100B14CF`, `TRACK_DISP = 0x100B14CC` |

Hold store writes MSC, packs, dirties, forces XF remix, redraws overlay.

---

## Persist across Part Save / reboot (working)

Sparse blob inside the **part window** (not a separate file):

| | |
|--|--|
| Offset from bank+part×`0x18B2` | **`SPARSE_OFF = 0x90522`** |
| Shadow twin | `SHADOW_SPARSE_OFF = 0x967EC` |
| Size | 144 bytes |
| Magic | u16 **`MS` = `0x4D53`** |
| Payload | up to 46 entries of `{u16 flat_or_id, u8 value}` after magic+count |

`build_pack`: MSC → working sparse, then the same durable half stock Part Save
does — memcpy working→shadow→`PART_STAGING` (`0x100AB196`) and set
`PART_SAVED` (`bank+0x9B312`). Sparse-only write was not enough; the full
shadow/staging/`9b312` path is what survives reboot. Pack also refreshes
`PART_PROJECT` (`0x100A4ECE`) so Project Save / Part Paste see current locks.

`build_unpack`: sparse → MSC on apply/reload.

Part Reload uses DRAM **CKPT** (`CLIP+0x200`, `CLIP = 0x460C9A00`) — Part Save
freezes sparse there. After project load (`faf0`), `AFTER_PROJECT_LOAD`
(`0x400622C6`) seeds CKPT from `PART_PROJECT` sparse then unpacks (stock `faf0`
fills CF→bank/`PART_PROJECT`/staging but not DRAM CKPT). Never body-hook
`PROJECT_LOAD` (`0x4000faf0`) or `PROJECT_SAVE` (`0x4000fbb4`).

---

## Code placement (ROM caves on 1.40C)

| Region | Range | Contents |
|--------|-------|----------|
| `SAFE_CAVE` | `0x400D24D0`…`0x400D2CDC` | dirty, clamp, pack, unpack, save, xf_mix, **xf2**, plock |
| `VOICE_RELOAD_CAVE` | `0x400D2E84`…`0x400D2EA0` | after xf_mix: `d2 ← MIDI_VOICE[track×0x44+flat]` |
| `CAVE2` | `0x400D2EE6`…`0x400D3020` | rebuild lock mask |
| `CODE2` | `0x400D6500`…`0x400D6600` | apply wrap, reload UI, bank switch/invalidate, scene-done, write remix |
| `STUB` | `0x400D7600`…`0x400D7C48` | hold A/B, dial, LED addi, pad/press/release, scene UI, morph, **bank_publish** |
| `PROJECT_CAVE` | `0x400E1EC4`…`0x400E2000` | Part Clear midisc wipe + after-project-load (CKPT seed) |
| `MSC` | `0x400D6600` | live 4K bank (zeros in stock) |

Never place code in `CLEAR_CAVE` (`0x400C4302` — stock xref table). xf2 must
stay in `SAFE_CAVE` (moving it to `PROJECT_CAVE` hangs boot).

Cross-cave calls use **sentinel addresses** (`SENT_PACK`, `SENT_UNPACK`,
`SENT_DIRTY`, `SENT_CLAMP`, `SENT_XF_MIX`, `SENT_VOICE_RELOAD`, …) fixed up after
link (`fix_jsr` in `build.py`).

DRAM (not in OS image): scene clipboard `CLIP = 0x460C9A00`, CKPT above it.
Does not use octakit boot temp `0x47fc7410`…`0x47fd910f`.

---

## Hooks that must be patched (working set)

Stock bytes asserted before splice (`build.py`).

| Site | Addr | Role |
|------|------|------|
| `GATE_A` / `GATE_B` | `0x400534CE` / `0x40052ECE` | MIDI hold path → hold stub (else stock audio) |
| `DIAL_HOOK` | `0x4004E348` | dial load reads MSC when scene held |
| `WRITE_HOOK` | `0x4005538A` | MIDI apply → write remix (8 bytes; cont `0x40055392`) |
| `DISP` | `0x40031964` | display/overlay glue |
| `PAD_HOOK` | `0x40031F44` | pads show locks from MSC |
| `PRESS_HOOK` / `RELEASE_HOOK` | `0x400434CA` / `0x40054CB6` | press refresh / release remix |
| `TRACK_GATE` / `PAGE_GATE` | `0x400343BC` / `0x4003445E` | allow MIDI through track/page LED path |
| `TRACK_ADDI` / `PAGE_ADDI` | `0x400343E8` / `0x4003448E` | → `taddi`/`paddi` stubs |
| `GREY_ENTER` | `0x40034754` | **nop** `bne` — MIDI must scan locks |
| `LED_SKIP_B` | `0x4003493E` | **nop** skip |
| `LED_ADDI_A/B` | `0x40034764` / `0x40034950` | jsr stubs that **`rts`** (solid green, not blink) |
| `GREY_CELL` | `0x4004E6EA` | grey cell base for MIDI |
| Morph / XF after | `MORPH_EXIT`, `XF_AFTER1/2`, `XF_PUB*` | morph + post-XF remix |
| Apply / save / reload | `STOCK_APPLY`, `SAVE_UI`, `RELOAD_UI`, … | unpack on apply; pack on save |
| Bank write | `BANK_WR_SWITCH_*`, `BANK_WR_INIT_*` | preserve `d1–d7/a0–a6` around `move.l d0,BANK_PTR` |
| `AFTER_PROJECT_LOAD` | `0x400622C6` | after stock `jsr faf0`: CKPT seed + unpack |

Encoder unlock cave: `0x400C45B0` (press while held clears MSC cell).

---

## Bank register preserve (working)

Stock `move.l d0, (0x46C82456)` at bank switch/init clobbered caller regs and
broke sample load from virgin 1.40C projects.  
`build_bank_switch` / `build_bank_invalidate` / `build_bank_publish` wrap that
store with a ColdFire-safe save/restore (`lea`/`movem`, not `movem` to `-(sp)`).

| Site | Address | Stock context | Cave |
|------|---------|---------------|------|
| A | `0x400622aa` | Guarded; BANK_ID published **after** | pack → publish → unpack |
| B | `0x40087d44` | Unconditional; BANK_ID published **before** | **publish → unpack** (no pack) |

Site B must not pack (durable SAVE mid bank-load → wrong pattern). Always unpack
after publish (wipes MSC).

---

## Full-B CTRL CC lock freeze (working)

Unheld MIDI apply writes behind (`8f162`), then `write_remixed` runs `xf_mix`
into `MIDI_VOICE` only. Stock then `CC_TX` (`0x4009EEC8`) still used dialed
`d2` — at full scene B a B-locked CTRL CC looked locked but still transmitted.

After `xf_mix`, `build_voice_reload_d2` sets `d2` from
`MIDI_VOICE[track×0x44+flat]` so `CC_TX` / SOUND mirrors use the mix. Mid-XF
with empty A still morphs (VOICE is the lerp). Other MIDI pages do not take
`CC_TX`.

`WRITE_HOOK` must cover **8** bytes (`WRITE_CONT = 0x40055392`). Cont
`0x40055390` / LEN 6 landed inside `move.l #0x18b2` immediate.

---

## Solid green LEDs (working)

- Nop `GREY_ENTER` and `LED_SKIP_B` so MIDI lock scan is not skipped
- `LED_ADDI_*` / track/page addi → stubs that **return** (no jump into blink/CONT)

---

## Build / flash reminder

`python tools/build_midisc40.py` produces **your** `1.40MIDISC5.bin` from **your**
1.40C (splash `1.40MDISC5`). Do not redistribute that binary. Flash/recovery:
`docs/FLASHING.md`.
