# 02 · Game design (v0.1 draft, 2026-10-06)

Depth and sources: `research_notes/game_mechanics.md`. This doc is the decision layer on top of it.
Defaults marked **[default]** are ours to tune; items marked **[decide]** need Osh (or Osh + Triode).

## 1. Core loop, one paragraph

The DJ plays. Every deliberate controller gesture that we can name is a **move**. Moves within a
musical window chain into a **combo** with a hit counter; the counter crosses fixed thresholds that
trigger announcer-style tiers, and each tier makes the overlay louder (colour, sparks, lightning,
fire border, super flash). Idle lets the combo "drop": the counter wobbles, a 2-bar countdown drains,
then the combo is **banked** (points kept, counter reset to 0). Points fill a **HYPE meter**; a full
meter fires a SUPER on the next real move. Later (v3), chat becomes P2: bits, subs, channel points and
a free `!punch` take chunks off the DJ's health bar; the DJ's moves hit back; rounds end on KO or at
track end; PERFECT if untouched.

Design principles we are following (from the precedents): count only deliberate actions; use bars
not seconds; fixed, named, visible tiers; score = base × freshness × scaling × variety; show the drop
coming; bank rather than zero; feedback within 100 ms with the move name on screen.

## 2. Time base

- `beat = 60 / bpm`, `bar = 4 beats`, `phrase = 8 bars`. BPM comes from the on-air deck's track.
- Without a beat-phase event we approximate: anchor a bar clock on the on-air deck's last play/cue
  edge and re-anchor on each one. "On the one" bonuses stay off until NP3 sends `beat.tick`.
- All windows below are in bars and converted at the moment the window opens.

## 3. Moves

Thresholds use hysteresis because fader values arrive at ≤10 Hz: closed ≤ 0.10, open ≥ 0.80,
EQ killed ≤ −0.80, EQ flat within ±0.10. Tiers: Basic 10–25 pts, Technical 30–50, Special 60–100,
Ultra 150+.

### 3.1 Detectable today (from `np:mix` state + `np:track`)

| Move | Gesture | Rule (short) | Tier/pts |
|---|---|---|---|
| QUICK CUT | hard cut A→B | A open→closed and B closed→open, both playing, within 1 bar | Basic 20 |
| FADER SLAM | throw a fader open | closed→open in ≤ 250 ms | Basic 15 |
| TRANSFORMER | fader chop | one playing channel crosses 0.5 ≥ 4× in a bar | Technical 30+ |
| BASSLINE SWAP | hand the bass over | L[a] flat→killed and L[b] killed→flat within 2 bars, both open and playing | Technical 40 |
| VOCAL SWAP | same on mids | mirror on M | Technical 35 |
| FULL KILL | kill all three bands | L, M, H all killed within 1 bar on an on-air channel | Technical 30 |
| EQ KILL SWEEP | kill, then bring back in order | after FULL KILL, restore L→M→H within 2 bars | Technical 45 |
| EQ SWEEP IN | slow band restore | a band rises monotonically through ≥ 4 steps within 4 bars | Basic 20 |
| HIGH DUCK | high cut and back | H killed and restored on one channel within 2 bars | Basic 15 |
| THE DROP | everything back at once | channel cut (L killed) ≥ 2 bars, then L back to flat within 1 beat | Special 60 (+40 ON THE ONE, needs beat) |
| CUE STUTTER | cue stabs | cue toggles ≥ 4× in a bar on an on-air deck | Technical 30 |
| DEAD STOP | stop while on air | playing→false while fader open and on air | Basic 15 (proxy for VINYL BRAKE) |
| TRIM BOOST | gain ride | trim +0.2 within a bar while on air, once per track | Basic 10 |
| DOUBLE DROP | two tracks slammed | two channels playing, F ≥ 0.9, L flat, both on air ≥ 1 bar, preceded within 2 bars by a DROP or SWAP | Ultra 150 |
| THREE-DECK STACK | three live | three channels playing with F ≥ 0.5 for ≥ 4 bars (FOUR ON THE FLOOR 200 for four) | Special 100 |
| LONG BLEND | ride two decks | two channels playing, F > 0.5 for ≥ 32 bars; +25 per further 16; extends the combo window | Special 75+ |
| SLOW BURN | patient fade | F rises closed→open over ≥ 16 bars with no reversal > 0.1 | Basic 20 |
| CLEAN TRANSITION | tidy ender | after B ≥ 0.9, A ≤ 0.1 and stopped within 1 bar; banks the combo with +10 % | Technical 35 |
| HARMONIC MIX | key-compatible change | new on-air key is Camelot ±1 same letter, or same number other letter | Technical 40 |
| ENERGY BOOST | key/tempo up | +1 Camelot and/or ≥ 2 % faster | Technical 30 |
| GEAR CHANGE | tempo jump | ≥ 4 % BPM delta between on-air tracks via a QUICK CUT or DOUBLE DROP | Basic 15 |
| CROSSFADER SLAM | throw the crossfader | X from ≤ −0.8 to ≥ 0.8 within 1 beat | Basic 25 (crossfader liveness unverified; Osh does not use it) |

