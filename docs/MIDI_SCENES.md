# MIDI scene locks

Goal: MIDI tracks get scene locks that behave like audio scene locks — hold
A/B and turn a param, the value moves, greys and is stored; scene change
recalls it; the crossfader morphs it — stored independently of audio scenes.

**Live status:** see `docs/OTMIDI_HANDOFF.md` (OTMIDI1.9+ store/grey work;
1.14 = private MIDI bank). Everything below this line is the historical
probe/RE log (OT3.x era); early “not working” claims are stale.

## Why sixteen builds failed — read this before writing a seventeenth

Every one of those builds rests on one **inferred** claim that was never
measured: that turning a MIDI encoder while A/B is held executes
`0x4006257C`. That address was read out of a disassembly and it reads
convincingly:

    40062502  move.l  (0x80000012).l, d1   ; d1 = MIDI mode flag
    4006250a  addq.l  #8, d2               ; MIDI track becomes 8..15
    40062574  tst.l   (0x460d169c).l       ; scene A/B held?
    4006257a  beq.b   40062594             ; no -> normal apply
    4006257c  tst.l   d1                   ; MIDI?
    4006257e  bne.w   40062d1c             ; yes -> leave, no scene write

But "reads convincingly" is not "executes". The reported symptom — nothing
moves, nothing greys, no crash, audio unaffected — is what you would see if
our code never runs at all.

OT3.16 gives us a second, stronger piece of evidence. Its hold handler
re-tests the MIDI flag and, when the flag is false, jumps to `0x40062582`,
which pushes `d2` and calls stock `52ae8`. On a MIDI track `d2` is 8..15, and
`52ae8` addresses `(scene*8 + track)*32`, so that call would write into the
*next scene's* cells and visibly corrupt audio scenes. Audio came out clean.

So either the handler never executes, or it executes and every write it makes
is discarded downstream. **We cannot tell which, and that is the actual
blocker.** It is not a missing address; it is missing observability.

Retracted, and as of the P1 probe below these are measured falsifications, not
doubts:

- ~~`0x4006257C` is the block that stops MIDI scene writes.~~ **False.** That
  code does not execute when A/B is held on a MIDI track. Measured by probe.
- ~~`andi.l #7, d2` unblocks MIDI (OT3.14, OT3.15).~~ Retracted twice over: it
  was never confirmed to run, and had it run it would have made a MIDI lock
  overwrite the audio lock of the same-numbered track. Not independent, and
  destructive.
- ~~The draw hook at `0x40036A14` can grey TRAN.~~ That site is the NOTE-page
  piano roll and only resolves params 0, 3, 4, 5.

## OT3.P1 probe result — measured on hardware, 2026-08-27

Twelve stubs, one per reference to the scene-held flag, each marking its own
MIDI step-lock param when it executed with MIDI mode active and a scene held.
Reported: params 1, 2, 3, 4 lit (VEL, LEN, NOT2, NOT3), nothing else.

NOT2/NOT3 read `+36` rather than `100`, which is a confirmation and not a
discrepancy: the draw renders those params as offsets from `0x40`, and
100 - 64 = 36. Two independent encodings of the same sentinel agree.

**Executes** while A/B is held on a MIDI track:

    0x40034360   0x400346B4   0x40034890   0x40034AC6

**Does not execute** — including the one that mattered:

    0x40062574   <- every build OT3.1..OT3.16 hooked this or its neighbours
    0x40062DB2   0x40062E98   0x40062F70    (whole 0x40062xxx family dark)
    0x40031F3C   0x40052B22

`0x400434BE` (param 5) staying dark is a self-check on the probe: that site
*sets* the flag, and the stub samples the flag before the store, so on the
first press it reads 0 and correctly declines to mark. The instrument behaves
as designed.

So the block is in the `0x40034xxx` family, and it is a **display** block:

    40034350  ; draw scene-lock indicators while A/B is held
    40034360  cmp.l  (0x460d169c).l, d0   ; which scene is held -> d4
    400343BC  tst.l  (0x80000012).l       ; per-track loop, 8 iterations
    400343C2  bne.b  4003443c             ; *** MIDI -> skip all the work ***
    400343E8  addi.l #$8f3e2, d0          ; audio: read the scene cell
    ...
    4003445E  tst.l  (0x80000012).l       ; per-page loop
    40034464  bne.b  400344c0             ; *** MIDI -> skip again ***
    400344BC  jsr    (a4)                 ; a4 = 0x40013784, render(index, 2)

The function runs on MIDI tracks — the probe proves it is entered — and then
declines to do anything because the track is MIDI. Two `tst.l/bne` pairs, and
`0x40013784` is the routine that renders a lock indicator with a style
argument (`pea 2` at `0x400344B2`).

Two siblings on the same live path, not yet fully read:

- `0x400346A4` — 184-byte frame, resolves the held scene, then stashes the MIDI
  flag into `0x34(a7)` at `0x400346FE` rather than branching on it immediately.
  A function that *keeps* the flag is one that has a MIDI case. Prime suspect
  for where a param's displayed value and highlight are chosen.
- `0x40034AB0` — reads scene A *and* B indices and builds per-scene flag arrays
  in locals at `0xa0(a7)`/`0xa4(a7)`. Looks like scene button/LED state.

## OT3.17 / P2 counting probe result — measured 2026-08-27

Each stub bumps its own step-lock byte instead of writing a constant, so a
per-frame site saturates and a per-event site shows a small count. Two runs,
one pattern each, hold scene A without turning vs. hold and turn.

    hold only:      param 2 = 1, param 3 = sat, param 4 = sat, param 6 = 1
    hold and turn:  the above keep moving, and param 1 appears

So, by site:

| Site | Behaviour |
| --- | --- |
| `0x40034360` (param 1) | **only when a param is turned while held** |
| `0x400346B4` (param 2) | once per hold |
| `0x40034890` (param 3) | every frame while held |
| `0x40034AC6` (param 4) | every frame while held |
| `0x40052B22` (param 6) | once per hold |

`0x40034360` is inside `0x40034350`, the lock-indicator draw. A routine that
refreshes lock indicators *only* when a param is turned while a scene is held
is being called from the scene-lock write path. This also explains the blink
reported against OT3.17's grey fix: the function runs once per turn, lights
the LED, and nothing relights it.

Both `0x40034350` and its neighbour `0x400346A4` are reachable only through
function pointers at `0x400BABA2`/`0x400BABA6` — no direct `jsr` exists
anywhere in the image. They are virtual methods of one object, plausibly
"scene hold UI": `0x400346A4` on enter (once per hold), `0x40034350` on change
(once per turn). The direct caller is therefore not statically recoverable
without tracing the object, and **it does not need to be**: `0x40034350` is
itself invoked at the moment a lock is written, which is exactly the hook the
store needs.

### Answered, on hardware, at no flash cost

**Does the MIDI live value change when a param is turned while A/B is held?
No.** Held A, turned, released, value unchanged. So the encoder delta never
reaches the MIDI live table while a scene is held.

That kills the "diff a shadow copy inside `0x40034350`" design outright: there
is nothing to diff. It also means the block is *upstream of the live table*,
and — combined with P2 — that it is **not** a scene-held test, because the only
site consulting `0x460D169C` on a turn is the indicator draw.

The consistent reading of P1 + P2 + this: while A/B is held, encoder events are
routed to the scene-hold UI object (the one whose methods sit at
`0x400BABA2`/`0x400BABA6`) instead of to the normal MIDI param handler. For
audio that object writes the scene cell and then calls `0x40034350` to refresh
indicators. For MIDI it evidently does nothing. So the missing write is *inside
that object*, and `0x40034350` is a measured beachhead into it.

## Full dispatcher read, 2026-08-27 — supersedes the P3 plan below

Static read only, no new flash yet. Re-disassembled `0x400624FC..0x40062620`
in full (earlier notes only ever quoted `0x40062502..0x40062594`, a partial
window that hid the actual branch structure).

    400624FC  mvz.b (0x80000000).l, d2        ; d2 = track
    40062502  move.l (0x80000012).l, d1       ; d1 = MIDI flag
    40062508  beq.b  4006250C
    4006250A  addq.l #8, d2                   ; MIDI -> track+8
    4006250C  tst.l  d0
    4006250E  beq.w  40062594                 ; -> NORMAL APPLY (no lock context)
    40062512  tst.l  (0x460D172A).l           ; FLAG_A
    40062518  beq.b  4006255E
    4006251A..40062530   ...jsr 40054CD8...   ; CALL #1 (FLAG_A path)
    4006255E  tst.l  (0x460D172E).l           ; FLAG_B
    40062564  beq.b  40062574
    40062566..4006256E   ...bra.w 40062AFC    ; FLAG_B path, unrelated handler
    40062574  tst.l  (0x460D169C).l           ; SCENE_HELD
    4006257A  beq.b  40062594                 ; not held -> NORMAL APPLY
    4006257C  tst.l  d1                       ; MIDI?
    4006257E  bne.w  40062D1C                 ; MIDI -> LEAVE, nothing called
    40062582..4006258C   ...jsr 40052AE8...   ; audio: scene store, then LEAVE
    40062594  NORMAL APPLY:
    400625AA  jsr 40054CD8                    ; CALL #2 (the actual value applier)
    400625B4  bra.w 40062D1C

So there are exactly three things this dispatcher can do with an encoder
event, and they are mutually exclusive per event:

