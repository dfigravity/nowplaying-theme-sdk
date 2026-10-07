# DJ Street Fighter — Game Mechanics Research Note

Date: 2026-10-06
Scope: combo/streak design precedents, a DJ-gesture move vocabulary, the combo/escalation engine, the Twitch "fight back" layer, the health/KO loop, and the event list to request from the NP3 author.

Inputs assumed (from the protocol findings of 2026-10-05/06): `np:mix` state snapshots on every controller event (median 0.3 s apart, bursts at ~100 ms, each state sent twice), 6 channels with `channelFader` 0..1 (coarse), `eqLow/Mid/High` -1..1, `playing`, `cueActive`, `jogTouching`, `trim`, `filter` (not live yet), `looping`, `crossfader.position` -1..1, `onAir`, plus `np:track` with BPM and Camelot key. No beat phase today. The theme runs in a sandboxed iframe inside an OBS browser source, can fetch the internet, and can reach 127.0.0.1.

A note on time units used below: `beat = 60 / bpm` seconds, `bar = 4 beats`, `phrase = 8 bars` unless the genre says otherwise. At 128 BPM a beat is 0.469 s, a bar 1.875 s, 8 bars 15 s, 32 bars 60 s. Windows are expressed in bars so they scale with tempo; we convert to wall time using the on-air track's BPM.

---

## 1. How combo and streak systems are actually designed

### 1.1 Street Fighter (hit counter, scaling, meter, stun)

