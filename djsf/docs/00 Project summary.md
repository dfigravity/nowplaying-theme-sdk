# 00 · Project summary (detailed, as of 2026-10-06 evening)

Read this first if you are new to the project. It summarises every other document; follow the
links for depth. The index for this folder is `../README.md`.

## 1. What the project is

**DJ Street Fighter** is a custom overlay theme for Now Playing 3 (NP3), the DJ now-playing app by
Triode (GitHub `chrisle`). It turns what the DJ does on the controller into a fighting game:

- Every deliberate gesture (a fader cut, a bass swap, a backspin, a hot-cue juggle) is a **move**
  with an arcade-style callout.
- Moves within a musical window chain into a **combo** with a hit counter; fixed hit counts trigger
  announcer-style tiers, and each tier makes the overlay louder (colour shifts, sparks, lightning,
  fire border, super flash).
- Idle lets the combo drop: the counter wobbles, a two-bar countdown drains, then the combo is
  **banked** (points kept, counter reset). Points fill a **HYPE meter**; a full meter fires a SUPER.
- Later, Twitch chat becomes player two: bits, subs, channel points and a free `!punch` take chunks
  off the DJ's health bar; the DJ's moves hit back; rounds end on KO or at track end.

It is co-developed with Triode: we build the theme, the engine and the art; he extends NP3 and the
theme SDK so the data the theme needs actually arrives. His framing: the SDK becomes a microcosm of
his mix-processor-service, and themes are consumers of events.

## 2. Where we are

Discovery and planning are complete. The theme itself is not built. What exists:

| Area | State |
|---|---|
| Research | Six sourced notes (visual style, rendering stack, game mechanics, NP3 platform + full FLX10 MIDI list, Pro DJ Link data model, other hardware ecosystems). `research_notes/README.md` indexes them. |
| Planning docs | 01 what is possible now · 02 game design · 03 protocol proposal for Triode (v0.2) · 04 visual bible and asset list · 05 build plan · 06 hardware matrix and data-path limits · 07 gesture ground truth · 08 graphic design brief · 09 handoff to Triode |
| Tooling | Move detector (`tools/detect_moves.py`), Web MIDI tap with gesture labels (`tools/midi_tap.html`, served by the recorder at http://127.0.0.1:5180/tap, Chrome only), comparison and slicing scripts |
| Renderer spike | Pixi 8 theme with an inlined PNG builds into a single bundle inside the real SDK after two one-line SDK fixes (`docs/sdk-assets-and-dynamic-imports.patch`). Not yet rendered inside NP3 or OBS. |
| Data | Four recordings from 2026-10-06 in `recordings/` including a labelled nine-gesture session with raw MIDI, markers and NP3 states in one file |
| For Triode | Doc 03 (the protocol proposal), doc 09 as a cover note, doc 11 (questions, also issue #1) |

## 3. What we measured (facts, not assumptions)

All from the wire, with a DDJ-FLX10, Rekordbox and NP3 3.0.0-beta.

- **What a theme receives:** `np:track` on track change (identity, BPM, Camelot key, genre, label,
  duration, artwork URL) and `np:mix`, a full six-channel mixer state snapshot on controller events.
  No events, no deltas, no beat phase, no track position, no options, no chat.
- **Decimation:** NP3 emits at most about 10 states per second (about 3 unique per second under
  load) and discards everything between emissions. A raw MIDI tap next to the overlay showed
  22,096 MIDI messages become 38 distinct states in three minutes; a median of 74 raw messages
  collapse into one state; a fader ride of 357 messages became 7 updates. Values are fresh (about
  60 ms old), so the loss is upstream of state assembly on the desktop-to-cloud leg, not in the SSE
  stream or the page. (`docs/06` §A, §A2)
- **What never reaches a theme:** platter and ring rotation (1 kHz on the FLX10), pads, loops, Beat
  FX, Sound Color FX, the COLOR/filter knob, stems. NP3's own FLX10 map reads only play, cue, sync,
  fader, EQ, trim, pitch and jog touch, and binds "jog turn" to the wheel-side ring. (`docs/01` §8)
- **Detectable today from state alone:** bass swap, vocal swap, full kill, fader slam, quick cut,
  EQ sweep, high duck, long blend, three-deck stack, plus every track-metadata move (harmonic mix,
  energy boost, gear change). Proven on recordings with `tools/detect_moves.py`. (`docs/01` §3)
- **Gesture ground truth:** a backspin is touch on, 87 platter messages in 86 ms all negative and
  saturated at −63, touch off, then three seconds of free spin reported on the wheel-side
  controller; NP3 showed two states for it. A nudge was 3,552 ring messages and zero states.
  (`docs/07`)
- **Resolution:** FLX10 faders, EQ and trim are 14-bit on the wire (NP3 reads the 7-bit MSB); most
  other Pioneer gear and all DJM mixers are 7-bit. (`docs/06` §B)
- **Cloud hop latency:** median 47–52 ms from NP3's state timestamp to overlay arrival. Fast enough
  for named events.
- **SDK build:** Vite library mode base64-inlines imported images regardless of settings, so sprites
  ship today with no host change; the SDK's meta scanner breaks on image imports and its bundler
  drops dynamically imported chunks, both fixed by the patch. `entry.js` with Pixi and a PNG is
  1.35 MB raw, 332 KB gzip. (`spike/README.md`)
- **Platform limits:** the art CDN sends no CORS header, so album art cannot be read as pixels;
  dashboard options never reach custom themes; OBS 31/32 run Chromium 127; 127.0.0.1 is a secure
  context from the overlay page.

## 4. What we decided

| Decision | Why |
|---|---|
| Gesture recognition runs in NP3 (desktop app or mix processor), not the theme | raw jog ticks at 1 kHz cannot cross the cloud; the state stream already discards them |
| Events named by **function** (`jog.backspin`, `fader.channel`), never by controller | one theme must serve FLX10, CDJ-3000 + DJM, XDJ, Denon, Serato rigs |
| Every event carries a **source timestamp** at packet receive | timing survives any throttle or batching downstream |
| Continuous controls are **coalesced**, never hold-and-drop | a chop inside a window must still be countable |
| Host announces **per-channel capabilities** (`np:capabilities`); moves are gated per channel | CDJ rigs have position and beat phase but no EQ on the link; Denon has faders but no EQ or jog; Traktor hardware is invisible |
| Renderer: **PixiJS 8**, used imperatively (no `@pixi/react`, which needs React 19) | atlases, animated sprites, bitmap text, nine-slice, particles, stoppable ticker; three.js is the wrong idiom, Phaser owns the page |
| **384×216 virtual canvas scaled exactly 5× to 1920×1080**, nearest sampling, transparent, texture GC off, warm-up render after load | pixel-perfect, cheap fill, nothing pops late in a three-hour stream |
| Sprites **inlined as base64** now; `public/` shipping requested for later | works today; realistic payload is 1–2 MB of indexed PNG |
| **Original pixel art only**, Endesga-32 palette snapped to 12-bit, ≤ 15 colours per sprite | no Capcom assets, names, fonts or likenesses; the idiom is fair game, the assets are not |
| Combo windows in **bars** (8, extended to 16 by sustained activity), 2-bar drop warning, **bank never zero** | DJing has natural pauses; THPS-style stack with a visible balance meter |
| Tier thresholds 3 / 6 / 10 / 15 / 25 / 40 hits; freshness 1.0/0.75/0.5/0.25/0.1; scaling 100→60 % with a floor for big moves; variety cap ×4 | borrowed from SF6 scaling, THPS freshness, Guitar Hero caps, KI announcer |
| **No full-size DJ fighter**: the webcam is P1; 24×24 portraits, a 48×64 corner mascot, a chat crowd strip as P2 | a fighter would compete with the person on camera; 3rd Strike needed 23,039 frames |
| Chat fight-back reacts to cheers that already happened, with deterministic capped damage, no currency, no wagers, no prizes | Twitch Bits policy; an OBS overlay is not a Bits-enabled Extension |
| SFX, if any, off by default | autoplay works in OBS but routing and taste problems under a live mix |

## 5. What is still open

**Osh decides** (`docs/05` §6):
1. ~~Tier word set~~ — decided 2026-10-06: ours (NICE, SOLID, WICKED, SAVAGE, LETHAL, MAXIMUM, ULTRA).
2. P1 name on the plate; approval of portraits + mascot + crowd instead of a full fighter; the mascot concept (working name "Wax", a record-headed brawler).
3. Twitch source: ask Triode for `np:community`, build a Streamer.bot adapter on 127.0.0.1, or both.
4. Rounds per track vs fixed-length rounds; centre timer = track remaining or round clock.
5. SFX as an off-by-default option, or none.
6. Which gestures matter most in his playing (faders yes, crossfader no; hot cues, loops, FX, stems, scratching?).
7. Who draws the ≈ 500 frames: Osh in Aseprite, AI-assisted with cleanup, or a commissioned pixel artist.
8. Whether tier thresholds scale with the rig's available move set or stay fixed across rigs.
9. ~~Where the code lives~~ — decided by Triode: a GitHub fork of the SDK.

Triode's answers (Discord, 2026-10-06): **fork the SDK and modify the fork** (that fork is
the shared surface, so neither side handles the other's private source), and **iteration 1 is one
side only, no PvP**; "2nd iteration, we add something" (chat or DJ vs DJ, still open).

**Triode answers** (`docs/03`, `docs/09`): the event stream with source timestamps and coalescing;
`np:capabilities`; the two SDK build patches; asset shipping; options and visibility messages;
community events; FLX10 and DJM-V10 mapping fixes; decoding gaps in his Pro DJ Link library; where
the decimation timer lives.

**Still to label** (`docs/07` end): transformer chop, full kill, high duck, the drop, filter moves,
scratch, vinyl brake, hot cue juggle, loop roll, beat jump, stem drop, trim boost, cue stutter,
long blend, clean transition, idle.

## 6. Build plan in brief (`docs/05`)

- **Phase 0** alignment with Triode: event list, capabilities, patches, division of work.
- **Phase 1** engine on today's data: scaffold the theme in the SDK, render the spike in OBS,
  port the detector to TypeScript with recorded fixtures, placeholder art, replay harness.
- **Phase 2** art v1 and v2 plus the real event stream as Triode ships it; SDK PRs.
- **Phase 3** chat fight-back: health, damage, rounds, KO, v3 art. **Deferred to iteration 2**
  (Triode: iteration 1 is one side only, no PvP).
- **Phase 4** options, performance pass in the real OBS browser, docs and release.

## 7. Parallel tracks and who does what

| Track | Owner | Entry point |
|---|---|---|
| Engine, theme, tests, tooling | Osh + a Claude session | `README.md` → `docs/05`, `docs/02`, `docs/01` |
| Graphic design and asset pack | Osh + an Opus session | `docs/08 Graphic design brief.md` → `docs/04` |
| NP3 and SDK changes | Triode | `docs/09 Handoff to Triode.md` → `docs/03`, `docs/06`, `docs/07`, the patch, `recordings/` |
| Ground-truth recordings | Osh | `docs/07` procedure |