1. **FLAG_A path** -- calls `0x40054CD8` (see below).
2. **FLAG_B path** -- jumps away to `0x40062AFC`, unread.
3. **Neither flag set:** if a scene is held, audio calls `52AE8` (scene store)
   and MIDI calls nothing and leaves; if no scene is held, both fall to
   **NORMAL APPLY**, which also calls `0x40054CD8`.

**The load-bearing fact: when a scene is held and the track is MIDI, this
dispatcher calls nothing at all.** Not `52AE8`, not `0x40054CD8`. That is
sufic to explain "value does not change, nothing greys" without any further
gate inside `0x40054CD8` -- the dispatcher never reaches it.

This also explains a discrepancy with the P1 probe, which found `0x40062574`
dark: `0x40062574` only executes when FLAG_A and FLAG_B are *both* clear. P1
did not instrument `0x460D172A`/`0x460D172E`, so it cannot say whether one of
them was set during the user's hold-and-turn test, diverting execution before
`0x40062574` is ever reached. **Not yet known whether FLAG_A/FLAG_B were the
reason, or whether this whole 40-byte region is reached by a different route
for a plain encoder turn than the one this trace assumes.**

`0x40054CD8` itself, read in the same pass: decodes a raw index into track
(`d7`, divs by 6 twice) and calls `0x400A6994` first (an "is this control
usable" gate -- also referenced from inside `52AE8`'s own gating, per earlier
notes). If track `d7 > 7` (i.e. MIDI, `+8` encoding) it branches to a block
that writes `8f162` -- **so this function, if reached, already contains a
correct write to the MIDI display table.** For `d7 <= 7` (audio) it takes a
different block that writes a *different* table (`0x8edaa`/`0x8ee9a`, not
`8f3e2` or `8f162` -- likely a "recent value" or highlight cache, not
identified yet). Neither branch touches `0x460D169C` or the scene cells
directly; scene storage for audio is handled entirely by the separate
`52AE8` call at `0x40062582`, upstream of this function.

If `0x40054CD8` were reached with a MIDI track and the display write inside it
executed, that alone would move the dial. It measurably does not move. So
either the dispatcher truly calls nothing for MIDI+held (most consistent
reading of the trace above), or FLAG_A/FLAG_B change that on real hardware in
a way not yet measured.

### OT3.P3 result — measured on hardware, 2026-08-27: all four dark

Fresh pattern, MIDI track, trig on step 1, hold A (and separately B), nudge a
MIDI parameter a small amount, release. **None of the four checkpoints lit.**
No p-locks appeared on step 1 at all, on any page, either scene button.

This is unambiguous in a way the earlier probes were not — there is no
"wrong number, right site" reading possible here, the result is presence or
absence of any lock, and there was none. So, decisively:

- ~~The `0x400624FC..0x40062620` dispatcher runs for a MIDI encoder turn while
  a scene is held, diverted by FLAG_A/FLAG_B before reaching the MIDI
  block.~~ **False.** It does not run *at all* — not the entry checkpoint,
  not either flag test, not the scene-held test. Measured.
- This also retracts trusting `0x40054CD8` (the "generic value applier" that
  full dispatcher read found and reasoned about at length) as relevant to
  this gesture. It was reached only in theory, through a dispatcher that
  itself was never entered. The detailed read of its internals was real work
  correctly done, but it describes a code path this gesture does not take.

So the mechanism is not in the ColdFire instruction stream anywhere near
`0x40062xxx`. What IS proven to run for this exact gesture (P1, P2, and
reproduced by the OT3.17 indicator fix on hardware) is `0x40034350` and
`0x400346A4` — and both are reachable only through function-pointer slots at
`0x400BABA2`/`0x400BABA6`, with **no direct `jsr` to either address anywhere
in the image.** Whatever calls them does so through a register loaded at
runtime, which a literal-bytes search cannot find.

One static lead was chased partway: `pea.l $400babba.l` immediately followed
by `jsr` appears at exactly two sites, `0x40043494` (-> `jsr 0x4007E760`) and
`0x40054CA6` (-> `jsr 0x4007E81C`). Both targets, once read, turn out to be a
generic **linked-list register/unregister** pair operating on a list head at
`0x460E7624` (insert-if-absent at `0x4007E764`, remove at `0x4007E820`, same
shape both times: walk the list rooted at `0x460E7624`, compare against the
node, splice it in or out). `0x400BABBA` is a **node being registered into an
observer list**, not a "this" pointer into a call. This is a generic
callback/observer framework, not code specific to scenes or MIDI — whatever
walks `0x460E7624` and invokes each registered node's callback is a separate,
not-yet-found piece of generic UI plumbing, and reverse-engineering it
further means reverse-engineering that framework, not this feature. Recorded
so the next person doesn't redo this dead end: **this lead does not go
anywhere cheap.**

### The actual structural reason NOTE never reaches any of it — found via docs/PARAM_PAGES.md, not a new probe

`PARAM_PAGES.md` §2/§5b already documents a field this investigation had not
looked at: every page descriptor stores **six per-encoder handler pointers**
at its own entry start (`E+0x00..E+0x14`, one per knob on the page). Reading
them directly out of the image for every MIDI page:

| page | E | six handler pointers |
|---|---|---|
| NOTE | `0x400d3e06` | `0 0 0 0 0 0` |
| ARP | `0x400d3f98` | `0x40038d94` ×6 |
| LFO (MIDI) | `0x400d412a` | `0x40038d94` ×6 |
| CTRL 1 | `0x400d42bc` | `0x40038d94` ×6 |
| CTRL 2 | `0x400d444e` | `0x40038d94` ×6 |

**NOTE is the only MIDI page with all six handlers null.** Every other MIDI
page — ARP, LFO, CTRL1, CTRL2 — uses `0x40038d94`, the exact same shared
default handler most ordinary audio parameters use (per `PARAM_PAGES.md` §2,
"usually `0x40038d94` ×6"). `0x40038d94` itself is just a delta-to-range
clamp/scale utility, not the scene-aware code — but the fact that NOTE alone
opts out of the whole generic per-encoder mechanism means NOTE almost
certainly has its own bespoke value-apply code that nothing else on the
machine shares. Every probe and every disassembly session so far (`52ae8`
gates, the `0x40062xxx` dispatcher, `0x40054CD8`, `0x40034350`) was reasoning
about the **generic** path. If NOTE bypasses it entirely, none of that was
ever going to see NOTE's actual code, on hardware or in a disassembly.

