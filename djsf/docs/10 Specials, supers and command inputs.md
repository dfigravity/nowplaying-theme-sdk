# 10 · Specials, supers and command inputs (proposal, 2026-10-06)

Triode's framing was that combos of DJ actions should trigger special abilities. `02` already turns
single gestures into **moves** and chains of moves into a **combo** counter. This doc adds the
layer between them, the one a fighting game calls a **command input**. A special is a short,
ordered sequence of moves inside a tight musical window. It reads like a quarter-circle plus
punch, and it pays out a named ability with its own visual. A **super** is a special done with a
full HYPE meter.

Everything here is a proposal for Osh and Triode to cut down. Names are ours, not Capcom's.

## 1. How a special is recognised

- A special is a pattern over the move stream that `02` §3 already produces. It is not a new
  gesture detector, so it runs in the theme even when recognition of the base moves moves into
  NP3.
- Each step names a move (or a move on a particular channel relation, such as "the other deck").
  The whole sequence must land inside its window, measured in bars or beats like everything else.
- When a special completes, it **consumes** its steps. The individual moves still count as hits,
  but their callouts merge into the special's callout, so one action produces one big name on
  screen.
- A special adds `+1` hit for itself plus its own points, resets freshness like any Special-tier
  move, and freezes the HUD for 10 frames instead of 6. (SF2 used 14 frames of hit-stop. Ours is
  shorter because the music keeps going.)
- Specials are gated by capability exactly like moves (`02` §3.3). The HUD's move list shows only
  the specials the rig can perform.

## 2. Specials

"Today" means every step is detectable from `np:mix` + `np:track` as measured in `01`. "Events"
means it needs the NP3 event stream proposed in `03`.

| Special | Command (in order) | Window | Pts | Needs | Visual (asset) |
|---|---|---|---|---|---|
| **SUB CANNON** | hold LOW KILL on the outgoing deck ≥ 1 bar ("charge") → FADER SLAM the other deck → its LOW back to flat | slam and release within 1 beat | 120 | today | bass bomb 24×24 flies across the top band into the CHAT bar, 48×48 burst (v3 `chat` sheet, reuse) |
| **CROSSFIRE** | QUICK CUT A→B → QUICK CUT B→A → QUICK CUT A→B | 2 bars | 100 | today | three slash streaks across the camera-safe edge, small sparks at each cut |
| **FULL HANDOVER** | BASSLINE SWAP + VOCAL SWAP + HIGH swap between the same two decks, any order | 8 bars | 140 | today | three swap arrows stack, then merge into one gold arrow |
| **BLACKOUT DROP** | FULL KILL on every on-air channel held ≥ 1 beat → THE DROP | 2 bars | 160 | today | 60 % darken while killed, then a white super-flash frame on the drop |
| **THE LONG GAME** | LONG BLEND (≥ 32 bars) → CLEAN TRANSITION | ends the blend | 150 | today | slow gold sweep along both bars; banks the combo with +25 % |
| **LEVEL UP** | HARMONIC MIX and ENERGY BOOST on the same transition | the transition | 90 | today | numerals flash and step up one LUT tier for 2 bars |
| **RISING STORM** | HIGH PASS RISER → THE DROP | 1 bar | 150 | events (`filter`) | 32×64 lightning arc rising from the callout (v2 `fx`) |
| **SPIN CYCLE** | BACKSPIN → QUICK CUT or FADER SLAM on the other deck | 1 bar | 140 | events (`jog.backspin`) | spinning mini-record projectile (8×8 dizzy record, scaled 2× by sprite, v2) |
| **ECHO SLAM** | ECHO OUT on A → FADER SLAM B on the one | 1 beat after the tail | 130 | events (`fx`, `beat.tick`) | callout leaves 3 afterimages fading −4/−8/−12 px |
| **CUE STORM** | HOT CUE JUGGLE → LOOP ROLL → release | 4 bars | 150 | events (`pad`, `loop`) | pad-grid flicker of sparks behind the combo block |

Why these six for today: every step in the first six was either proven on the 2026-10-06
recording (BASSLINE SWAP, FULL KILL, FADER SLAM, EQ SWEEP IN, HIGH DUCK) or uses the same
primitives. That means specials ship in Phase 1, with no dependence on Triode.