Proven on the real recording (see `01`): BASSLINE SWAP ×2, FULL KILL, FADER SLAM, EQ SWEEP IN,
HIGH DUCK. The rest use the same primitives.

### 3.2 Need NP3 events (see `03 Event protocol proposal.md`)

| Move | Needs | Tier/pts |
|---|---|---|
| BACKSPIN | `jog.backspin` (or `jog.rotate` ≤ 30 Hz with velocity) | Special 80 |
| SCRATCH (BABY / CHIRP / TRANSFORMER SCRATCH) | `jog.rotate` alternations while touching | Technical 40+ |
| VINYL BRAKE | brake / velocity ramp | Special 60 |
| NUDGE | `tempo.bend` on the incoming deck | Basic 10 |
| HIGH PASS RISER / LOW PASS DIVE | `filter` live (FLX10 CFX knob is not mapped today) | Special 75+ |
| FILTER WOBBLE | `filter` ≥ 20 Hz | Technical 35 |
| ECHO OUT | `fx.on/off` + fader out | Special 60 |
| HOT CUE JUGGLE / CUE DRUM | `pad.press` hot cue ≥ 3 in a bar / ≥ 8 in 2 bars | Technical 45 / Special 90 |
| LOOP ROLL, BEAT JUMP | `loop.*`, `beatjump` | Technical 35 / Basic 20 |
| STEM DROP | `stems.toggle` (FLX10 part isolation) | Special 60 |
| CRAB | crossfader ≥ 20 Hz | Special 80 |
| ON THE ONE (×1.5 modifier) | `beat.tick` | modifier |

Overlap rule: evaluate higher tiers first and consume the signal deltas they used, so one gesture
yields one callout. Score nothing while `mixer.sourceId == "simulated"`.

### 3.3 Moves are gated per channel by the rig's capabilities

The FLX10 is one rig. On a CDJ-3000 + DJM-V10 the mixer moves exist only if the DJM's USB MIDI is on,
while jog moves come from the player's 30 ms position stream; on Denon Prime there is no EQ, filter or
jog rotation at all but there is beat phase at 28 Hz; on Traktor hardware there is nothing but the
track. Each move therefore declares its required inputs (fader, eq, filter, jog.rel-or-position,
pads, loops, stems, beatPhase) and is enabled per channel from `np:capabilities` (`06` §D). The HUD
shows the live move list for the rig and the set's possible maximum, so a CDJ set is scored against
its own ceiling. Tier thresholds may scale with the size of the available move set (decide).

## 4. Combo engine [default values]

- **Window:** a move chains if within 8 bars of the previous move. Balance states (LONG BLEND active,
  a loop held, filter held off-centre, ≥ 3 deltas in the last 2 bars) extend the window to a cap of 16 bars.
- **Opener:** the first move must be Technical+ or a QUICK CUT. TRIM BOOST / NUDGE cannot open.
- **Score per move:** `base × freshness × scaling × variety`
  - freshness (THPS): 1.0, 0.75, 0.5, 0.25, 0.1 for repeats of the same move in one combo; any Special resets all freshness.
  - scaling (SF6 compressed): hits 1–3 100 %, 4–6 90 %, 7–10 80 %, 11–15 70 %, 16+ 60 %; floor 100 % for Special and Ultra.
  - variety: `1 + 0.25 × (distinct moves − 1)`, cap ×4.
- **Tiers (hit count → word):** **decided 2026-10-06: set B** (ours): 3 NICE · 6 SOLID · 10 WICKED ·
  15 SAVAGE · 20 LETHAL · 25 MAXIMUM · 30+ ULTRA. (Rejected: A, announcer-style GOOD … KILLER.)
  - Either way the thresholds drive the visual escalation ladder in `04`.