**Every hold-and-turn test done to date, by hand and by probe, was on the
NOTE page** (VEL/LEN/NOTE/NOT2 are NOTE's six parameters). That may be the
whole explanation for the string of dark probes: not that scene-hold logic
for MIDI is missing everywhere, but that it was only ever tested on the one
MIDI page that structurally cannot share it.

**This is a free hardware test — no build needed.** On the currently flashed
firmware (or stock 1.40C), on a MIDI track, switch to the CTRL1, CTRL2, ARP,
or LFO page (not NOTE) and hold A or B while turning a parameter:

- If it greys / holds a static value / recalls per scene already — MIDI
  scene locking already works, just not on NOTE, and the real remaining work
  is much smaller than assumed (fix or extend one bespoke page instead of
  building a whole new mechanism).
- If it behaves exactly like NOTE (no grey, no movement) — the null-handler
  theory doesn't explain the symptom either, and the generic `0x40038d94`
  path (or whatever calls it) needs the same "does it even run" probe NOTE
  already got.

### HARDWARE, 2026-08-27: every MIDI page fails, not just NOTE

Tested by hand on CTRL1/ARP/LFO as well as NOTE: **no MIDI page locks or
greys** while A/B is held. So the null-handler asymmetry above is real but
**is not the explanation** — the pages that share the generic handler with
audio fail identically. Retract it as a cause; keep it only as a note that
NOTE is additionally bespoke. Scope decision from the user: **NOTE may be
excluded from MIDI scenes** if it stays expensive. ARP/LFO/CTRL1/CTRL2 are
enough for the feature to be worth shipping.

### The callback list is a TIMER table — retracts the whole "find the caller of 0x40034350" thread

Read this session, and it closes a line of investigation rather than
advancing it. Measured, all from the stock image:

**The A/B press handler is `0x4004348C..0x400434D4`.** Fully decoded:

```
4004348E  move.l  $8(a7), d2          ; button id
40043492  pea.l   $400BABBA.l
40043498  jsr     $4007E760.l         ; REGISTER that object in the list
400434A0  moveq   #$19, d0
400434A2  cmp.l   d2, d0              ; 0x19 = scene A
400434A6  clr.l   $460D1690.l         ; A: 0     (B: =1 at 400434B4)
400434AC  move.b  #$1, d0             ; A: HELD=1 (B: =2 at 400434BA)
400434BE  move.l  d0, $460D169C.l     ; <-- SETS SCENE_HELD
400434C4  clr.l   $460D1698.l
400434CA  jsr     $400418E0(pc)       ; redraw
```

**There is no MIDI check anywhere in it.** SCENE_HELD is set to 1 (A) or 2
(B) for MIDI tracks exactly as for audio, which is consistent with every
probe that ever saw SCENE_HELD nonzero on a MIDI track. The matching release
handler is `0x40054CA2`: unregisters via `0x4007E81C`, then clears both
`0x460D1694` and `0x460D169C`. Both hook points are confirmed, unconditional
and MIDI-agnostic — **useful, and reusable.**

**But the list they register into is a periodic-timer table, not an event
bus.** `0x460E7624`'s insert/remove pair compiles the list into an 8-slot
table at `0x460E7628`, stride `0xe`. Two dispatchers consume it, and they are
the only consumers in the image:

```
4007E944   walk 8 slots; per slot: counter++, if due -> jsr (a0) with slot
           index as the argument, reset counter      ; periodic tick
4007E996   invoke ONE slot by index: a0 = *(0x460E762C + idx*0xe); jsr (a0)
```

So `0x400BABBA` is a **periodic redraw job installed while A/B is held**, and
`0x40034350` / `0x400346A4` are its **timer callbacks** — not encoder-path
code, and never were. That explains P1/P2 cleanly (those sites saturated
because they run every tick) and it means the long-running thread
"find who calls `0x40034350` and you find the write path" was chasing a
repaint timer. **Retracted. Do not resume it.**

### Where the write path provably is and is not

- `0x40054CD8` is the generic apply: `d7 <= 7` audio, `d7 > 7` MIDI/extended
  (the `0x40054EA6` branch, which writes the display cell at `0x8f162` and
  the sound cell at `0x46c76dc0` — both known-good addresses). Registers at
  the MIDI store: `d4` = clamped value, `d2` = param-8, `d5` = display track.
  A diversion hook here has everything it needs.
- It has **exactly three callers in the whole image**: `0x40062532`
  (FLAG_A path), `0x400625AC` (normal apply), `0x400A15F2` (keypad/name
  entry, unrelated). Both real ones are inside the `0x40062xxx` dispatcher.
- P3 measured that dispatcher's **entry** dark for MIDI+held. Combined with
  the caller census: while A/B is held on a MIDI track, **nothing calls the
  apply function at all.** That matches the symptom exactly — the value does
  not move, does not grey, and is unchanged on release.
- `0x400624FC` has **zero literal references** anywhere in the image, so its
  own caller is a computed/indirect call and cannot be found by address
  search. **This is now the single blocking unknown.**

### Recommended approach for the next deep session (ranked)

**1. One-checkpoint probe that discriminates decisively (cheapest, do first).**
Instrument `0x400624FC` entry gated on MIDI only — *not* on SCENE_HELD.
Then turn a MIDI encoder (a) not holding, (b) holding.

- fires unheld, dark held -> the gate is upstream and conditional on hold.
  That upstream caller is the whole fix, and it is worth the hunt.
- dark in both -> MIDI encoders never use this dispatcher, and since
  `0x40054CD8`'s only other callers are ruled out, the MIDI apply path is
  something we have not identified at all. Different search entirely.

This is one hook and one readout, and it splits the remaining hypothesis
space in half. Nothing else should be built before it.

**2. `0x400136A8` is the named next target for the upstream hunt.** Both
timer dispatchers tail-`jmp` to it, so it is shared UI-event plumbing sitting
one level above the callback mechanism. It is the most promising unread
route to the main event pump and to whatever table reaches `0x400624FC`.

**3. Design-around, now that scope allows dropping NOTE.** The press and
release handlers above are confirmed, unconditional and MIDI-agnostic, and
the OT3.17 store + indicator already work on hardware. The missing piece is
only the value capture. **Note the trap:** capture-on-release by diffing
live values against a press-time snapshot looks attractive and *cannot
work* — the live value is measured unchanged while held, so there is
nothing to diff. Any design-around still needs one point where the held
encoder delta is observable, which is exactly what (1) is measuring.

### The MIDI apply path, found 2026-08-27 — and OT3.18 built on it

`0x40055304` is the MIDI half of the parameter-apply function, and it is the
code that actually maintains the MIDI value cells. Measured, in order:

```
40055304  d3 = displayed pattern (0x100b14cf)
4005530A  d4 = displayed track   (0x100b14cc)
40055310  d6 = flat param index 0..31, from 0x2f(a7)
40055318  a2 = track*32 + param
4005531C  d0 = pattern * 0x18b2
40055326  addi.l #$8f162, d0          <-- OT3.18 HOOKS HERE
4005532C  add.l  (0x46c82456).l, d0   ; bank base
40055332  lea.l  (a2, d0.l), a5       ; a5 = &live cell
4005534C  d0 = (a5)                   ; CURRENT value
40055352  a0 = *(a3 + d2 + 0x12a)     ; per-param handler, default 0x4003240C
40055368  jsr (a0)                    ; new value from the encoder delta
4005536A..40055388                    ; clamp to min .. min+count-1
4005538A  move.b d2, (a5)             ; WRITE
40055392..400553A2                    ; also -> 0x100a52b0 family
400553A6..400553E6                    ; if channel matches -> 0x46c76dc0
400553EA  tst.l (0x460D172A).l        ; FLAG_A = a trig is held
4005540C  jsr 0x40042158              ; ...then write a STEP LOCK
```

Two things this settles:

1. **`0x460D172A` ("FLAG_A" in the old dispatcher notes) is the trig-held /
   p-lock-record flag**, and `0x40042158` is the MIDI p-lock write. So the OS
   already contains the exact feature shape being built — divert a MIDI
   parameter turn into a *lock store* when a modifier is held. Scenes just
   need the same treatment with a different modifier and a different store.
   Cell layouts cross-validated here: MIDI sound cell is
   `0x46c76dc0 + track*68 + param` (stride 0x44, matching the `lea 0x44(a0)`
   walk at `0x4003F3E4`), and `0x100a4ece + 0x3e2 = 0x100a52b0` exactly, the
   address `docs/` already had recorded independently.
2. **`a5` is `a2 + d0` where `a2` is already `track*32 + param`.** So the
   whole read-modify-clamp-write sequence can be pointed at a different
   store by changing one base — reusing stock clamping and the stock
   per-parameter handler instead of reimplementing either.

**OT3.18** (`tools/build_ot318.py`) does exactly that, in one instruction:

- not held -> stock `addi.l #$8f162`, return to `0x4005532C`. Byte-identical.
- held -> `d0 = MSC + scene*256`, jump to `0x40055332`, skipping the bank
  add. `a5` lands in our store, so the stock code reads the *stored* value,
  applies the delta to it, clamps it to the parameter's real range, and
  writes it back into the scene. The live cell is never written while held,
  which is the requested "dial sits on the locked value" behaviour.
- an unlocked cell (`0xff`) is seeded from the live value first, so the first
  detent nudges from where the parameter is rather than jumping to the top.
- scene index from the measured derivation (`0x8ed90` for A, `0x8ed91` for
  B); `0xff` means unassigned and falls through to stock rather than
  storing into scene 15.

Readout is the OT3.17 indicator, which is the one piece already proven on
hardware. **The store is seeded on track 8 only, as a control**: track 8
lighting proves the readout works, and an indicator on the track actually
turned can then only have come from the new hook. Both light = the store
works. Track 8 only = the apply path is not reached while held either, and
that result kills this hook as cleanly as P3 killed the dispatcher.

Stub verified by disassembling the assembled image (repo rule), not by
trusting the assembler.

**The crossfader morph is deliberately not in this flash.** It is one hook
away — `0x4003F3A2`, the tail of the audio morph pass, which publishes the XF
position from `0x460D16C8` and interpolates through the signed 16-bit weight
table at `0x400BCD90` with `result = (A<<16 + (A-B)*w + 0x7f + round) >> 16`.
Held back because morph is downstream of storage (nothing to morph until the
store fills), and because it is a nested 8x32 loop on every XF tick where a
mistake can take the unit down and *mask the storage result*, wasting the
flash.

### Superseded static reasoning, kept for the record only

The paragraphs below (the full dispatcher trace and the `0x40054CD8` read)
are retracted as an explanation for *this* gesture by the P3 result above.
They are not wrong as a description of what that code does — they are wrong
about it being on the path we care about. Left in place because the
addresses and technique (full dispatcher trace) are reusable elsewhere.

### Cheapest next measurement (supersedes "hook the 8f162 writers" below)

Don't probe the *writers* — the trace above says none of them run for
MIDI+held, which would just re-confirm a static reading with a live one at flash
cost. Probe the **branch itself**: one stub at `0x4006257C`
(`tst.l d1 / bne.w`, still the correct hook site, just for a different reason
now) that fires a sentinel whenever it is reached with the MIDI flag set,
*and* two more stubs on `0x460D172A`/`0x460D172E` that fire whenever either
reads non-zero while a MIDI encoder is turned with a scene held. Same
machinery as P1/OT3.17 (`tools/build_ot317.py`'s `find_probe_sites`/
`build_probe_site`, generalized to a caller-supplied site list instead of one
literal). Three sites, one flash, and it will show which of the two
explanations above is right.

## Superseded: P3 as originally planned (kept for the record)

Cheapest decisive step, one flash, same counting-probe machinery as OT3.17
(`tools/build_ot317.py` -- reuse `build_counter` and `build_probe_site`
verbatim, only the site list changes).

Hook the **writers of the MIDI live table**, not the readers. `0x40028910`
region is confirmed as the MIDI param write path:

    40028900  movea.l (0x46c82456).l, a0
    4002890a  adda.l  #$8f162, a0
    40028910  move.b  (a2), (a0)     ; DISPLAY
    40028912  move.b  (a2), (a5)     ; SOUND, a5 = ...+0x100a52b0

Probe it and the other `8f162` writers, then compare two runs:

  - turn a MIDI param with **no** scene held  -> the writer that fires is the
    normal path
  - turn with A held                          -> whichever site stops firing
    localises the gate to its caller

Then hook that caller's MIDI/scene decision the way OT3.17 hooked
`0x400343BC`, and route MIDI edits into the store instead of dropping them.

Readers of `8f162` for reference (16): `0x40026538 0x4002890C 0x4002967A
0x4002B4F8 0x40036A0A 0x40036A90 0x4003BAA2 0x40043960 0x40043AF8 0x4004E37C
0x4005056C 0x40050A84 0x40054EC4 0x40055328 0x4005C3AE 0x4005D6D8`.

## Handoff notes

What is already built and reusable:

- `tools/ot3_asm.py` — every encoding checked against a stock instruction, and
  `link()` resolves branches so displacements are never hand-typed. Use it.
  The tree has previously shipped `ea8a` for `eb8a` and `jsr` for `jmp`.
- `tools/build_ot317.py` — the working pattern for this whole class of work:
  assert stock bytes at each hook, assert the cave and store are stock zeros,
  assert store and cave do not overlap, patch, verify only expected spans
  changed, refuse any stub referencing `0x8f3e2`, then disassemble the emitted
  stub and fail on anything undecodable. That last check caught a real
  store/cave overlap before it reached hardware.
- `tools/_dis_ot3.py` — ColdFire-aware; Capstone's generic M68k mode
  misreads the ISA_B `mvs/mvz` and `muls.l/divu.l` forms this code is full of.
- Cave: one stock zero run at `0x400D64DA..0x400D7C1C`. OT3.17 uses
  `0x400D6600` for the 4096-byte store and `0x400D7600..0x400D7C00` for code.

**Lock-indicator fix — keep it, and do not call it a grey fix.** `0x400343BC`
and `0x4003445E` (`tst.l (0x80000012).l`, 6 bytes each) become `jmp` to stubs
that send audio back to the stock instruction with stock CCR and, for MIDI,
scan the store and make the identical render call (`pea 2` / `move.l (aN),dN` /
`addq #1` / `jsr (a5|a4)`) before rejoining the loop advance.

Confirmed on hardware: with a seeded lock on page 0, holding A on a MIDI track
lights **the correct page LED** (SRC, page 0) from any page, which is the
stock semantics — the page LED means "a lock lives on this page", not "this is
the page you are viewing". It blinks rather than holding, because
`0x40034350` is called once per turn and nothing relights it.

Also measured: the **track** LED does *not* go green for MIDI. It goes yellow,
which is the plain scene-hold colour (red on audio tracks), so the loop-1 patch
at `0x400343BC` is either not landing or is being overwritten. Only the loop-2
page LED is confirmed.

What this fix is **not**: it does not grey a parameter value, and OT3.17
contains no code that tries to. Greying the value is a separate, unfound
mechanism — see the unknowns below. Do not read "indicator lights" as
"greying works".

Traps specific to this feature:

- `0x4006257C` and the whole `0x40062xxx` family are dead on this path.
  Measured. Do not go back there.
- Never route MIDI through `0x40052AE8`. Its cell address is
  `(scene*8 + track)*32`, so a MIDI track index of 8..15 lands in the next
  scene, and clamping the index with `andi.l #7, d2` (OT3.14/15) makes a MIDI
  lock overwrite the same-numbered audio track's lock.
- The store must boot `0xFF`-filled: `0xFF` is the OS's own "unlocked"
  sentinel, and `0x00` is a legal value.
- Params 3/4/5 on the MIDI NOTE page display value − 64. Sentinels read low.

Not started: persistence. See the section below; it needs the OS serializer,
and it should not be attempted until the write path works in RAM.

### Still unknown after P1

The probe gated on "MIDI mode and a scene held", which does not require an
encoder turn, so it cannot separate *holding* from *turning*. Where the store
would happen on a turn is therefore still unmeasured, and the value not moving
means something also gates the MIDI param write while a scene is held. Next
measurement (P2) should hook the MIDI param writer at `0x400288A0` and its
upstream candidates with the same technique: if it lights while A/B is held,
the write happens and something discards it; if it stays dark, the gate is
upstream of it.

## Measured facts

All read out of stock 1.40C with `tools/_dis_ot3.py`. Code-derived, which is
the strongest evidence available without hardware — but note that none of it
establishes *which* code executes on a given user action.

### Globals

| Address | Meaning | Evidence |
| --- | --- | --- |
| `0x80000000` | current track | `0x40060BA0` |
| `0x80000004` | current pattern | `0x40060B6E` |
| `0x80000012` | MIDI mode flag | branched on at `0x400434E0`, `0x40060AB8` |
| `0x100B14CC` | display track | `0x400369EE`, `0x40043916` |
| `0x100B14CF` | display pattern | `0x400369E8`, `0x40043944` |
| `0x100B14D0` | p-lock pattern | `0x40036A20`, `0x40043910` |
| `0x460D169C` | scene held: 0 none, 1 = A, 2 = B | **set** at `0x400434BE` |
| `0x460D5D48` | held step, `<= 0x3f` means held | set at `0x40060AF2` |
| `0x46C82456` | live bank/project pointer | ubiquitous |

`0x460D169C` is now measured rather than assumed — `0x400434A0` sets it to 1
or 2 depending on which button was pressed, which confirms the A/B encoding
every stub in this tree relies on.

### Tables

    MIDI p-lock    bank + pat*0x8ed8 + track*0x8b0 + step*32 + 0x4900 + param
    MIDI flat      bank + pat*0x18b2 + track*32    + 0x8f162 + param
    audio scene    bank + pat*0x18b2 + scene*256   + track*32 + 0x8f3e2 + param

The MIDI p-lock formula is confirmed three times independently, at `0x40036A46`
(param 0), `0x40036ADA`/`0x40036B0A`/`0x40036B3A` (params 3, 4, 5) and
`0x4004393A`/`0x400439FE` (params 0, 1).

### The OS's lock idiom — this is the important one

Everywhere the OS resolves "locked value or live value" it does the same thing:
read the lock byte with a sign-setting move, then branch on the sign. `0xFF`
means unlocked because `0xFF` is negative as a byte.

    4004393A  move.b  $4900(a0), d0        ; step p-lock, param 0
    4004393E  move.b  d0, $1c(a7)
    40043942  bge.b   40043968             ; locked -> keep it
    ...                                    ; else fall back to the flat
    40043964  move.b  (a0), $1c(a7)        ; 8f162 + pat*0x18b2 + track*32

Same shape at `0x40036A46`/`0x40036A4E`, `0x400439FE`/`0x40043A02`. So a lock
array is a byte array where non-negative means locked, and our store's
`0xFF = unlocked` convention already matches the OS. Good — but the grey
*attribute* is not chosen in any of these functions. They resolve values only.

### What is still unknown

1. **Which code runs when A/B is held and a MIDI encoder turns.** The whole
   feature depends on this and it has never been measured.
2. **Where the MIDI dial row is drawn**, i.e. which read of `8f162` feeds the
   row that shows TRAN. There are 16 readers of `8f162`; the two studied so far
   are the NOTE-page piano roll (`0x400369C8`) and the held-step note send
   (`0x400438FC`). Neither is the dial row.
3. **How a locked param is greyed.** Still unfound, and OT3.17 did not address
   it despite being named "grey fix" in its own docstring — the name was
   wrong, it only ever drove lock indicators. Greying is not in any
   value-resolution function read so far (`0x400369C8`, `0x400438FC`,
   `0x40043930`): those choose values, never attributes. The remaining
   candidate is `0x400346A4`, which runs once per hold, has a 184-byte local
   frame and stashes the MIDI flag into `0x34(a7)` at `0x400346FE` instead of
   branching on it — a function that keeps the flag is a function with a MIDI
   case. Read it before inventing a mechanism.

## Plan

### 1. Probe build — stop guessing which code runs

One flash buys the fact that sixteen flashes have not. Instrument several
candidate sites; each writes a distinct constant into a channel that is
*known* to display, then read the constant off the screen to learn which site
executed.

The channel: an **audio** scene cell (track 1, scene A, param 0). Audio scene
locks demonstrably work and display, so they are a working oscilloscope for
"did this hook run". Nothing else in this build has that property.

Candidate sites, each writing its own signature: `0x40062502` (MIDI flag
read), `0x40062574` (scene-held test), `0x4006257C` (the presumed block),
the MIDI encoder entry, and the MIDI param setter.

Procedure: MIDI page, hold A, turn TRAN. Then audio page, hold A, read
track 1 param 0. The number names the deepest site reached.

Cost: one flash, one audio scene cell the user clears afterwards.

### 2. Find the dial row the same way

Write a sentinel into each candidate display source and see which one moves
TRAN on screen. This answers "what must I write for the value to move" by
measurement instead of inference, and will likely expose the grey attribute
next to it.

### 3. Build the feature on the confirmed path

Only after 1 and 2. The store design from OT3.16 is sound and can be reused as
is: own array, `0xFF` = unlocked (matching the OS idiom), never touching
`52ae8` or the audio scene cells, every write gated on a lock existing so a
project with no MIDI locks behaves exactly like stock.

### 4. Persistence

Still open, and the earlier optimism is retracted:

- ~~176 spare bytes per (pattern, track) after the p-lock array.~~ **Wrong.**
  Track *n*'s p-locks end at `0x4900 + n*0x8b0 + 2048`, and track *n+1*'s
  p-locks start at `0x4900 + (n+1)*0x8b0`. The 176-byte gap between them holds
  track *n+1*'s per-track fields — `0x48F8(a0)` is read at `0x40060BB6`, which
  is below `0x4900` and therefore inside that gap for the next track. Used.
- Part-record tail: ~464 bytes per part. The scene block is measured at 4256
  bytes (4096 cells + 160 flags), confirmed against a real project (LN-1, 16
  banks: parts 1..7 of every bank show it as one unbroken 4256-byte `0xFF`
  run). But the bank file stride is `0x18BB` against `0x18B2` in RAM, so the
  file is serialized rather than dumped and the OS serializer has to be taught
  any new field. That is real work and it should not be attempted before the
  feature works in RAM.

Consequence to state plainly to the user: until step 4 lands, MIDI scenes do
not survive a power cycle.

## OT3.19 — built, bug caught before flash, awaiting the hardware test

`tools/build_ot319.py` (the design described above: suppress `SCENE_HELD` for
MIDI, drive a private `OWN_HELD` flag, force the encoder turn through the
normal apply path at `0x40055326`) was written in the previous session and
never run. Built and disassembled for the first time 2026-09-01.

**Bug found by the repo's own disassemble-the-output rule, not by the
assembler — it would have wasted a flash.** `build_recall()`'s per-parameter
loop advanced its cave-store cursor with a helper, `addq_a(0)`, meant to emit
`addq.l #1,a0`. It computed `0x5088 + (an << 9)`, which for `an=0` is
`0x5088` — a *different, fully valid* instruction, `addq.l #8,a0` (ADDQ's
data field is 3 bits and `0b000` means 8, not 0, so a base that hasn't
already folded in `data=1` silently means 8; the `<<9` was also aimed at the
wrong field — 9 is the data field's shift, not the 0-shift register field,
so the helper would have stayed broken for any register but `a0` too). The
assembler accepted it, and the build's own disassembly self-check accepted it
— `addq.l #8,a0` is perfectly decodable, just semantically wrong. It would
have advanced the recall cursor 8 bytes per parameter instead of 1, so scene
recall would have read every 8th stored byte and written garbage into most
params. Fixed to `0x5288 + an` (the two other call sites in the same file
already used the correct literal, `5288`, hardcoded). Rebuilt; the recall
loop now disassembles as `addq.l #1,a0` and the full cave (772 B) still
disassembles clean start to end.

Shipped as **`OTMSCN01.bin`** on the Desktop (internal version string stays
`1.40OT3.19` — that string is just this build's own build tag, harmless to
leave).

**Not yet known:** whether the underlying trick — telling the OS nothing is
held so it drives the MIDI encoder through its own normal apply path, while
we separately remember 1/2 in `OWN_HELD` — actually works. Every fact this
design rests on (the press/release handlers, the `0x40055326` apply site, the
`0xFF`-unlocked convention) is independently measured. What is not measured
is the composition: this is the first flash of this specific mechanism.

**The test** (also printed by the build): MIDI track, any page except NOTE
(NOTE is separately excluded — see the null-handler section above). Hold A,
turn a parameter, release — does it read back what was dialled? Hold B,
dial elsewhere, release. Tap A, tap B — do the two recall? If nothing moves,
check param 5 on step 1: locked to `111` means storing ran but recall is
broken (which would now point at a *different* bug than the one just fixed,
since that fix was verified by direct disassembly of the shipped image, not
inferred); unlocked means the turn still isn't reaching `0x40055326` at all,
and the next suspects are `0x460D1690`, `0x460D1698`, and the periodic job at
`0x400BABBA` (see "the callback list is a TIMER table" above — not the timer
callback itself, but whatever decides to register it, which was never
identified).

Crossfader morph is deliberately still not in this build — same reasoning as
OT3.18: it's downstream of storage, so there's nothing to morph until a
hardware test confirms the store/recall pair actually holds correct values.

## `OTMSCN01.bin` tested on hardware — no lock at all (2026-09-01)

Tested per the procedure above, on CTRL1/ARP/LFO (not NOTE) as instructed.
Result: **no lock at all** — not even the param-5/step-1 marker that would
indicate "storing ran but recall is broken." This falsifies the OT3.19
hypothesis outright: suppressing `SCENE_HELD` and driving a private
`OWN_HELD` flag does not get MIDI encoder turns to flow through
`0x40055326`. Either that apply site is never reached regardless of
`SCENE_HELD`'s value, or something else entirely gates it that the
press/release hook never touched.

## OT3.P4 — does `0x400624FC` run for a MIDI turn at all? Measured: no.

Every build since the original dispatcher trace (OT3.13 era) through OT3.18
and OT3.19 was built downstream of `0x400624FC`, the `mvz.b
(0x80000000).l,d2` dispatcher entry that was long assumed to be *the* MIDI
encoder routing point, gated somehow on `SCENE_HELD`. That assumption was
never directly measured — only inferred from disassembly of what happens
*if* control reaches it.

`tools/build_ot3_p4.py` hooked `0x400624FC` itself with a probe that
branches on `MIDI_FLAG` then `SCENE_HELD`, bumping one of two step-lock
counters (param 10 = unheld hits, param 11 = held hits) via the same
`build_counter` helper from OT3.17/P3. Flashed as `OT3.P4.bin`.

**Test result: both param 10 and param 11 read back unlocked — zero hits,
either way.** `0x400624FC` never runs for a MIDI encoder turn, held or
unheld. This is decisive and retroactively explains every prior result in
this family:

- P3's "no locks at all" (2026-08-?) — consistent, not a fluke.
- OT3.18's storage failure on track 1 while its track-8 control passed —
  the control only proved the OT3.17 *indicator/readout* mechanism still
  worked (it was seeded at build time, not written at runtime); it never
  proved `0x40055326` — or anything downstream of `0x400624FC` — actually
  ran during a real turn.
- OT3.19's "no lock at all" (previous section) — the private-hold-flag trick
  was solving the wrong problem: there is no gate on `SCENE_HELD` to route
  around at this address, because this address is not on the MIDI encoder's
  path in the first place.

**Retracted:** the entire `0x40062xxx` / `0x40054CD8` dispatcher family as
the MIDI-turn apply path. Nothing under this address should be targeted
again for ordinary encoder-turn handling. (It may still be real code for
something else — trig/p-lock recording, perhaps — just not this.)

## Finding the real entry point: `0x40055008`, not `0x40055304`

`0x40055304` — the address OT3.18 hooked, based on a plausible-looking
disassembly starting exactly there — has **zero literal references anywhere
in the image**. That should have been the tell. Reading backward from it
this session (2026-09-01) found it is not a function at all: it's the
MIDI-mode branch inside a real function that starts 764 bytes earlier, at
`0x40055008`:

```
40055008  lea.l   -$30(a7), a7
4005500c  movem.l d2-d7/a2-a6, (a7)
40055010  d5 = $34(a7); a4 = $38(a7)        ; two stack arguments from the caller
40055018  jsr 0x40027e00 ; jsr 0x40027e30   ; redraw-adjacent calls
40055024  jsr 0x40031f28  -> a3             ; param-table lookup
4005503a  jsr 0x400a6994                    ; "is this control usable" gate
40055044  btst.b #0, d1
40055048  beq.w 0x400554d4                  ; gate fails -> UNEXPLORED, new suspect
4005504c  d4 = (0x460d1684).l               ; unnamed global, not yet in this doc
40055060  move.b ..., $2f(a7)               ; stashes something at the SAME stack
                                             ; slot 0x40055310 later reads as d6
40055066  tst.l   0x80000012                ; MIDI flag
4005506c  bne.w   0x40055304                ; MIDI branch (OT3.18's hook site)
40055070  ...                               ; audio falls straight through instead
```

`0x40055008` has real callers too — unlike `0x400624FC`, it isn't an
isolated island. It's wired as the handler pointer inside a 22-byte-per-
parameter descriptor table found at `0x400c085c..` (six consecutive
records for one MIDI page all point at it; a seventh record right after
uses a different handler, `0x4004eb24`, matching a page where one knob is
special-cased). This is the same *kind* of structure `docs/PARAM_PAGES.md`
already documents at the per-page level, just one level deeper — a genuine,
data-driven "apply an encoder turn to this parameter" dispatch, not a
speculative address.

One open question this raises immediately: who reads the pointer out of
that table and does the indirect `jsr`? Searched for literal references to
the table's own base address — none exist anywhere in the image, meaning
the base is computed at runtime (probably via the already-documented
per-page `E` pointers, one more indirection than previously modeled) rather
than baked in as a constant. Not yet chased further; see OT3.P5 below for
why that chase was deferred in favor of a cheaper, more decisive test first.

## OT3.P5 — built, awaiting hardware test: does `0x40055008` run for MIDI, held or not?

`tools/build_ot3_p5.py` hooks `0x40055008` (8 bytes — its two prologue
instructions, `lea` + `movem`, packed with no room for a 6-byte `jmp`
between them, so both are replayed verbatim after the probe). Same shape as
P4: branch on `MIDI_FLAG` then `SCENE_HELD`, bump one of two step-lock
counters — param 8 = unheld hits, param 9 = held hits. Flashed as
`OT3.P5.bin`.

This is the cheapest next measurement because it's the fork in the road:

- **8 locked, 9 unlocked** — the real apply function runs unheld, never
  held. The block is upstream of `0x40055008`, between its unidentified
  caller and here. Next target: find that caller (the indirect `jsr`
  through the descriptor-table pointer).
- **8 locked, 9 locked too** — a materially different diagnosis than
  everything built so far: the function runs fine in both states, so the
  block is *inside* it, downstream of entry. Leading suspect: the
  `0x400A6994` "is this control usable" gate and its bail to `0x400554D4`,
  which no prior session has ever looked at. New target, not yet explored
  at all.
- **8 unlocked, 9 unlocked** — dead end, same shape as `0x400624FC`. This
  whole lead (the descriptor table, `0x40055008`) is not on the ordinary
  encoder-turn path either, and the real path has to be found from a
  different starting point — most plausibly by first finding *any*
  confirmed caller of the per-page `E` pointers `docs/PARAM_PAGES.md`
  already documents, and tracing forward from there instead of backward
  from a guess.

## OT3.P5 — hardware result: `0x40055008` runs unheld, never held (2026-09-01/02)

Tested on the LFO (MIDI) page, step 1. The two probe slots (8, 9) land on
that page's third and fourth knobs — `SPD3` and `DEP1` — purely as a side
effect of the fixed page order the firmware's own resolver uses (NOTE, LFO,
ARP, CTRL1, CTRL2; NOTE takes flat slots 0-5, so LFO's six knobs are 6-11,
putting `SPD3` at 8 and `DEP1` at 9). Nothing about the parameter names
themselves is significant — they're just where those two arbitrary counters
happened to fall.

