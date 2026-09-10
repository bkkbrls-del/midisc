# Proper audio-style MIDI scene store + grey (no step-lock workaround)

**Date:** 2026-09-05  
**Baseline working bin:** `Desktop/midi scenes/grey scene locks.bin` (`1.40OTMIDI`)  
**Symptom clarified:** A/B locks **do store**; greys often only appear after **reselecting** the scene. Not encoder lag.

---

## 1. What your working bin actually does

Cave disasm shows it is the early dual-write + dial-hook build:

| Hook | Behavior |
|------|----------|
| `31964` | MIDI ∧ held → force `55008` (knobs move) |
| `5538A` | Live write + **dual-write `8f3e2`** (`track&7`) |
| `4E348` | If `SCENE_HELD`: read **`8f3e2`**, `d5\|=1`, draw lock value |
| Track/page | Jump into **audio** indicator bodies |
| `GREY_ENTER` | **nop** |
| `4E6EA` | **stock** (never used on MIDI — see below) |
| `1694` | **never set** |
| `4d948` | **not called from write** (only whatever `55008` does at end) |

So: **store works** (into shared audio scene RAM). **Grey is a dial hack** at the MIDI live-load site (`4E348`), gated on `SCENE_HELD` — same *shape* as step-lock grey (`d5\|=1` + substitute value), not audio’s scene-edit path.

That is why **reselecting A/B** makes greys appear: assign runs a full overlay rebuild; dials redraw and the hack finally paints. During the turn, nothing sets audio’s edit flags, so paint is inconsistent.

Also: writing `8f3e2` with `track&7` is why CTRL flats can move **audio delay** (CTRL2 ≡ FX2 flats).

---

## 2. How audio *really* stores and greys (Ghidra + stock)

### Store — `AUDIO_SCENE_HOLD_EDIT` @ `0x40053498`

```
if (MIDI_FLAG) return;          // MIDI never enters this editor

write cell:
  bank + pat*0x18b2 + (scene*8 + track)*0x20 + flat + 0x8F3E2

mirror working copy @ 0x100A5530 …
optional live audio mirror if active pattern

_DAT_460D1694 = 1;              // scene-edit UI mode (B alt uses 2)
_DAT_460D1698 = 1;
jsr 0x4004D948(0xFFFFFFFF);     // overlay refresh
jmp 0x4007CF28;
```

### Grey — inside `0x4004D948`, **audio dial branch only**

At `0x4004E1E0`:

```
tst.l MIDI_FLAG
beq   AUDIO_DIALS          ; → 0x4004E4C6 … includes 4E6EA
; else MIDI_DIALS          ; → 0x4004E1EA … never hits 4E6EA
```

**Audio** (`4E4C6`…): when `1694 != 0`, load dial value from **`8f3e2`** @ `0x4004E6EA`, then `d5\|=1` if locked (`!= 0xFF`).

**MIDI** (`4E1EA`…): dial value load is @ `0x4004E348` → always **`8f162` live** (or step-lock table if `173a`). **No scene-cell read exists on the MIDI branch.**

So: audio grey = `1694` + refresh + read **scene store**.  
MIDI stock has **no equivalent** — that is the hole, not a missing nop.

---

## 3. Proper MIDI path (mirror audio logic, not step-locks)

### A. Store (wire to MIDI params later)

```
cell = MIDI_SCENES + scene*256 + track*32 + flat
     // NOT 8f3e2
*cell = value
// live already updated by 55008 → 8f162 (+ CC TX)
```

Same indexing audio uses (`scene*256 + track*32 + flat`), private bank so CTRL≠delay.

### B. Arm the same edit flags audio uses

After a successful lock write (held A/B, assigned scene):

```
1694 = 1 if A held, 2 if B held    // selects 8ed90 vs 8ed91 in audio logic
1698 = 1
```

Do this **before** the `4d948` that already runs at the end of `55008`.  
Do **not** add a second nested `jsr 4d948` from the write hook (1.11 hang).

### C. Grey on the **MIDI dial branch** (this is the real fix)

Because MIDI never reaches `4E6EA`, patch the **MIDI** value load @ `0x4004E348`:

```
if (1694 != 0) {                    // audio-style edit mode — NOT “if SCENE_HELD” alone
  scene = (1694==1) ? assignA : assignB;
  v = MIDI_SCENES[scene][track][page*6+slot];
  if (v != 0xFF) { d5 |= 1; draw v; return; }   // grey + lock value
}
// else stock: load live 8f162
```

That is the **same policy** as audio’s `4E6EA` block, relocated to the branch MIDI actually executes.

| Wrong (workaround) | Right (audio policy) |
|--------------------|----------------------|
| Gate on `SCENE_HELD` only | Gate on **`1694`** (scene-edit mode) |
| Read `8f3e2` | Read **`MIDI_SCENES`** |
| Hope reselect redraws | Trailing `4d948` from `55008` paints **immediately** |
| Dual-write audio cells | Private bank only |

### D. Do not

- Nop `GREY_ENTER` / jump MIDI into audio indicator bodies (1.13 hang + wrong LEDs)
- Dual-write `8f3e2`
- Nest extra `4d948` / `34350` from encoder write
- Expect `4E6EA` remaps alone to work on MIDI (path never runs)

---

## 4. Why repress was needed + how this removes it

```
hold+turn today (working bin):
  write 8f3e2 + move live
  1694 stays 0
  MIDI dials still mostly show live until a heavy redraw

reselect scene:
  assign path → full 4d948 → dials redraw → SCENE_HELD dial hack paints grey
```

```
proper:
  write MIDI_SCENES + move live
  set 1694/1698
  55008’s existing 4d948 → MIDI dial path sees 1694 → reads MIDI_SCENES → greys now
```

---

## 5. Next: wire locks to MIDI params (after grey path is right)

Priority order (audio does this with `8f3e2` → live):

1. **Hold edit** — done via `55008` + private store + flags + MIDI-branch grey above  
2. **Scene reselect / assign** — copy `MIDI_SCENES[scene] → 8f162` (and CC) **before** stock refresh  
3. **Pads 1–16** — OR-scan private bank in `31F44`  
4. **XF morph** — later, private-bank lerp (not XF_PUB jsr until bisect)

User note (from `midi scenes.txt`): on change, resolve **parameter → trig lock → scene**, then internal/CC out. Scene layer must feed **MIDI live `8f162`**, never audio tables.

---

## 6. Recommended 1.16 scope (when you say build)

1. Keep private `MIDI_SCENES` (from 1.14+) — stop any `8f3e2` MIDI writes  
2. Set `1694`/`1698` on lock write  
3. Replace dial hook policy: **`1694`-gated read of `MIDI_SCENES`** at `4E348` (drop SCENE_HELD/`8f3e2` workaround)  
4. Leave `4E6EA` stock (audio-only); optional assert MIDI never needs it  
5. No pad/recall/XF in the same flash unless grey is confirmed instant without repress  

**Rescue:** working `grey scene locks.bin` or `OTMIDI1.10.bin`.

---

## One-liner

**Audio greys by setting `1694` and reading scene cells inside `4d948`’s audio dial branch; MIDI never enters that branch — so the proper fix is the same `1694` + scene-cell read on the MIDI dial load at `4E348`, backed by a private `MIDI_SCENES` store, not dual-write `8f3e2` or step-lock-style `SCENE_HELD` hacks.**
