# MIDI own scene path (RE) — parallel to audio, no audio conflict

**Date:** 2026-09-05  
**Rule:** MIDI scenes get the *same shape* as audio (store a value → apply grey), on **MIDI-only** cells and the **MIDI** dial branch. Never write audio `8f3e2`.

---

## 1. Audio template (stock)

| Step | What | Where |
|------|------|--------|
| **Entry** | Hold A/B encoder | A=`53498`, B=`52E98` |
| **Store** | Scene cell only | `bank + idx×0x18b2 + (scene×8+track)×32 + flat + **0x8f3e2**` |
| **Live** | Untouched | audio base params stay pre-hold |
| **Arm grey** | Edit flags | `1694=1`, `1698=1` |
| **Paint** | Overlay refresh | `jsr 4d948` |
| **Grey read** | Scene cell → dial | inside `4d948` **audio** branch @ **`4E6EA`**: `adda #8f3e2` → if `≠0xFF` then `d5\|=1` |
| **Release** | Clear hold | dials read live again (unchanged) |
| **Lifecycle** | Part | clear / part save / part reload see `8f3e2` |

Unlocked sentinel: **`0xFF`**.

---

## 2. MIDI parallel (required)

Same steps, **different store + different grey read**. No shared cells with audio.

| Step | Audio | MIDI (own path) |
|------|-------|-----------------|
| **Entry** | body of `53498` / `52E98` | Same editors, but today **`534CE` / `52ECE`** empty-return on `MIDI_FLAG` — replace with MIDI store, **not** `55008` |
| **Store** | `+0x8f3e2` | **Own bank:** `MSC[scene][track][flat]`, `0xFF`=unlocked |
| **Live** | untouched | **`8f162` untouched** while held |
| **Arm grey** | `1694` / `1698` | **Same flags** (shared UI mode is fine) |
| **Paint** | `4d948` | Same one `4d948` at editor tail |
| **Grey read** | `4E6EA` → `8f3e2` | **`4E348`** (MIDI dial load in `4d948`) → read **MSC**, then `d5\|=1` + draw lock value |
| **Release** | live restored visually | live never written → pre-hold position |
| **Apply later** | assign/XF → runtime | assign/XF → copy MSC → `8f162` / CC (separate step) |

### Why two grey sites

At `4d948` / `0x4004E1E0`:

```
tst.l MIDI_FLAG
beq   AUDIO_DIALS   ; … includes 4E6EA (8f3e2)
; else MIDI_DIALS   ; … live load at 4E348 (8f162) — never hits 4E6EA
```

Remapping `4E6EA` alone does **nothing** for MIDI. Grey for MIDI must be taught at **`4E348`**.

### Indexing (same shape as audio, own base)

```
cell = MSC + scene×256 + track×32 + flat
     // track 0..7 = MIDI T1..T8
     // flat = page×6 + slot (CTRL1 18–23, CTRL2 24–29, …)
```

Do **not** `track&7` into `8f3e2` — that is the audio-conflict bug.

---

## 3. Store placement (RE status)

| Candidate | Pros | Cons |
|-----------|------|------|
| **RAM MSC @ `0x400D6600`** (16×8×32=4096, cave) | No audio conflict; fits; already used in 1.14+ | Not in part → clear/save/part switch ignore it |
| **Part tail ~464 B** | Survives with part | Too small for flat 4096; needs sparse format + serializer |
| **Audio `8f3e2`** | Stock clear/grey/pads | **Forbidden** — overwrites audio / delay morph |

**Behaviour-first (flash when ready):** MSC in cave + own grey at `4E348` + hold entry at `534CE`/`52ECE` (scene-only write).  
**Part persistence:** later — sparse list in part tail or teach serializer; hook clear to wipe MSC for active part until then.

---

## 4. Hook map (when building the real fix)

```
534CE / 52ECE   MIDI+held → write MSC[scene][track][flat]; set 1694/1698;
                fall into stock tail (4d948) OR jmp that tail
                NEVER jmp 55008

4E348           if 1694≠0 (or SCENE_HELD): v=MSC[…]; if v≠FF: d5|=1; draw v
                else stock load 8f162

31964           must be STOCK (no force 55008)

8f3e2 / 4E6EA   never patched for MIDI writes
```

---

## 5. One-liner

**Audio = store in `8f3e2` + grey at `4E6EA`. MIDI = store in its own MSC + grey at `4E348`, entered by fixing the MIDI bail in `53498`/`52E98` — same behaviour, zero audio cells.**