**Result: `SPD3` (param 8, unheld) locked with a value that tracked the
number of turns. `DEP1` (param 9, held) showed no lock at all — checked and
confirmed explicitly.**

This is decisive and lands on the first of P5's three predicted outcomes:
**the real apply function runs for an ordinary turn, and is never entered at
all while A or B is held.** Since the hook fires at the function's own
prologue — before anything inside it, including the `0x400A6994` gate, has a
chance to run — a hold-state check inside the function is now ruled out as
the cause. The block is entirely upstream: **whatever decides to make this
call in the first place skips the call outright when a scene is held.**

That reframes the search cleanly. Three sessions of dead ends
(`0x400624FC`, `0x40055304`-as-if-a-function, OT3.18, OT3.19) all guessed at
*downstream* code and never found the actual gate. The gate has to be at or
before the call site — the still-unidentified code that reads a handler
pointer out of the 22-byte-per-parameter descriptor table at `0x400c085c..`
and does the indirect `jsr`. That call site is the new, sole target.

**Next step, not yet done:** find every code site that reads `SCENE_HELD`
(`0x460D169C`) as a literal and inspect each one for an indirect call
(`jsr (aN)`) nearby — the caller of `0x40055008` should be exactly the site
that checks hold state and conditionally skips a `jsr (aN)` rather than the
`jmp`/`bcc` shapes every prior session already ruled out. This is a fresh,
narrower search that hasn't been run yet.