## 3. Supers

- **Arming:** the HYPE meter is full (`02` §4). "MAX" flashes 8 frames on, 8 off.
- **Firing:** the next **special** fires its super version. (In `02` today, any Technical+ move
  fires a super. This proposal makes supers a reward for a special, and a plain Technical+ move
  still fires one after 32 bars of waiting so the meter never sits full forever.)
- **Super sequence (frames at 60 fps):**
  1. Freeze for 14 frames: the HUD stops and the bars pop white for 2 frames.
  2. Darken the stage to 60 % for 12 frames. Only the HUD stays lit.
  3. Cut-in: the mascot's super pose (v2 `mascot`) slides in on a 96×64 panel, plus a `SUPER!`
     callout in the white LUT.
  4. The special's name in the red LUT with a 3× pop.
  5. 3 px shake for 10 frames, up to 12 sparks.
  6. 8 bars of ×2 points with the HYPE meter draining visibly.
- **Names:** the special's name with a prefix. Default prefix **HYPER**, as in HYPER SUB CANNON
  and HYPER CROSSFIRE. One word to letter, and generic, not a Capcom term.
- **Damage (v3):** a super deals 40 % to chat (`02` §5). A non-super special deals `points / 10`
  like any move.

## 4. Finishers and reactive callouts

These are borrowed from fighting-game convention, and every word is generic.

| Callout | Trigger | Why it is fun |
|---|---|---|
| **FIRST ATTACK** | first move of each track, once the 8-bar intro immunity ends | marks the start of every "round" |
| **REVERSAL** | any move within 1 bar after chat lands damage (v3) | the DJ answers chat on the spot |
| **COUNTER** | a special within 1 bar after chat lands damage (v3) | ×1.5 points on that special |
| **ULTRA FINISH** | at 25+ hits, close the combo with CLEAN TRANSITION or DOUBLE DROP | KI-style ender: +10 bonus hits counted up rapidly, rank word flashes, then the bank |
| **PERFECT** | track ends with the DJ's bar untouched (v3) | already in `02` |
| **DIZZY** (chat side) | three specials land on chat inside 8 bars | the crowd strip gets orbiting mini-records for 2 bars, and chat damage is halved |

## 5. Command list on screen

Fighting games teach inputs with a move list. We can show one compactly:

- While no combo is running and nothing has happened for 16 bars, the ticker alternates
  NOW PLAYING with one special's command line, written in icons:
  `SUB CANNON  [EQ-LOW KILL] hold ▶ [FADER ▲] ▶ [EQ-LOW ↺]`.
- This needs a small **command icon set**: 8×8 icons for fader up, fader down, fader slam, EQ
  kill, EQ restore, filter up, filter down, jog spin back, pad hit, loop, and "hold". It's a v2
  add of about 12 frames in the `hud` sheet. Text versions work today through `font8`.
- The list reflects the rig's capabilities, so a Prime 4 user never sees BACKSPIN-based
  specials.

## 6. What the art needs (beyond `08`)

| Asset | Phase | Notes |
|---|---|---|
| Callout words for every special | v1 | already covered: the `callout_font` BMFont prints any name |
| `SUPER!`, `HYPER`, `FIRST ATTACK`, `REVERSAL`, `COUNTER`, `ULTRA FINISH` | v1 | same font; the white and red LUT rows exist in `lut.png` |
| Command icon set 8×8 × 12 | v2 | **done** (`fx` sheet, `icon_*`) |
| Super cut-in panel 96×64 (8 frames) | v2 | listed in `08` v3 as "chat cut-in"; make one shared frame for both sides |
| Slash streak 64×8 (4 frames) for CROSSFIRE | v2 | **done** (`fx`, tag `slash`) |
| Swap arrows 16×16 (3 frames) for FULL HANDOVER | v2 | **done** (`fx`, tag `swap_arrows`) |

## 7. Questions for Osh

1. Which specials match how you actually play? Cut the list to 4–6 before tuning.
2. Do supers need a special, or may any Technical+ move fire them as in `02`?
3. Prefix word for supers: HYPER, or something of yours?
4. Is the idle command-list in the ticker welcome, or noise on stream?