- **Dropping:** with no move for 6 of the 8 window bars → DROPPING: counter shakes, 2-bar countdown bar drains. Any move rescues.
- **Bank:** at expiry the combo is banked, never zeroed: points → set score, HYPE meter, rank bucket; summary flashes ("14 HITS · 2,310 PTS · BEST: BASSLINE SWAP"); counter → 0.
- **Rank (DMC-style letter under the DJ's bar):** leaky bucket 0..1000, D 0 · C 150 · B 300 · A 500 · S 650 · SS 800 · SSS 950; drain 1 pt/beat at D up to 4 at SSS; letter held 16 idle bars before it may fall one step per 8 bars; a chat hit drops it two letters.
- **HYPE (super) meter:** 1,500 banked points = full; Ultra adds a flat 25 %. When full it fires on the next Technical+ move (or after 32 bars on its own): 8 bars of maximum visuals, ×2 points, and (v3) 40 % damage to chat. Then resets.
- **Stats:** per track and per set: best combo (hits, points), total hits, move histogram, max rank, supers, damage taken, PERFECT. Track card for 6 s on `np:track` change.

State machine and pseudo-code: `research_notes/game_mechanics.md` §3.5.

## 5. Chat fight-back (v3) — iteration 2 candidate

Triode, 2026-10-06: iteration 1 is one side only, no PvP; the second side comes in iteration 2
and is not chosen yet (DJ vs chat as below, or DJ vs DJ). Keep this section as the chat option.

- **Source of events [decide]:** (a) NP3 host emits `np:community` (recommended ask). Note NP3's Twitch service today holds chat-post scopes only and the overlay stream carries no community events; but cheers (IRC `bits=` tag), subs/gifts/resubs/raids (IRC USERNOTICE) and chat need no broadcaster scopes when a bot is modded into the channel, which is how Triode's Check-In globe already works, so the cost to him is moderate. Channel points without text input and hype trains need EventSub with broadcaster scopes. (b) Local bridge adapter (Streamer.bot WebSocket on 127.0.0.1:8080 first; Lumia, Mix It Up as alternates). (c) Direct token in the theme: rejected. (d) Anonymous Twitch IRC WebSocket from inside the theme: possible for chat and cheers only, untested against the overlay page's CSP, dev-mode fallback at most.
- **Damage table (deterministic, capped):** 1 bit = 1 HP (cap 500/event); sub T1/Prime 150, T2 250, T3 500; resub tier + 5/month (cap 600); gifts 150 each, 500 cap per bomb; channel points PUNCH 20 / HADOUKEN 80 (5 per user per minute); free `!punch` 5 HP, 30 s per-user cooldown, 60 HP/min global; raid 2/viewer cap 300; follow 10; hype train 100 per level.
- **DJ defence/offence:** each combo hit heals 1 %; tier-ups heal 3/5/10/20/40 %; guard at ≥ 10 hits halves incoming damage; each move deals `points/10` to chat; SUPER deals 40 %.
- **Breaker (optional):** channel-points BREAKER during a 10+ combo banks it at 50 % with the redeemer's name; misuse → KI-style lockout badge and a 3-minute cooldown.
- **Rounds:** one per track, best of 3 per match [decide: or 10-minute rounds]; both bars 1000 HP; time-out → more HP wins; PERFECT; KO sequence (freeze 300 ms, slow flash, "K.O." + finisher name, 4 s hold, round card with top 3 attackers, DJ best combo, rank), then reset; match card after round 3.
- **Fairness:** per-user and global caps above; overflow becomes a longer cinematic not more damage; dedupe by event id; ignore `test` events for scoreboards; 8-bar intro immunity per track.
- **Twitch policy:** reacting to cheers with on-stream effects is allowed; no secondary currency, no wagers or random outcomes tied to bits, no prizes of value; never word it as "buy damage". An OBS overlay is not a Bits-enabled Extension and does not take bits itself.

## 6. Tuning table (ship defaults)

| Parameter | Default |
|---|---|
| Combo window | 8 bars, extended to 16 by balance states |
| Drop warning | last 2 bars |
| Tier thresholds | 3 / 6 / 10 / 15 / 25 / 40 (words: decide) |
| Freshness | 1.0 / 0.75 / 0.5 / 0.25 / 0.1 |
| Scaling | 100 / 90 / 80 / 70 / 60 %, floor 100 % Special+ |
| Variety | ×(1 + 0.25 per distinct move), cap ×4 |
| HYPE meter | 1,500 pts, 8 bars active, ×2 points, 40 % to chat |
| Rank | D C B A S SS SSS, hold 16 bars, −1 per 8 bars, −2 on hit |
| Health | 1000 each, 1 bit = 1 HP |
| Free attack | `!punch` 5 HP, 30 s/user, 60 HP/min global |
| Round | per track, best of 3, 8-bar intro immunity |

## 7. Decisions needed

1. ~~Tier word set~~ — decided: set B (2026-10-06).
2. P1 name on the plate ("OSH"? "ALDEROSH"?) and whether the DJ is a sprite at all (see `04`: recommendation is portraits + a corner mascot, no full fighter).
3. Twitch event source: ask Triode for `np:community`, and/or build the Streamer.bot adapter.
4. Rounds per track vs fixed-length rounds.
5. SFX: ship as an option off by default, or not at all.
6. Which moves matter most to Osh's style (Osh uses channel faders, never the crossfader; what about hot cues, loops, FX, stems?). This ranks the event asks to Triode.
7. Whether tier thresholds scale with the rig's available move set, or stay fixed so all rigs compete on one ladder.