## Hunting `0x40055008`'s caller — three leads chased and ruled out (2026-09-02)

`0x40055008` has zero literal references as a `jsr abs.l` target anywhere in
the image (confirmed by the same byte search used throughout this doc), so
the call is either indirect through a register or via a displacement form
the disassembler would have shown if it were nearby — and it wasn't, in
every window disassembled so far. Three specific hypotheses for the
mechanism, each checked directly against the image rather than assumed:

1. **The per-encoder handler table.** `PARAM_PAGES.md §2` documents six
   handler pointers at each page descriptor's `E+0x00..E+0x14`, "usually
   `0x40038d94`". Checked the real LFO (MIDI) descriptor (`E = 0x400d412a`)
   directly: all six are `0x40038d94`, confirming the existing doc. **Ruled
   out as the path to `0x40055008`**: disassembled `0x40038d94` in full — it
   is exactly what it was already documented as, a standalone delta-to-range
   clamp utility (calls `0x400209d4`, does a couple of `divs.l`, clamps,
   returns). It does not call `0x40055008`, or anything else, internally.
2. **The 22-byte descriptor table at `0x400c085c`.** This is real and
   decodes cleanly, but tracing `FUN_400326d4` (`PARAM_PAGES.md`'s
   documented "stages a page" function, confirmed by disassembly here too —
   it loops six parameters calling `FUN_400a6994` exactly as documented)
   shows it works with a **different**, per-invocation scratch array (passed
   in as an argument, one entry per parameter, fields at `+6`/`+0xa`/`+0xe`/
   `+0x12`) that only coincidentally shares the 22-byte stride — not the
   same structure as the fixed table at `0x400c085c` at all. That table's
   real owner (which page or subsystem it actually belongs to) is still
   unidentified; it is not `PARAM_PAGES.md`'s per-page table (that lives at
   `0x400d2e52+n*0x192`, ~73 KB away) and not the LFO(MIDI) page's own
   `E+0x00` array (confirmed `0x40038d94` x6, above).