- Origin: combos were an accident in Street Fighter II (1991); players found that some attacks left no recovery time for the opponent, and Capcom formalised it. Early SF2 combos were 2–5 hits; modern games show 100+ hit counters ([Wikipedia: Combo](https://en.wikipedia.org/wiki/Combo_(video_games)), [EventHubs](https://eventhubs.com/news/2024/oct/18/19-hit-combo-streetfighter-2)).
- Hit counter: SF6's HUD shows the number of hits in the current combo; it exists to tell the player whether the sequence was a true combo. SF6 forces an air recovery on the 100th hit, which is a hard cap on combo length ([SRK wiki: SF6 HUD](https://srk.shib.live/w/Street_Fighter_6/HUD)).
- Damage scaling (SF6): hits 1–2 do 100 %, hit 3 does 80 %, hit 4 70 %, 5 60 %, 6 50 %, 7 40 %, 8 30 %, 9 20 %, hit 10+ 10 %. Super Arts have minimum scaling floors of 30/40/50 % for levels 1/2/3 so a finisher still feels big. Drive Rush used mid-combo adds a further 15 % penalty and Perfect Parry halves damage; these stack down to 4 % ([EventHubs: Jamie scaling](https://www.eventhubs.com/news/2023/oct/17/jamie-worst-combo-sf6), [EventHubs: Ryu 75 %](https://eventhubs.com/news/2024/jan/21/javits-ryu-75-percent-sf6)). The lesson: a per-hit multiplier that decays geometrically keeps long combos from running away while preserving a floor for finishers.
- Resources: SF6 gives each fighter 6 Drive bars that refill over time and when hitting the opponent (even on block); Drive Impact costs 1 bar, Drive Parry 0.5 bar, Drive Rush 1 bar from a parry or 3 bars after a normal, Drive Reversal 2 bars. Emptying it puts you in Burnout ([EventHubs: Drive costs](https://eventhubs.com/news/2023/jan/03/drive-gauge-actions-cost-sf6), [Dexerto](https://www.dexerto.com/street-fighter/street-fighter-6-drive-gauge-system-2144653/)). Super gauge fills when an attack hits or is blocked, not on whiff ([esports.gg: Super Arts](https://esports.gg/news/street-fighter-6/super-arts-in-street-fighter-6-what-to-know-and-when-to-go/)). Alpha introduced the 3-level super gauge, filled by performing normals and specials, with stocks carrying between rounds ([Wikipedia: SF Alpha](https://en.wikipedia.org/wiki/Street_Fighter_Alpha)). SF4's Revenge gauge fills by taking damage and resets each round, which is why Ultras read as a comeback mechanic ([Giant Bomb: SFIV](https://giantbomb.com/wiki/Games/Street_Fighter_IV)).
- Stun (SF4): a counter per character with max values from 750 to 1200 (Ryu 1000); every hit adds stun damage; reaching max dizzies you; the counter drains when you are not being hit ([SRK: SF4 Stun Meter](https://srk.shib.live/w/Street_Fighter_IV/Basic_Elements/Stun_Meter)).

Design principles to steal: a visible hit counter that only counts "true" chains; geometric per-hit scaling with a floor for finishers; meter that fills on meaningful contact (not on whiffs, i.e. not on idle wiggling); a separate comeback resource that fills when you are losing.

### 1.2 Killer Instinct (2013): structured combos, breakers, the announcer

- Structure: Opener > Auto-Double or Manual > Linker > Auto-Double or Manual > Ender. Openers are what "turn the combo system on"; if you have not seen an opener, the system is not operating ([ki.infil.net: Combo](https://ki.infil.net/combo.html), [Wikipedia: KI 2013](https://en.wikipedia.org/wiki/Killer_Instinct_(2013_video_game))).
- Length governor: the KV (knockdown value) meter is a red bar under the combo counter; when it hits 100 the next non-ender hit causes a "blowout". Light attacks build KV fast, heavies slowly, shadow moves add none ([ki.infil.net: KV and Enders](https://ki.infil.net/combo4.html)).
- Enders: levels 1–4 driven by accumulated white damage; higher levels do more damage, more meter, or bigger launchers, and the animation gets flashier. A shadow ender grants +1 level (a "level 5") ([ki.infil.net](https://ki.infil.net/combo4.html)).
- Breakers: the defender can break auto-doubles, manuals, linkers and post-opener juggles by matching the strength (L/M/H); a wrong guess or bad timing locks you out for 3 s (4 s after a counter-breaker), shown as a colored L/M/H badge or a white clock. A successful break restores 50 % of white life and returns both to neutral ([ki.infil.net: Breakers](https://ki.infil.net/cbreaker.html), [EventHubs: lockouts](https://www.eventhubs.com/news/2013/jun/16/dave-verfaille-killer-instinct-if-you-mash-during-opponents-combo-you-will-get-punished-combo-breakers-and-lock-outs-explained)).
- Ultra: available when the opponent is in danger (below 15 % of the second life bar); unbreakable; ends the match; shadow meter is maxed during it ([ki.infil.net](https://ki.infil.net/combo4.html)). In the original SNES game an Ultra ending added 18 hits to the counter.
- The announcer: named callouts at fixed hit counts, in the classic games: Triple (3), Super (4), Hyper (5), Brutal (6), Master (7), Awesome (8), Blaster (9), Monster (10), King (11), Killer (12+), then Ultra and Ultimate ([TASVideos: KI combo names](https://tasvideos.org/Forum/Posts/99984)). This is the most directly reusable piece: a voice/text tier table keyed on hit count.

Design principles: require an "opener" before counting (for us: a real transition gesture, not an EQ tweak); a visible governor so combos end deliberately with an "ender" rather than fizzling; tiered callouts at fixed counts; a defender-side mechanic (chat's breaker) with a lockout so spamming is punished.

### 1.3 Devil May Cry style rank (D → SSS)

- Ranks: D, C, B, A, S, SS, SSS. Every connecting attack adds Stylish Points; cheap actions (shooting from range) give almost nothing, variety and taunts give more; getting hit drops you one or two ranks ([Shacknews: DMC5 Stylish Points](https://shacknews.com/article/110322/stylish-points-and-style-ranks-in-devil-may-cry-5), [DMC wiki: Stylish Rank](https://devilmaycry.fandom.com/wiki/Stylish_Rank)).
- Decay numbers from a community measurement thread: DMC1 loses the rank after only 1.5 s; DMC3 drops one full grade roughly every 6.5 s and starts a new grade at the midpoint of its bar; DMC4 drops a grade every ~12 s and never falls below the grade you already hold (only the bar drains); DmC drops a grade every 5.5 s (4.5 s on Hardcore). The higher the grade, the faster the bar drains ([devilmaycry.org thread](https://devilmaycry.org/threads/dmc-3-4-style-meter-behavior.23616/)).
- Repetition rule: in DmC only two repetitions of the same attack keep the meter alive; after that the move neither retains nor increases rank. DMC3 is stricter (a single repeat starts decay). DMC4 eventually lets repeated moves count again, which is why it is the most spam-tolerant ([same thread](https://devilmaycry.org/threads/dmc-3-4-style-meter-behavior.23616/), [DMC wiki](https://devilmaycry.fandom.com/wiki/Stylish_Rank)).

Design principles: rank is a leaky bucket, not a counter; leak rate increases with rank; idle drains the bar but (DMC4 style) can keep the letter until a timeout, which is the forgiving behaviour we want for a DJ who is letting a track breathe; getting hit (chat landing damage) knocks the rank down by two; a per-move repetition counter that stops rewarding after the second repeat.

### 1.4 Tony Hawk's Pro Skater (the closest analog to a rolling stack)

- Formula: Score = (sum of trick base points) × multiplier. Each trick adds +1 to the multiplier; a 180/360 spin adds +0.5, a 540 or more adds +1; gaps add +1. Example: Kickflip = 100; Kickflip + Heelflip = 200 × 2 = 400; add a 180 and it is 200 × 2.5 = 600 ([Red Bull: THPS 1+2 tips](https://www.redbull.com/gb-en/tony-hawks-pro-skater-1-2-tips), [StrategyWiki: THPS2](https://strategywiki.org/wiki/Tony_Hawk's_Pro_Skater_2/Gameplay)).
- The stack keeps accumulating until you land (bank) or bail (lose everything). THPS2's manual and THPS3's revert exist purely to extend the combo across flat ground and out of quarter-pipes, with a wobbling balance meter you must keep centred ([Wikipedia: THPS3](https://en.wikipedia.org/wiki/Tony_Hawk%27s_Pro_Skater_3)). Bailing awards nothing for the current combo and empties the special meter; successful tricks fill the special meter, which unlocks much higher value signature tricks ([StrategyWiki: THPS](https://strategywiki.org/wiki/Tony_Hawk%27s_Pro_Skater/Gameplay)).
- Freshness: repeating a trick degrades it. In THPS3 a Kickflip is worth 100, 75, 50, 25, then 10 on successive uses; THPS 1+2 keeps the same rule ([TASVideos post](https://tasvideos.org/Forum/Posts/322835), [Activision support](https://support.activision.com/tony-hawks-pro-skater-1-2/articles/tony-hawks-pro-skater-1-2-scoring-and-combos)).

This is our model: base points per move, a multiplier that grows by +1 per move (fractional for small moves), a "balance" state (long blend, held loop, sustained filter) that keeps the combo alive while the DJ is between tricks, a visible wobble/countdown before the combo drops, and a bank on landing (clean transition) rather than a loss. We should not copy the bail-loses-everything rule literally; a DJ "bail" (a train wreck) is rare and hard to detect, so we bank on timeout instead.

### 1.5 Rhythm games: Guitar Hero, Rock Band, Beat Saber

- Guitar Hero: base 50 per note; the multiplier steps to ×2 at a 10-note streak, ×3 at 20, ×4 at 30; Star Power doubles the current multiplier (max ×8) and is earned by hitting marked phrases; the Rock Meter rises on hits and falls on misses, and if it bottoms out the crowd boos you off ([Guitar Hero wiki](https://guitarhero.fandom.com/wiki/Guitar_Hero), [Wikipedia: Guitar Hero](https://en.wikipedia.org/wiki/Guitar_Hero_(video_game))).
- Rock Band: same streak multiplier; Overdrive doubles your multiplier, and in a band each player's Overdrive stacks (four players = ×8); Unison phrases reward coordinated play ([Wikipedia: Rock Band](https://en.wikipedia.org/wiki/Rock_Band_(video_game))).
- Beat Saber: a perfect cut is 115 points (70 for the 100° pre-swing, 30 for the 60° follow-through, 15 for accuracy). Multiplier steps 1× → 2× → 4× → 8× on consecutive cuts; a miss halves the multiplier rather than resetting it. Letter grades by accuracy: SS ≥ 90 %, S 80–89.99, A 65–79.99, B 50–64.99, C 35–49.99, D 20–34.99, E below ([BSMG ranking guide](https://bsmg.wiki/ranking-guide.html), [Road to VR](https://roadtovr.com/beat-saber-studio-shows-get-highest-score-new-video/)).

Design principles: fixed thresholds that players can memorise (10/20/30); a bonus resource that doubles rather than adds; "halve on failure" is gentler than "reset on failure" and keeps a long set from feeling punished by one dead patch.

### 1.6 Tetris Effect and Lumines: escalation with named tiers and a charged mode

- Tetris Effect Zone: the meter fills by clearing lines (a quarter of the bar per N lines, N depending on stage); activating it freezes gravity for up to 20 s; clears inside Zone get escalating names: Tetris 4–7, Octoris 8–11, Dodecatris 12–15, Decahexatris 16–17, Perfectris 18–19, Ultimatris 20, Kirbtris 21, Impossibilitris 22, Infinitris 23, Electris 24–25, WTFtris 25+. Each Octoris-or-better adds +1× and activating from a full meter adds another +1× (max 3×) ([tetris.wiki: Tetris Effect](https://tetris.wiki/Tetris_Effect), [Prima: Zone](https://primagames.com/tips/how-zone-mechanic-works-tetris-effect-connected)).
- Lumines: a Time Line sweeps left to right in time with the music and erases completed squares as it passes; clearing 4+ squares in one sweep is a combo, and clearing on consecutive sweeps builds the multiplier. The sweep speed is set by the track's tempo, so scoring windows are literally musical ([Wikipedia: Lumines](https://en.wikipedia.org/wiki/Lumines)).

Design principles: name the extremes (people chase the funny top tier); a charged mode the system enters automatically with a time limit; evaluate on the beat (Lumines' sweep) rather than on the wall clock.

### 1.7 Bayonetta: variety and reset tokens

Combo Score = Combo Points × Combo Multiplier; repeating the same combo yields diminishing returns, and landing a Wicked Weave resets the repetition penalty ([Nintendo Life: Bayonetta 2 scoring](https://nintendolife.com/guides/bayonetta-2-how-the-combat-scoring-system-works-and-how-to-get-a-platinum-trophy-in-every-battle), [Steam discussion](https://steamcommunity.com/app/460790/discussions/0/1646544244468357624)). We can use a "signature move resets freshness" rule: a Special-tier move clears the repetition counters so a DJ who does a big transition is allowed to go back to chops.

### 1.8 Extracted principles (what the engine must do)

1. Count only deliberate actions ("openers"): crossing hysteresis thresholds, not noise.
2. Use musical windows (bars) for chaining and decay; wall-clock only as a fallback.
3. Escalate with fixed, visible tiers and name them; put the announcer in.
4. Score = base × multiplier with per-hit scaling so 30-hit combos do not dwarf a single great Double Drop; floor the big moves.
5. Freshness: 100/75/50/25/10 % for repeats of the same move within one combo; a Special resets freshness.
6. Rank meter is a leaky bucket with faster drain at higher ranks; idle drains the bar, not the letter, until a longer timeout.
7. Show the drop coming (THPS balance wobble, KI KV bar): a visible countdown before the combo ends.
8. Halve on failure rather than zero, except on a true KO.
9. Feedback within ~100 ms of the gesture, with the move name and the channels involved, so the meter never feels random. Every point on screen must be explainable by a callout the viewer saw.
10. A super meter that fills on points, auto-activates on the next meaningful move, and is time-limited (Zone, Star Power).

---

## 2. DJ gesture → move vocabulary

Conventions: `F[n]` channel fader of channel n (0..1), `L/M/H[n]` eqLow/Mid/High (-1..1, 0 flat), `X` crossfader (-1..1), `P[n]` playing, `T[n]` jogTouching, `onAir(n)`. Fader values arrive coarse, so all thresholds use hysteresis: "closed" = ≤ 0.10, "open" = ≥ 0.80, "killed" EQ = ≤ -0.80, "flat" EQ = within ±0.10. Windows in bars use the BPM of the loudest on-air track. "Today" means detectable from current `np:mix` snapshots; "Needs event" names the SDK event required.

Tiers and base points: Basic 10–25, Technical 30–50, Special 60–100, Ultra 150+. These are multiplied by the combo multiplier (section 3).

| # | Move (callout) | Gesture | Detection rule | Tier / pts | Today? |
|---|---|---|---|---|---|
| 1 | QUICK CUT | Hard cut from one live channel to another | `P[a] && P[b]`; `F[a]` goes open → closed and `F[b]` closed → open, both transitions inside ≤ 1 bar (≤ 2 s wall-clock cap) | Basic 20 | Today |
| 2 | CROSSFADER SLAM | Crossfader thrown side to side | `X` moves from ≤ -0.8 to ≥ 0.8 (or reverse) within ≤ 1 beat, assigned channels both playing | Basic 25 | Today if `crossfader.position` updates live (unverified) |
| 3 | TRANSFORMER | Fader chopped on/off | On one playing channel, `F[n]` crosses 0.5 at least 4 times within 1 bar; +5 pts per extra crossing, cap 12 | Technical 30+ | Today, limited by the 100 ms burst rate; require ≥ 4 distinct states |
| 4 | CRAB | Crossfader stutter | `X` crosses 0 at least 6 times within 1 bar | Special 80 | Needs live crossfader at ≥ 20 Hz |
| 5 | BASSLINE SWAP | Bass handed from A to B | `L[a]` flat → killed and `L[b]` killed → flat, both within a 2-bar window, both channels `F ≥ 0.5 && P`; "CLEAN SWAP" bonus +20 if the two final crossings are within ±1/4 beat | Technical 40 | Today |
| 6 | MID SWAP ("VOCAL SWAP") | Same with mids | Mirror of #5 on `M` | Technical 35 | Today |
| 7 | EQ KILL SWEEP | Kill all three bands, bring back in order | On one on-air channel, `L,M,H` all ≤ -0.8 at some point, then restored to flat in the order L→M→H within 2 bars | Technical 45 | Today |
| 8 | THE DROP | Everything restored on the one | A channel has been "cut" (L ≤ -0.8 or filter ≠ 0) for ≥ 2 bars, then L and filter return to flat within ≤ 1 beat. +40 "ON THE ONE" if within ±1/8 beat of a downbeat | Special 60 (+40) | Today without the downbeat bonus; the bonus needs a beat-phase event |
| 9 | HIGH PASS RISER | Long filter sweep up, release | `filter[n]` rises monotonically (allow 1 small reversal) from ≤ 0.1 to ≥ 0.6 over ≥ 4 bars, then returns to ≤ 0.1 within ≤ 1 beat; pts scale with bars held (4 → 75, 8 → 100, 16 → 125) | Special 75+ | Needs filter event (filter did not update in the 2026-10-05 recording) |
| 10 | LOW PASS DIVE | Same, sweep down | Mirror of #9 with negative filter | Special 75+ | Needs filter event |
| 11 | FILTER WOBBLE | Rhythmic filter | `filter[n]` alternates across ±0.3 at least 4 times within 2 bars | Technical 35 | Needs filter event at ≥ 20 Hz |
| 12 | ECHO OUT | FX on, fader out | `fx.on(unit→n)` then `F[n]` open → closed within 1 bar while FX active; FX off within 4 bars after | Special 60 | Needs FX events |
| 13 | BACKSPIN | Jog spun backwards hard | `jog.rotate` on deck n with negative direction and |velocity| ≥ 2× nominal for ≥ 0.25 s while `T[n]`; followed within 1 bar by `F[n]` closed or `P[n]` false | Special 80 | Needs jog rotation event. Today only a weak proxy: `T[n]` true for 0.2–1.0 s then fader cut ("SPIN OUT?" shown with a question mark, half points) |
| 14 | SCRATCH | Jog rocked back and forth | `T[n]` true and `jog.rotate` direction alternates ≥ 4 times within 1 bar; +10 per extra alternation up to 100; "BABY", "CHIRP", "TRANSFORMER SCRATCH" if combined with #3 on the same channel | Technical 40+ | Needs jog rotation |
| 15 | VINYL BRAKE | Power-off stop | Play stop with a ramped velocity: `P[n]` true → false and jog/tempo velocity decays from 1.0 to 0 over 0.3–2 s | Special 60 | Needs velocity or a dedicated brake event. Proxy today: DEAD STOP (Basic 15): `P[n]` true → false while `F[n] ≥ 0.5 && onAir(n)` |
| 16 | HOT CUE JUGGLE | Rapid cue drumming | ≥ 3 `pad.hotcue` presses on one deck within 1 bar; "CUE DRUM" Special 90 if ≥ 8 within 2 bars | Technical 45 / Special 90 | Needs pad events |
| 17 | CUE STUTTER | Cue button stabs | `cueActive[n]` toggles ≥ 4 times within 1 bar on a deck that is on air | Technical 30 | Today (cueActive updates live) |
| 18 | LOOP ROLL | Short roll then release | `loop.roll` on with size ≤ 1/4 beat, held ≤ 2 bars, released; or `looping[n]` true for ≤ 2 bars then false while on air | Technical 35 | Needs loop events; possibly today via `looping` (unverified) |
| 19 | BEAT JUMP | Jump forward/back | `beatjump` event on an on-air deck | Basic 20 | Needs event |
| 20 | NUDGE | Tempo bend to lock | ≥ 2 `tempo.bend` events within 4 bars on a playing deck that is not on air (i.e. beatmatching the incoming track) | Basic 10 | Needs event |
| 21 | TRIM BOOST | Gain ride | `trim[n]` rises ≥ 0.2 within 1 bar while on air; once per track per channel | Basic 10 | Today |
| 22 | DOUBLE DROP | Two tracks slam together | Two channels `P`, both `F ≥ 0.9`, both `L ≥ -0.1`, both on air simultaneously for ≥ 1 bar, preceded within 2 bars by at least one #8 THE DROP or #5 BASSLINE SWAP | Ultra 150 | Today (phrase alignment bonus needs beat phase) |
| 23 | THREE-DECK STACK | Three decks live | Three channels `P && F ≥ 0.5` for ≥ 4 bars; "FOUR ON THE FLOOR" Ultra 200 for four | Special 100 | Today |
| 24 | HARMONIC MIX | Key-compatible transition | New on-air track's Camelot key equals previous ±1 on the wheel (same letter) or same number, other letter | Technical 40 | Today (np:track key) |
| 25 | ENERGY BOOST | Key up / tempo up | New on-air track is +1 Camelot (or +7 semitones) and/or ≥ 2 % faster BPM | Technical 30 | Today |
| 26 | GEAR CHANGE | Tempo jump | BPM differs by ≥ 4 % between consecutive on-air tracks, and the transition was a #1 or #22 | Basic 15 | Today |
| 27 | LONG BLEND | Two decks ride together | Two channels `P && F > 0.5` for ≥ 32 bars; points +25 per further 16 bars; while active it extends the combo window (section 3) | Special 75+ | Today |
| 28 | SLOW BURN | Patient fade-in | `F[b]` rises from closed to open over ≥ 16 bars with no reversal > 0.1 | Basic 20 | Today |
| 29 | CLEAN TRANSITION | Tidy ender | After `F[b] ≥ 0.9`, the outgoing channel has `F[a] ≤ 0.1` and `P[a] = false` within ≤ 1 bar; acts as an "ender" that banks the combo with +10 % | Technical 35 | Today |
| 30 | ON THE ONE | Phrase-accurate action | Any Special/Ultra move whose final crossing lands within ±1/8 beat of a 16- or 32-bar phrase boundary | Modifier ×1.5 | Needs beat-phase event |

Notes on detection:

- Dedupe duplicate `np:mix` states (each is sent twice) before diffing; derive per-signal delta events (`signal, channel, prev, value, at`) and push those into the rolling stack. All the rules above are written against those deltas.
- Fader coarseness: treat any change < 0.05 as noise; use the 0.10/0.80 hysteresis bands so a fader parked at 0.9 that jitters to 0.85 does not re-trigger.
- Musical windows: convert bars to ms with the on-air BPM at the moment the window opens. Without a beat-phase event we cannot know the downbeat; the "ON THE ONE" bonus and the "phrase boundary" variants are the main things that need it.
- Source gating: when `mixer.sourceId` is `simulated`, score nothing and show the overlay in "demo" styling, because the simulated fallback snapshots play state guesses (protocol note of 2026-10-06).
- Several moves overlap (a Quick Cut inside a Transformer). Resolve by evaluating higher-tier matchers first and consuming the deltas they used, THPS-style, so one gesture produces one callout.

---

## 3. Combo and escalation design for the overlay

### 3.1 Chain rules

- Combo window: a move chains if it lands within 8 bars of the previous move (15 s at 128 BPM). The window is extended, not reset, by "balance" states: a Long Blend in progress, a loop active, a filter held off-centre, or any three or more signal deltas in the last 2 bars. The extension caps the window at 16 bars so an abandoned blend does not keep a combo alive forever (THPS manual with a balance meter; KI KV bar as the governor).
- Opener: the first move of a combo must be Technical tier or better, or a Quick Cut. Trim Boost or Nudge alone cannot start a combo (KI openers).
- Hit counter: increments by 1 per move. Named tiers at fixed counts, announcer-style: 3 GOOD, 6 GREAT, 10 SUPER, 15 ULTRA, 25 GODLIKE, 40 KILLER (nothing above; the counter keeps going but the callout stays KILLER with a growing hit number).
- Score: `combo_points += base(move) × freshness(move) × scaling(hit_index) × variety`. `scaling` follows SF6's curve compressed: hits 1–3 100 %, 4–6 90 %, 7–10 80 %, 11–15 70 %, 16+ 60 %, with a floor of 100 % for Special and Ultra tier (super minimum scaling). `freshness` is THPS: 1.0, 0.75, 0.5, 0.25, 0.1 for the nth use of the same move in this combo; any Special resets all freshness counters (Bayonetta's Wicked Weave). `variety = 1 + 0.25 × (distinct moves in combo − 1)`, capped at ×4 (Guitar Hero's cap).
- Special callout: Special and Ultra moves get a full-width banner with the move name and the channels involved ("BASSLINE SWAP 1→2"), plus a distinct sound stinger per move. Basic moves get a small ticker line in the left-hand combo list.

### 3.2 Decay and reset

- When no move has landed for 6 of the 8 window bars, the combo enters DROPPING: the hit counter starts to shake and a 2-bar countdown bar drains (THPS balance meter). Any move during DROPPING rescues the combo and refills the window.
- At window expiry the combo is BANKED, not lost: the points are added to the set score and the super meter, a summary flashes ("14 HITS — 2,310 PTS — BEST: BASSLINE SWAP"), and the counter resets to 0. We never zero points on a timeout; the only loss conditions are chat KOs (section 5), where the current unbanked combo is halved (Beat Saber's halve-on-miss).
- Rank meter (DMC): separate from the hit counter, shown as the letter under the DJ's health bar. It is a leaky bucket in the range 0..1000 with tier boundaries D 0, C 150, B 300, A 500, S 650, SS 800, SSS 950. Each banked point adds to the bucket; drain rate is 1 point per beat at D, rising to 4 per beat at SSS. The letter is held for 16 bars of inactivity before it is allowed to fall (DMC4's retention), after which it drops one letter per 8 bars. Taking a chat hit drops the letter by two (DMC rule) but not the bucket below the new letter's floor.

### 3.3 Super meter

- Fills with banked combo points: 1,500 points = full. Ultra moves add a flat 25 %. When full it does not fire immediately; it fires on the next Technical or better move so the visual lands on a real moment (Guitar Hero players save Star Power for the solo). If nothing happens for 32 bars it fires on its own.
- SUPER: 8 bars of "charged mode": the mixer-reactive visuals go to maximum, the combo multiplier is doubled (Star Power), and in the fight layer it deals a fixed 40 % to chat's health. Then the meter resets to 0.

### 3.4 Per-track and per-set stats

Keep per track: best combo hits, best combo points, total hits, moves used (histogram), max rank, supers fired, damage taken, PERFECT flag. Keep per set: the same plus a running "move of the set". Show the track card for 6 s on `np:track` change ("LAST TRACK: 38 HITS, BEST 14, RANK S, 0 DAMAGE — PERFECT"), KI-style result screen.

### 3.5 State machine and pseudo-code

```
state: IDLE | ACTIVE | DROPPING | SUPER
ring: RingBuffer(1024 deltas, horizon 64 bars)
combo: {hits, points, moves[], freshness{}, lastMoveAt, windowBars}

on mixState(s):
  if s.source == 'simulated': return
  if s == lastState: return                  // dedupe the doubled sends
  for each (signal, ch) changed by > 0.05 or boolean flip:
    ring.push({at: now, ch, signal, prev, value})
  lastState = s
  moves = matchers.run(ring, bpm)            // highest tier first, consume used deltas
  for m in moves: onMove(m)
  tick()

on event(e):                                 // future np:event (jog, pads, fx, loops, beat)
  ring.push(e); if e.name == 'beat': clock.update(e); moves = matchers.run(ring, bpm) ...

onMove(m):
  if state == IDLE and not isOpener(m): return
  if state == IDLE: state = ACTIVE; combo = fresh()
  n = ++combo.freshness[m.name]
  pts = m.base * FRESH[min(n,5)] * scale(combo.hits+1, m.tier) * variety(combo)
  if state == SUPER: pts *= 2
  combo.hits++; combo.points += pts; combo.moves.push(m); combo.lastMoveAt = now
  if m.tier >= SPECIAL: combo.freshness = {}
  combo.windowBars = 8
  ui.callout(m, pts, combo.hits); announcer.tier(combo.hits)   // 3,6,10,15,25,40
  if superMeter.full and m.tier >= TECHNICAL: enterSuper()
  state = (state == SUPER) ? SUPER : ACTIVE

tick():                                      // every beat (from beat event or BPM-derived timer)
  idle = barsSince(combo.lastMoveAt)
  balance = longBlendActive || loopActive || filterHeld || deltasInLast(2 bars) >= 3
  limit = balance ? 16 : combo.windowBars
  if state == ACTIVE and idle >= limit - 2: state = DROPPING; ui.showCountdown(2 bars)
  if state in (ACTIVE, DROPPING) and idle >= limit: bank()
  rank.drain(beats=1, rate = RANK_RATE[rank.letter]); rank.maybeDemote(idleBars=16, stepBars=8)
  if state == SUPER and barsSince(superStart) >= 8: exitSuper()

bank():
  setScore += combo.points; superMeter.add(combo.points / 1500)
  rank.add(combo.points); stats.record(combo)
  ui.summary(combo); state = IDLE

onChatHit(dmg):                              // from section 5
  dj.hp -= dmg; rank.demote(2)
  if state != IDLE: combo.points *= 0.5
```

Implementation: pattern matchers are small functions over the ring buffer with a `since(bars)` helper that converts bars to ms using the current BPM; each returns at most one move and the set of delta indices it consumed. Run them on every ingest and on every beat tick so held-state moves (Long Blend, Three-Deck Stack) fire without a controller event.

---

## 4. The Twitch "fight back" layer

### 4.1 What Twitch exposes

EventSub subscription types (type, version, required scope) relevant to us, from the official list ([EventSub subscription types](https://dev.twitch.tv/docs/eventsub/eventsub-subscription-types/), [scopes](https://dev.twitch.tv/docs/authentication/scopes/)):

| Event | Version | Scope | Payload fields we care about |
|---|---|---|---|
| channel.cheer | 1 | bits:read | is_anonymous, user_id/login/name, bits, message |
| channel.bits.use | 1 | bits:read | type (cheer, power_up, custom_power_up), power_up |
| channel.subscribe | 1 | channel:read:subscriptions | tier (1000/2000/3000), is_gift |
| channel.subscription.gift | 1 | channel:read:subscriptions | total, tier, cumulative_total, is_anonymous |
| channel.subscription.message (resub) | 1 | channel:read:subscriptions | tier, cumulative_months, streak_months, duration_months, message |
| channel.channel_points_custom_reward_redemption.add | 1 | channel:read:redemptions or channel:manage:redemptions | reward.title, reward.cost, user_input, status |
| channel.hype_train.begin / progress / end | 2 | channel:read:hype_train | total, progress, goal, level, top_contributions |
| channel.raid | 1 | none | from_broadcaster, viewers |
| channel.follow | 2 | moderator:read:followers | user, followed_at |
| channel.chat.message | 1 | user:read:chat (plus user:bot and channel:bot for app tokens) | chatter, message text, badges, cheer info |

Payload field references: [EventSub reference](https://dev.twitch.tv/docs/eventsub/eventsub-reference/); channel-points scope discussion: [dev forum](https://discuss.dev.twitch.com/t/eventsub-token-authorization-error/36701); chat auth explanation: [dev forum](https://discuss.dev.twitch.com/t/explanation-of-channel-chat-message-event-auth/64378).

Transport facts ([EventSub WebSocket docs](https://dev.twitch.tv/docs/eventsub/handling-websocket-events/)): connect to `wss://eventsub.wss.twitch.tv/ws`; a welcome message carries a session id and you have 10 s to create your first subscription; keepalive default 10 s (configurable 10–600); up to 300 enabled subscriptions per connection, cost ceiling 10 per user token (most user-scoped subscriptions cost 0 when the broadcaster authorised them); max 3 connections per client/user; handle reconnect messages by opening the new URL before closing the old one. WebSockets require a user access token; app tokens fail. Chat on EventSub and the Conduit transport were announced in 2024 ([dev forum](https://discuss.dev.twitch.com/t/available-today-twitch-chat-on-eventsub-an-api-for-sending-chat-and-the-conduit-transport-method-for-eventsub/54596)).

Chat read without a token: Twitch IRC still accepts the anonymous `NICK justinfan<digits>` login with any PASS, read-only ([dev forum: anonymous chat](https://discuss.dev.twitch.com/t/anonymous-connection-to-twitch-chat/20392)). Non-TLS IRC WebSocket endpoints were turned off on 15 Aug 2025 and Twitch is steering everyone to EventSub chat, which needs `user:read:chat` ([IRC migration](https://dev.twitch.tv/docs/chat/irc-migration/), [change log](https://dev.twitch.tv/docs/change-log/)). So a free "!punch" command can be read anonymously over `wss://irc-ws.chat.twitch.tv:443` today, but it is legacy; cheers also appear in IRC as PRIVMSG with a `bits=` tag, so the anonymous path can see cheer amounts, just not subs, redemptions, hype train or raids. PubSub (the old channel-points feed) was decommissioned 14 Apr 2025 ([PubSub migration](https://dev.twitch.tv/docs/PubSub)).

### 4.2 Integration paths for a sandboxed browser-source theme

(a) The NP3 host forwards community events over postMessage. NP3 already ships a built-in Twitch bot ([nowplayingapp.com](https://www.nowplayingapp.com)) and the author's Stream Globe Check-In consumes Twitch chat, so the backend already holds a Twitch user token and an EventSub or IRC client. Adding `channel.cheer`, `channel.subscribe`, `channel.subscription.gift`, `channel.channel_points_custom_reward_redemption.add`, `channel.hype_train.*`, `channel.raid` to that client and emitting a normalised `np:community` message costs him little, keeps tokens out of the theme, and works for every theme author. This is the path to ask for.

(b) A local bridge the theme connects to on 127.0.0.1:
- Streamer.bot: WebSocket server on `127.0.0.1:8080`, auto-start on, optional password auth that by default is only enforced on privileged requests like SendMessage. A client sends `{"request":"Subscribe","id":"x","events":{"Twitch":["Cheer","Sub","ReSub","GiftSub","GiftBomb","Follow","Raid","RewardRedemption","ChatMessage","HypeTrainStart","HypeTrainLevelUp","HypeTrainEnd"]}}` and receives `{event:{source,type}, data:{...}}`; the Cheer payload has `user`, `bits`, `text`, `anonymous`, `cheerEmotes`, `createdAt`, `isTest` ([config](https://docs.streamer.bot/api/websocket/guide/configuration), [requests](https://docs.streamer.bot/api/servers/websocket/requests), [Twitch events](https://docs.streamer.bot/api/websocket/events/twitch), [Cheer](https://docs.streamer.bot/api/websocket/events/twitch/cheer)). The 180+ Twitch event types include the full hype-train and reward set.
- Lumia Stream: `ws://127.0.0.1:39231/api?token=...` (wss on 39232); every alert (follows, subs, cheers, raids, gift subs, channel-point redeems), chat and commands arrive as `{origin, type, event, data}` ([Lumia dev docs](https://dev.lumiastream.com/docs/websockets/listen-to-events)).
- Mix It Up: overlay server on `http://localhost:8111/overlay/`, a developer API, and a ready-made "Stream Boss" widget that is essentially our health loop ([Mix It Up docs](https://dev.site.mixitupapp.com/docs/features/overlays), [Stream Boss](https://dev.site.mixitupapp.com/docs/features/overlays/stream-boss)).
- SAMMI: Twitch/YouTube trigger engine with a JavaScript extension bridge and OBS WebSocket integration ([SAMMI](https://sammisolutions.itch.io/sammi)).
- A 60-line Node or Python relay: holds the user token, runs the EventSub WebSocket, serves `ws://127.0.0.1:<port>` to the theme. Chrome treats loopback as potentially trustworthy, so `ws://127.0.0.1` from a secure page is not blocked as mixed content; verify once in OBS's CEF build.

(c) Direct from the theme: the theme would need a user token. The only browser-side grant is the implicit flow, whose token cannot be refreshed and expires in about 60 days, after which the streamer has to interact with the browser source to re-authorise ([dev forum](https://discuss.dev.twitch.com/t/how-to-get-and-listen-realtime-channel-events-in-javascript/30985)). The token would live in the OBS source URL or local storage of a sandboxed iframe, and a theme zip that ships a client id invites abuse. Twitch staff and veterans recommend a proxy/backend for OBS overlays, with a capability URL and short-lived server-issued credentials if remote ([dev forum: overlay auth](https://discuss.dev.twitch.com/t/best-practice-auth-for-public-obs-overlay-backend-websocket-outside/64235)). Treat (c) as a dev-only mode.

Recommendation: ask for (a) and build the theme against the `np:community` schema below; implement (b) as an adapter (Streamer.bot first, since it is free and the WebSocket API is stable) that emits the same internal events, so the game logic never knows where the event came from. Keep (c) out.

### 4.3 Policy constraints

- Bits Acceptable Use Policy: Bits may be used to activate experiences for the broadcaster or community (the policy's own example is feeding a virtual pet) and to enhance a free-to-play experience; using Bits as a bet or wager, soliciting Bits for a wager, and selling/trading/transferring Bits for real or virtual currency or other items of value are prohibited ([Bits AUP](https://legal.twitch.com/legal/bits-acceptable-use), [Extensions guidelines](https://dev.twitch.tv/docs/extensions/guidelines-and-policies)). Twitch staff on the dev forum draw the line this way: reacting directly to a cheer event with an on-stream effect is fine; converting Bits into a secondary currency that is then exchanged for rewards is not ([dev forum: bits handling](https://discuss.dev.twitch.com/t/unsure-about-bits-handling-and-the-policies/62154)).
- Bits-enabled Extensions are a different product: an Extension runs inside Twitch's own iframe on the channel page, sells products defined by the Extension through the Extensions Bits API, is reviewed by Twitch, shares revenue, must not use random-chance loot or wagers, may not sell items the broadcaster or viewers specify in free text, and may not describe the transaction as "buy", "spend", "donation" or "cheering" ([Extensions guidelines](https://dev.twitch.tv/docs/extensions/guidelines-and-policies)). An OBS browser-source overlay is not an Extension and cannot take Bits itself; it only reacts to cheers that already happened. That is the normal alert-box pattern and is allowed.
- Channel Points have no monetary value and may not be converted into anything with real-world value ([dev forum: Channel Points policy](https://discuss.dev.twitch.com/t/channel-points-policy/36709)). Gambling content rules (slots, roulette, dice; unlicensed casino sites banned since Oct 2022) are about real gambling, not cosmetic games ([Twitch gambling education](https://www.twitch.tv/p/safety/education-portal/en/articles/gambling-education)).
- Practical rules for us: damage must be a deterministic function of the amount (no random crits tied to Bits), there is no prize of value for winning (bragging rights, a name on the scoreboard, a shout-out), never word it as "buy damage" in overlay copy, and keep channel-points attacks purely cosmetic. Precedents doing exactly this: Shark Attack boss fights with chat commands ([itch.io](https://dschmader.itch.io/shark-attack)), Chat Vs Streamer mode where the streamer hits back every 30 s ([itch.io](https://el-tutsi.itch.io/twitch-chat-avatars/devlog/468807/chat-vs-streamer-mode)), Chat Wars where bits set strength, and Meld's Chat 1v1 fighting overlay ([Meld](https://meldstudio.co/gallery/chat-1v1/)).

### 4.4 Proposed host message: `np:community`

```json
{
  "type": "np:community",
  "protocol": "np3-community/1",
  "at": 1791234567890,
  "id": "twitch:evt:abc123",
  "platform": "twitch",
  "kind": "cheer",
  "user": { "id": "12345", "login": "osh", "display": "Osh",
            "isSub": true, "isMod": false, "isVip": false, "isBroadcaster": false,
            "isAnonymous": false, "badges": ["subscriber/12"] },
  "amount": 500,
  "unit": "bits",
  "tier": null,
  "message": "take that",
  "reward": null,
  "meta": {}
}
```

`kind` enumerations and the fields each fills:

| kind | amount / unit | tier | extra |
|---|---|---|---|
| cheer | bits / "bits" | — | message, isAnonymous |
| sub | 1 / "subs" | 1000, 2000, 3000 (or "prime") | isGift=false |
| resub | months / "months" | tier | streak, cumulative, message |
| gift | total / "subs" | tier | isAnonymous, recipients count (gift bomb) |
| redeem | cost / "points" | — | reward {id, title, prompt}, userInput |
| raid | viewers / "viewers" | — | fromLogin |
| follow | 1 / "follows" | — | — |
| hype | level / "level" | — | progress, goal, total, phase ("begin","progress","end") |
| chat | 0 | — | message, emotes, isCommand, command, args |

Add a `test: true` flag so the dashboard's "send test event" button can drive the overlay, and a `seq` so the theme can detect gaps. For chat, let the host do nothing clever: send every message with the raw text and let the theme match `!punch`. If the author prefers, add `kind: "command"` with a host-side allow list.

---

## 5. Health and KO loop

### 5.1 Two health bars, SF layout

DJ on the left, CHAT on the right, both 1000 HP, round timer in the middle. DJ HP falls when chat lands attacks; CHAT HP falls when the DJ lands moves. The mixer-reactive visuals scale with the DJ's combo, and the screen "takes hits" (shake, flash, cracks) when chat lands.

### 5.2 Damage from community events (deterministic, capped)

| Source | Damage | Cap |
|---|---|---|
| Cheer | 1 HP per bit (100 bits = 10 %); 1,000+ bits is a "HEAVY" with a bigger animation | 500 HP per event |
| Sub tier 1 / Prime | 150 HP (15 %) | — |
| Sub tier 2 / tier 3 | 250 / 500 HP | — |
| Resub | tier value + 5 HP per cumulative month | 600 HP |
| Gift subs | 150 per gift, tier-scaled | 500 HP per bomb (a 20-gift bomb is a cinematic, not an instant KO) |
| Channel points "PUNCH" (500 pts) / "HADOUKEN" (2,000 pts) | 20 HP / 80 HP | per-user 5 per minute |
| Free chat `!punch` | 5 HP | 30 s per-user cooldown, global 60 HP per minute |
| Raid | 2 HP per viewer | 300 HP |
| Follow | 10 HP | — |
| Hype train level up | 100 HP per level; train end at level 3+ = "ULTRA" cinematic | — |

Everything that is not Bits is free or near-free for viewers, so non-donors always have a way to play (the free `!punch` and channel points), and the Bits/sub attacks are what make the big animations.

### 5.3 Defence and offence for the DJ

- Each hit in a combo restores 1 % HP; tier-ups heal more: GOOD +3 %, GREAT +5 %, SUPER +10 %, ULTRA +20 %, GODLIKE +40 %.
- Guard: while the DJ's combo is at 10+ hits, incoming damage is halved and the DJ's health bar shows a block flash (KI's unbreakable damage idea in reverse).
- Offence: each move deals `points / 10` HP to CHAT (a 40-point Bassline Swap at ×2 = 8 HP; a banked 2,000-point combo has dealt ~200 HP). SUPER (section 3.3) deals a flat 40 %. A Double Drop at ULTRA tier with the super active can KO chat from 60 %, which is the "DJ KOs chat" moment the author described.
- Breaker (optional, KI): a channel-points "BREAKER" redemption during a DJ combo of 10+ hits ends the combo early (banks at 50 %) and the redeemer's name appears as "C-C-C-COMBO BREAKER". Limit to once per combo and 1 per user per 5 minutes; if it fires when no combo is active, show the KI lockout badge and put that user on a 3-minute cooldown.

### 5.4 Rounds

- One round per track by default (the track change is a natural bell), best of 3 rounds per "match" of three tracks, with round pips under the names. Alternative for long blends: fixed 10-minute rounds.
- Round ends on KO or when the track ends; on time-out the side with more HP wins the round (SF time-over rule). Each round starts both bars at 1000 and keeps the DJ's rank letter and super meter (Alpha's super carry-over).
- PERFECT: the winner took no damage in the round; for the DJ this means no chat attack landed all track; for chat it means the DJ never landed a Technical or better move (shame display).
- KO sequence: freeze 300 ms, slow-mo flash, "K.O." with the finishing move or the finishing viewer's name, 4 s hold, then a round card with top 3 attackers (name, damage), DJ best combo, hits, rank, PERFECT badge; then round reset. After the third round: "WINNER — DJ" or "WINNER — CHAT" with a 10 s scoreboard, then the match counters reset.
- State to keep: `{round, djHP, chatHP, roundStartAt, trackId, attackers: Map<user,{dmg,hits,lastAt}>, perfectDJ, perfectChat, history[]}`.

### 5.5 Anti-abuse and fairness

- Per-user caps on free attacks (above) plus a global free-attack budget per minute so a raid of 500 people cannot KO the DJ in 10 s with `!punch`.
- Gift-bomb and big-cheer caps per event, with the overflow converted into a longer cinematic rather than more damage.
- Ignore events flagged `test` for the scoreboard, display them with a TEST watermark.
- Dedupe by event id; EventSub may redeliver.
- No damage during the first 8 bars of a track (round intro), so the DJ gets to execute the transition the round is meant to be about.
- Display the rule card (`!rules`) on request: what each action does, cooldowns, and that it is for fun.

---

## 6. Events to ask the app author for (ranked)

The author plans to turn the SDK into a small copy of his mix-processor-service that normalises MIDI into named events. This is the list, most valuable first, with the fields each needs. Every event shares the envelope below.

Envelope:

```json
{
  "type": "np:event",
  "protocol": "np3-event/1",
  "at": 1791234567890,
  "seq": 48213,
  "source": "midi",
  "device": "DDJ-FLX10",
  "deck": 2,
  "name": "jog.rotate",
  "value": -3.4,
  "prev": -2.9,
  "delta": -0.5,
  "raw": { "status": 176, "cc": 34, "value7": 12 },
  "meta": { "direction": -1, "velocity": 3.4, "touching": true,
            "beat": { "bpm": 128.0, "beat": 3, "bar": 7, "phrase": 2, "phaseMs": 112 } }
}
```

Field rules: `at` is the host's monotonic-corrected epoch ms at MIDI receive; `seq` is a per-session counter so the theme can detect drops; `deck` is 1-based or null for mixer-wide controls; `value` is normalised (0..1 for unipolar, -1..1 for bipolar, booleans as true/false); `prev` is the last normalised value for the same `name`+`deck`; `raw.value7` is the 7-bit MIDI value (and 14-bit `value14` where the controller sends MSB/LSB pairs, which the FLX10 does for faders and EQs); `meta.beat` is attached to every event when the host knows the beat grid.

Ranked list:

1. `beat.tick` — bpm, beat (1–4), bar (1–N within phrase), phrase index, phaseMs offset, deck it comes from (the master or on-air deck). One event per beat. Without this, all "on the one", downbeat and phrase-boundary rules are impossible and windows have to be approximated from BPM. If Rekordbox beat phase is not reachable over MIDI, even the master deck's beat LED or the beat FX tempo indicator would do; failing that, a `track.position` event (elapsed ms) every 500 ms plus the beatgrid offset lets the theme compute phase itself.
2. `jog.rotate` — deck, direction (±1), velocity as a ratio to nominal playback speed (1.0 = platter speed, negative = backwards), touching boolean, mode (vinyl/pitch-bend). Coalesce to ≤ 30 Hz with the max |velocity| in the window, plus `jog.touch` edges unthrottled. Enables Backspin, Scratch, Vinyl Brake, and the scratch-reactive visuals.
3. Continuous mixer values as events, unthrottled, with 7-bit (ideally 14-bit) raw: `fader.channel`, `fader.cross`, `eq.low`, `eq.mid`, `eq.high`, `filter`, `trim`. Today these arrive as coarse state snapshots; as deltas with raw values the Transformer, Crab and Filter Wobble matchers become reliable. Keep `np:mix` as the periodic state for late joiners.
4. `pad.press` / `pad.release` — deck, padMode (hotcue, padfx, beatjump, sampler, keyboard, beatloop, keyshift, slicer, looproll), index 1–8, velocity. Enables Hot Cue Juggle, Loop Roll, Beat Jump, Slicer detection.
5. `loop.in`, `loop.out`, `loop.active` (true/false), `loop.size` (beats, fractional), `loop.roll` (active, size), `loop.exit`. Enables Loop Roll and the balance-state extension.
6. `fx.toggle` (unit, slot, on/off, effectName), `fx.level` (unit, 0..1), `fx.beats` (unit, beat fraction), `fx.assign` (unit → channel list), `colorfx.toggle` (channel, effectName), `colorfx.param`. Enables Echo Out, FX-driven visuals, and lets us say "ECHO OUT" rather than "FX".
7. `deck.play`, `deck.cue`, `deck.sync`, `deck.master`, `deck.keylock`, `deck.slip`, `deck.vinylMode` as boolean edge events with deck. Play/cue exist in the state today; as edges they are cheaper to detect.
8. `tempo.slider` (deck, -1..1 and resulting bpm), `tempo.bend` (deck, direction, strength), `tempo.range`, `key.shift` (deck, semitones), `key.sync`. Enables Nudge, Gear Change refinements and key-aware Harmonic Mix during a blend.
9. `deck.load` / `deck.eject` with the full track object (title, artist, bpm, key, duration, genre, label) and `track.position` (elapsed ms, every 500 ms). Lets the theme know an outgoing deck is near its end (clean transition expectations) and compute phase if `beat.tick` is unavailable.
10. `onair.change` — current on-air channel list, previous list, reason (fader, crossfader, play, debounce). Exists inside the state; as an event it is the trigger for Harmonic Mix / Energy Boost / Gear Change evaluation.
11. `mixer.sourceChange` — midi vs simulated, so the theme can switch scoring off.
12. `np:community` (section 4.4) and a `np:config` message with the theme's saved options (health scaling, free-attack cooldowns), since dashboard settings currently never reach themes.

Rate and throttling: faders, EQs, filter, trim, crossfader unthrottled at native MIDI rate (a quick fader throw is 5–20 MIDI messages in under 200 ms, and we want all of them); jog rotation coalesced to ≤ 30 Hz; pads, play/cue, loops, FX, tempo edges unthrottled; `beat.tick` once per beat; `track.position` every 500 ms. postMessage comfortably handles a few hundred messages per second, but the host should batch: send `np:event` as an array when more than one event arrives within the same animation frame (`{type:"np:events", events:[...]}`) to keep the receiving side's work per frame bounded.

What the rolling stack needs on the theme side: a ring buffer of 1,024 events (at 128 BPM a busy 64-bar window produces maybe 300–600 events with jog coalesced), a time horizon of 64 bars (120 s at 128 BPM) after which entries are dropped, a per-`name+deck` last-value map for O(1) current state, per-channel "held state" trackers (blend start time, loop active since, filter held since), and matchers that scan backwards from the newest event only as far as their own window. Memory is trivial; the budget to watch is matcher CPU per event, so matchers should be indexed by the signal that can complete them (a Bassline Swap only needs to run when an `eq.low` crosses a threshold).

---

## Appendix: quick tuning table (defaults to ship with)

| Parameter | Default | Source analog |
|---|---|---|
| Combo window | 8 bars, extended to 16 by balance states | THPS manual / KI KV |
| Drop warning | last 2 bars of the window | THPS balance meter |
| Tier callouts | 3 GOOD, 6 GREAT, 10 SUPER, 15 ULTRA, 25 GODLIKE, 40 KILLER | KI announcer (3..12+) |
| Freshness | 1.0, 0.75, 0.5, 0.25, 0.1 | THPS3 kickflip 100/75/50/25/10 |
| Scaling | 100/90/80/70/60 % by hit bands, floor 100 % for Special+ | SF6 scaling and super floors |
| Variety | ×(1 + 0.25 per distinct move), cap ×4 | Guitar Hero ×4 cap |
| Super meter | 1,500 pts to fill, 8 bars active, ×2 points, 40 % to chat | Star Power / Zone / SF super |
| Rank | D C B A S SS SSS, leaky bucket, hold letter 16 bars then −1 per 8 bars, −2 on hit | DMC4 retention, DMC hit penalty |
| Health | 1000 HP each, 1 bit = 1 HP, sub = 150/250/500 | Stream Boss-style widgets |
| Guard | half damage while combo ≥ 10 | KI unbreakable damage, inverted |
| Free attack | `!punch` 5 HP, 30 s per user, 60 HP/min global | Chat Vs Streamer precedents |
| Round | per track, best of 3 per match, 8-bar intro immunity | SF rounds, timer rule |