3. **A system-wide search for the `moveq #$16,dN` / `muls.l` idiom** (the
   exact pattern `FUN_400326d4` uses for its own, unrelated 22-byte array)
   turned up 130+ hits across the image — far too many to hand-triage, and
   `0x16` (22) is common enough as an unrelated multiplier that this search
   isn't narrow enough to be useful as-is. Not pursued further this session.

**Where this leaves things:** the caller of `0x40055008` is confirmed real
(hardware-tested, runs for an unheld MIDI turn) but has resisted three
separate static-tracing approaches in one session. The cost of continuing
blind static search is starting to outweigh its hit rate. Two honest options
for the next session, not yet chosen between:

- Keep tracing statically — the next reasonable idea is filtering the
  130+ `muls`-by-22 hits by checking which ones sit near a reference to
  `DISPLAY_TRACK`/`PLOCK_PAT` or `0x460d1684` (the unnamed global `0x40055008`
  itself reads right before branching on the MIDI flag), rather than
  chasing all of them blind.
- Find the raw encoder-turn entry point from the hardware side instead of
  reasoning backward from the apply function — i.e. locate whatever code
  runs on *every* encoder interrupt/poll, before any page-specific
  dispatch, and hook that directly with a held/unheld split counter. This
  hasn't been attempted and no address for it is known yet either; it would
  need its own search from scratch, not a shortcut.

Neither is started. Documenting the dead ends now so a future session (or a
cheaper model) doesn't re-spend time re-discovering that `0x40038d94` and
`FUN_400326d4`'s array are not the answer.

## Static trace: encoder event -> `0x40055008` (2026-09-02)

P5 hardware already fixed the symptom: `0x40055008` runs unheld, never held.
This session traced forward from the encoder dispatch side (not backward from
`0x400624FC`, `0x40038d94`, or OT3.19 SCENE_HELD suppression — all ruled out).

### `0x40033250` — not on the apply path

`0x40033250` is a CTRL1-page class handler. It resolves bank/pattern/track,
checks pattern trig bits, and either `bra.w 0x4003240c` (CC routing) or
returns. **No call or data path to `0x40055008`.** Dead end for MIDI scene
apply, same as prior sessions concluded.

### Overlay apply path (unheld MIDI turns)

| Step | Address | What |
| --- | --- | --- |
| 1 | `0x400bf38a` | Jump table entry -> `0x4005578c` |
| 2 | `0x4005578c` | Page/param encoder handler |
| 3 | `0x40055720` / `0x40055728` | Param index via `0x400a7280` |
| 4 | `0x4005574c` | `tst.l $8(*0x400bcd14)`; if zero -> overlay |
| 5 | `0x40055776` | `jsr 0x400554e0` (overlay staging) |
| 6 | `0x400554e0` | `pea 0x400c085a`; `jsr 0x400326d4` (x4) |
| 7 | `0x400c085c` | 22-byte records; handler at +0 = `0x40055008` |
| 8 | `0x4004d948` | Overlay apply loop (`link` frame on a6) |
| 9 | `0x4004e5d8` | `move.l d0, -$40(a6)` apply-enable flag |
| 10 | `0x4004e6fc` | `tst.l -$40(a6)` |
| 11 | `0x4004e700` | **`beq.w 0x4004e7a8`** — skip when flag clear |
| 12 | `0x4004e7a0` | `jsr (a0)` — indirect call to staged handler |
| 13 | `0x40055008` | Real generic apply (P5 prologue hook) |

The `-$40(a6)` flag is built at `0x4004e5d8` from `0x400A6994` usability
bits OR'd with logic keyed on `0x460D1694` (scene morph state — **not**
`SCENE_HELD` at `0x460D169C`). No literal `tst (0x460d169c)` exists between
`0x4004d948` and `0x4004e7a0`.

Alternate branch at `0x40055768` (`jsr 0x400322f0` -> `0x40032228` jmp table)
exists when `*bcd14+8` is non-zero; stock `0x400bc6c0` is zero so unheld MIDI
overlay turns use `0x400554e0`, not `0x400322f0`.

### OT3.P6 — built, awaiting hardware

`tools/build_ot3_p6.py` hooks `0x4004E6FC` (8 bytes: `tst.l -$40(a6)` +
`beq.w` that skips the indirect apply at `0x4004E7A0`). Same param 8/9
unheld/held counters as P4/P5. Flashed as `OT3.P6.bin` (`1.40OT3P6`).

**First build bug (fixed):** the cave replayed `tst`/`beq` then always
`jmp`ed to `0x4004E706`, skipping stock `tst.l d0` at `0x4004E704`. That
corrupted the overlay apply loop (SRC params blank, MachineDrum-style arrows,
`error` on button press). Fixed: cave now `beq` -> `0x4004E7A8` or `jmp`
`0x4004E704`. **Recover with stock `1.40C` before reflashing the fixed
build.**

Predicted readings:

- **8 locked, 9 not** — held turns never reach this gate; block is still
  upstream (before `0x4004E6FC`).
- **8 locked, 9 locked** — gate runs both times; `beq` at `0x4004E700` skips
  `jsr (a0)` when held (`-$40(a6)==0`), matching P5 without entering
  `0x40055008`.

## OT3.P6 — hardware result: both params dark (fixed build)

After recovering from the first broken P6 cave, the fixed build booted clean
(no SRC corruption). Step 1 params **8 and 9 both unlocked** on MIDI tracks —
the hook at `0x4004E6FC` never ran.

Interpretation: P5 already showed `0x40055008` runs unheld; this hook sits on
the **overlay-only** path (`*0x400bcd14+8 == 0` → `0x400554E0` → `0x4004D948`).
Encoder dispatch at `0x40055728` uses **`jsr 0x400322F0`** when overlay `+8`
is **non-zero** (typical once a MIDI page is active). That path reaches
`0x40055008` without ever executing `0x4004E6FC`.

## OT3.P7 — hardware: SPD3 = 1 once per new track

Hook was `jsr 0x400322F0` **inside** `0x40055720` (reached only from the
`0x4005578C` setup path). Result: param 8 (SPD3) = **1** on a fresh MIDI
track, then no further bumps; knobs still moved; held path never lit DEP1.

Interpretation: after overlay `+8` is live, same-page encoder events **skip**
`55720` (`0x40055814`). Ongoing deltas do **not** go through that jsr.

Encoder jump-table records (e.g. at `0x400bf384`) list **`0x400322F0` as
slot 0** and `0x4005578C` as slots 1/2. Ongoing apply calls `322F0` **directly**
from the table — bypassing P7's hook — which is how P5 still saw `55008` on
every unheld turn.

P6 was also the wrong fork: `0x4004E6FC` sits on the **audio** redraw path
inside `0x4004D948` (after `beq` at `0x4004E1E6` when MIDI). MIDI never reaches it.

## OT3.P8 — built: hook `0x400322F0` prologue

`tools/build_ot3_p8.py` — same param 8/9 counters. Flashed as `OT3.P8.bin`
(`1.40OT3P8`). Catches **every** entry to the apply dispatcher (table slot 0
and the rare `55720` path).

Predicted:

- **8 ~= turn count, 9 empty** — live path; hold skips `322F0` entirely.
  Next: find the jump-table dispatcher that omits slot 0 when `SCENE_HELD`.
- **8 and 9 both count** — `322F0` runs while held; gate is between it and
  `55008` (inside `32228` / page handlers).
- **both dark** — unexpected; revisit.

## OT3.P8 — hardware: same one-shot as P7

`0x400322F0` prologue lit SPD3 intermittently once, then stayed dark while
knobs still moved and P5-style apply still happens. So `322F0` is **not** the
every-turn path either (setup / rare only).

## Ghidra headless (WSL) — caller of `0x40055008` (2026-09-04)

Project: `/home/LN/ghidra_setup/proj/gnd_re` (Ghidra 11.2.1 + JDK 21 portable).

### Static facts

| Fact | Result |
| --- | --- |
| XREFs to `0x40055008` | **0** (no `jsr abs`) |
| Dword embeds of `0x40055008` | 6× in table `@0x400c085a` (22-byte records, handler at **+2**) |
| Who mentions table base | only `FUN_400554e0` → `FUN_400326d4` (staging, does **not** call handler) |
| `movea.l 2(An),A0` + `jsr (A0)` in whole image | **one site**: `0x40062454` / `0x40062460` |

### The call site

Inside `FUN_40061a94`, switch on event type (`switch(*event - 1)`), **case `0x2B`**:

```
40062454  movea.l 2(a2), a0     ; handler
40062458  tst.l   a0
4006245a  beq.b   skip
4006245c  move.l  6(a2), -(sp)  ; arg
40062460  jsr     (a0)          ; → 0x40055008 when MIDI table staged
```

Decompiler:

```c
case '*':  /* type byte == 0x2B */
  if (*(code **)(pcVar6 + 2) != 0)
    (**(code **)(pcVar6 + 2))(*(undefined4 *)(pcVar6 + 6));
  ...
```

**P4 hooked `0x400624FC`** — a *different* case in the same function (MIDI flag →
`0x40054CD8` / scene-held → `0x40052ae8`). That case never runs for MIDI
encoder turns; the neighboring **case `0x2B` at `0x40062454`** is the only
firmware site that performs the table-shaped indirect call.

### `SCENE_HELD` (`0x460D169C`) readers (complete, n=11)

Press/release writers: `0x400434BE`, `0x40054CBC`.

Readers: `0x40034350`, `0x400346A4`, `0x40034880`, `0x40034A44`,
`0x40052AE8`, `0x40061A94` (@`0x40062574` → audio `0x40052ae8` only),
`0x40062DA0`, `0x40062E84`, `0x40062F60`.

None of those checks sits on the `0x40062454` case body. If held MIDI turns
never reach `0x40055008`, the gate is **upstream**: type-`0x2B` events are not
posted (or are posted with a null handler) while A/B is held.

### Next probe — OT3.P9 built

`tools/build_ot3_p9.py` hooks **`0x40062454`** (6 bytes: `movea.l 2(a2),a0` +
`tst.l a0`), same param 8/9 counters. Flashed as `OT3.P9.bin` (`1.40OT3P9`).

Expected:

- **8 counts, 9 dark** — live unheld call; hold skips posting / this case.
  Then find the type-`0x2B` poster that omits the event when `SCENE_HELD`.
- **both dark** — unheld apply uses another addressing form; revisit.
- **both count** — runs held too; gate is inside `0x40055008` (unlikely given P5).

## OT3.P9 — hardware: both dark (2026-09-04)

SPD3 (8) and DEP1 (9) unlocked after unheld + held turns. **`0x40062454` is
not on the every-turn MIDI apply path** (same miss class as P6–P8). The
table-shaped indirect call is real but unused for ordinary encoder turns.

## OT3.P10 — built: capture return address at `0x40055008`

Static hunt still cannot find the register-indirect caller (`55008` only
appears as table data). P10 hooks the `55008` prologue and on the **first
unheld MIDI hit** writes `(ret - 0x40000000)` into params **8..11** as four
7-bit digits (MSB first). Held hits bump param **7**.

`tools/build_ot3_p10.py` → `OT3.P10.bin` (`1.40OT3P10`).

Report params 7,8,9,10,11. Reconstruct:

`addr = 0x40000000 + (((((p8<<7)|p9)<<7)|p10)<<7)|p11`

## OT3.P10 — first flash bug; P10b hardware result (2026-09-04)

P10 wrote param indices (8,9,10,11) because `cell_addr` clobbered the digit
in `d2`. Fixed as **P10b** (`1.40OT3P10b`).

Hardware (unheld, first turn): **SPD3=0, DEP1=24, DEP2=60, DEP3=6**
→ return address **`0x40061E06`**.

### Live call chain (decoded)

```
FUN_40061a94  case type 2 (case '\x01')
  40061e00  jsr  0x40031944(enc_idx)
  40061e06  bra  exit          ← P10 return address

FUN_40031944
  a1 = *(0x46c7dede + enc*0x14)   ; RAM handler table
  jmp (a1)                         ; TAIL CALL → 0x40055008
```

So ordinary MIDI encoder turns do **not** use case `0x2B` / `0x40062454`
(P9). They use **case type 2 → `31944` → jmp through `46c7dede`**.

`FUN_4003125c` fills `46c7dede` from the 22-byte overlay records
(`*(record+2)` = `0x40055008` after `554e0`/`326d4` staging via keymap
install `31494`).

## OT3.P11 — hardware: `0x40031944` runs held AND unheld (2026-09-04)

`tools/build_ot3_p11.py` → `OT3.P11.bin` (`1.40OT3P11`).

Hardware: **SPD3=50** (param 8, unheld), **DEP1=57** (param 9, held).

Entry of the RAM-table dispatcher is **not** gated on `SCENE_HELD`. Combined
with P5 (`0x40055008` never held): the skip is **inside** `31944` after the
prologue — either early exit (`enc>7` or null `*(46c7dede+enc*0x14)`), or
`jmp (a1)` to a handler that is not `0x40055008`.

## OT3.P12 — hardware: held also takes `jmp (a1)` (2026-09-04)

`tools/build_ot3_p12.py` → `OT3.P12.bin` (`1.40OT3P12`).

Hardware: **SPD3=35** (param 8, unheld jmp), **DEP1=51** (param 9, held jmp).
(SPD1=64 on one run only — not written by this probe; ignore as leftover.)

Held takes the non-null `jmp (a1)` path. Combined with P5 (`55008` never
held): **while held, `a1` is not `0x40055008`.**

## OT3.P13 — hardware: held jmp target = `0x40053498` (2026-09-04)

`tools/build_ot3_p13.py` → `OT3.P13.bin` (`1.40OT3P13`).

Hardware: **SPD2=18** (param 7, unheld count OK), **SPD3=0, DEP1=20,
DEP2=105, DEP3=24** →

`addr = 0x40000000 + (((((0<<7)|20)<<7)|105)<<7)|24` = **`0x40053498`**.

### What that address is

`0x40053498` is one of the five **audio** encoder editors (same family as
`52ae8` / `52e98` / …). ROM overlay table `@0x400bae84` (22-byte records)
points every slot’s handler at `53498`. The MIDI table `@0x400c085a` points
at `0x40055008` instead. Staging at `0x400554e0` pea's **both** tables into
`326d4`/`3125c`.

Early in `53498`:

```
400534ce  tst.l  (0x80000012).l    ; MIDI_FLAG
400534d4  bne.w  0x40053a5c        ; → movem/lea/rts  (no-op)
```

So on a MIDI track, held turns **do** reach a handler — the wrong one —
and that handler **returns immediately**. That matches P5 (`55008` never
held) and the live “knob does nothing while A/B held” behaviour.

### What puts `53498` in the slot (static, 2026-09-04)

`46c7dede` is rebuilt by `FUN_4003125c` from linked list `0x460d165c`.
Later nodes overwrite earlier ones for the same enc index.

| Node | `node+8` table | Handler |
| --- | --- | --- |
| Boot MIDI `0x400c091e` (installed `@0x40061bda`) | `0x400c085a` | `0x40055008` |
| Scene A keymap `0x400bb2a2` | `0x400bae84` | `0x40053498` |
| Scene B keymap `0x400bb2b6` | `0x400bb1f2` | `0x40052e98` |

Scene A button record `@0x400bff30` (stride `0x1a`):

- `+08` press `0x4004348c` — sets `SCENE_HELD`
- `+0c` release `0x40054ca4` — clears `SCENE_HELD`
- `+14` keymap **`0x400bb2a2`** — framework calls `FUN_40031494` /
  `FUN_4003146c`

`SCENE_HELD` readers never rebuild the keymap; the button’s keymap pointer
is a sibling of the flag. Appending `bb2a2` after the MIDI node is what
replaces `55008` with `53498` in `46c7dede`.

**Fix direction (not built):** skip installing `bb2a2` when `MIDI_FLAG`, or
replace `53498`’s MIDI early-out with a MIDI scene-store path / tail into
`55008`. Do not suppress `SCENE_HELD` (OT3.19 dead end).

## OT3.P14 — hardware: no SPD3 on hold A (2026-09-04)

Exact ROM pointer `0x400bb2a2` never matched at `31494`. Button path at
`0x40058bd8` pushes `+0x14` into `5829c` and may install a **different**
node pointer via `31494`.

## OT3.P14b — hardware: `31494` runs on A/B, but not `bae84` (2026-09-04)

SPD1 (param 6) = **2** on first hold A; same for B; each further hold
**+1**. Params 7 and 8..11 stayed dark → installs happen, but
`*(arg+8) != 0x400bae84`. The ROM `bb2a2` story is not what `31494`
receives (or node layout differs).

## OT3.P16 — hardware: second `31494` arg = `0x400bee74` (2026-09-04)

SPD1=2, SPD3=0, DEP1=47, DEP2=92, DEP3=116
→ last arg **`0x400bee74`** (keymap node, `+8 = 0x400bedc4`).

`bedc4` handlers are `0x400508e4` / `0x400434d8` — **not** `53498`.
So the last install on hold A is not the scene-A `bae84` node.
First of the two calls still unknown.

## OT3.P17 — hardware: captured boot node, not hold-A (2026-09-04)

Reported **0,48,18,30** (and note locks may pre-exist) → **`0x400c091e`**,
the boot MIDI keymap install. Once-flag fired at startup; hold-A args never
recorded. SPD2=18 was likely DEP2 of that same quartet (or P13 leftover).

## OT3.P18 — hardware: nothing lit (2026-09-04)

`SCENE_HELD` gate on `31494` was wrong: keymap install runs **before** the
press handler sets the flag. Earlier probes (P14b/P16) did not use that gate.

## OT3.P19 — hardware: SPD1 only (2026-09-04)

Non-boot `31494` counted, but 8..11 stayed dark: RAM once-flag had already
fired earlier; clearing locks wiped the fingerprint.

## OT3.P21 — hardware: held jmp = `0x40053498` (2026-09-04)

SPD2=26 (unheld OK). **SPD3=0, DEP1=20, DEP2=105, DEP3=24** → **`0x40053498`**.

Live held handler is still the audio editor that **MIDI-bails** at
`0x400534ce` / `bne 0x40053a5c`, even though press-time `31494` installed
`bee74`/`508e4`. Something leaves `53498` in `46c7dede` for the turn.

**Fix target (confirmed):** replace that MIDI early-out with MIDI scene-store
(and/or unwind + `jmp 0x40055008` so the turn applies). Do not use
`0x4006257C` (P4 dark).

## OT3.22 — built: MIDI+held → `0x40055008`

`tools/build_ot322.py` → Desktop `OT3.22.bin` (`1.40OT322`).

Hook `0x400534ce` (10B `tst MIDI` + `bne bail`) → stub `@0x400D6600`:
- MIDI==0 → `jmp 0x400534d8` (audio unchanged)
- MIDI && !SCENE_HELD → `jmp 0x40053a5c` (stock bail)
- MIDI && SCENE_HELD → unwind frame → `jmp 0x40055008`

**Test:** MIDI track, hold A, turn LFO knob — value should move (stock: frozen).
MSC grey/morph store still next.

## OT3.22 — hardware: bricks on A+LFO (2026-09-04)

Stub used `lea 0x18(a7)` after restoring 9 longs. Stock epilogue is
`lea 0x24(a7)` (`4fef0024`). Stack off by 12 → hang/brick.

## OT3.23 — built: same redirect, correct frame pop

`tools/build_ot323.py` → Desktop `OT3.23.bin` (`1.40OT323`).
Identical to OT3.22 except `4fef0024`.

## OT3.23 — hardware: still crashes (2026-09-04)

Frame size was not the only bug. Mid-function redirect ran `2ea84` /
`6dbcc` before `55008`; unheld never does.

## OT3.24 — built: redirect at `53498` entry

`tools/build_ot324.py` → Desktop `OT3.24.bin` (`1.40OT324`).

Hook prologue only: MIDI+held → `jmp 0x40055008` with original stack.
Else stock `lea`/`movem` → `0x400534a0`. No patch at `534ce`.

## OT3.24 — hardware SUCCESS (2026-09-04)

MIDI parameters move while scene A/B is held. Audio scene hold-edit still
works. Confirmed: live held handler was `53498`; clean entry redirect into
`55008` is the correct fix (mid-function unwind in OT3.22/23 bricked).

## OT3.25 — built: store + indicators on the working path

`tools/build_ot325.py` → Desktop `OT3.25.bin` (`1.40OT325`).

Stacks OT3.24 entry redirect + OT3.18 MSC store at `0x40055326` + OT3.17
track/page indicator gates. Track-8 seed control unchanged. Morph still held.

## OT3.25 — hardware (2026-09-04): store lights, dial sits still

MIDI track 8, hold A, turn params: **values do not move**, but **params that
were turned blink** (lock indicator). That matches OT3.18: write goes to MSC
only (`a5` redirected); live `8f162` is not updated, so the dial number stays
put while the indicator scan sees the new non-`0xff` MSC cells.

Interpretation: **entry redirect + store + indicator path are live.** Next:
confirm same blink on track 1 after one detent (not only the track-8 seed),
then either morph or a held-display follow so the number tracks the lock.

## OT3.26 — built: per-pattern store + dial + morph (2026-09-04)

`tools/build_ot326.py` → Desktop `OT3.26.bin` (`1.40OT326`).

OT3.25 cave MSC was machine-global → locks blinked across Parts. OT3.26 stores
MIDI locks in the stock per-pattern scene cells (`8f3e2`), same addressing as
audio, so Part/pattern changes scope locks correctly.

- Hold-edit still reaches `55008` (OT3.24 entry)
- Live `8f162` write kept → **dial moves** while held
- Extra write into `8f3e2` when `SCENE_HELD` → lock persists with the pattern
- Indicators use the audio `8f3e2` path (no MSC)
- XF morph lerps scene A/B from `8f3e2` into MIDI sound tables

Caveat: MIDI and audio share that track’s scene slots; switching machine type
on a track can leave stale cells. Greying relies on stock `320A0` (reads
`8f3e2`) when the UI asks.

## OT3.26 — hardware: A moves, B stuck, no blink/grey (2026-09-04)

Indicators jumped to the MIDI `bne` skip (still skipped `8f3e2`). Grey hold-UI
at `0x40034754` also skips MIDI. B may not use `53498`, so entry redirect missed.

## OT3.27 — built: dispatcher force + real indicator/grey path

`tools/build_ot327.py` → Desktop `OT3.27.bin` (`1.40OT327`).

- `0x40031964`: MIDI+held → `a1=0x40055008` (A and B)
- Indicators → `343C4` / `34466` (audio `8f3e2` body)
- `0x40034754` nop → MIDI hold-UI greys from `8f3e2`
- Dual-write + morph kept

## OT3.28 — built: MSCN-style mix (2026-09-04)

`tools/build_ot328.py` → Desktop `OT3.28.bin` (`1.40OT328`).

MSCN mixes `8f3e2` A/B×XF at emit time and does not fight the knob while
held. OT3.27 morph re-applied scene A over live during hold-B (XF at A) →
stuck. OT3.28: morph **skips while `SCENE_HELD`**; when free, lerps locks into
`8f162` / `52b0` / `76dc0` and sets `100f8598` dirty so MIDI follows scene/XF.

## OT3.28 — hardware: brick at startup (2026-09-04)

Custom morph rejected. Rolled back.

## OTMIDI1.0 — built from clean 1.40C

`tools/build_otmidi10.py` → Desktop `OTMIDI1.0.bin` (`1.40OTMIDI1`).

Fresh extract of stock 1.40C. Hold-edit only (dispatcher→55008, dual-write
`8f3e2`, indicators, grey nop). **Morph not hooked.** Step 1: confirm A and B
knobs both move while held.