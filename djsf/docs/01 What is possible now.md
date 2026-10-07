# 01 · What is possible now (measured, 2026-10-06)

Everything here is taken from the wire: the Protocol Spy theme + `recorder.py` in
`../Now Playing 3 Overlays/`, recording `recordings/np3-2026-10-05_223636.jsonl`,
DDJ-FLX10 → Rekordbox (Performance mode) → NP3 3.0.0-beta → overlay in OBS. The
detector that produced the evidence is `tools/detect_moves.py` in this folder.
Platform background: `../Now Playing 3 Overlays/docs/NP3 Platform Knowledge.md`.

## 1. What the theme receives today

| Message | When | What we can do with it |
|---|---|---|
| `np:track` | on-air track change | Track identity, BPM, Camelot key, genre, label, duration, artwork URL. Gives us musical time (bar clock), harmonic-mix judgments, per-track scoreboards. |
| `np:mix` | every controller event, throttled | A full **state snapshot** of 6 channels: fader, 3-band EQ, trim, filter, play, cue, jog-touch, loop flag, crossfader, NP3's own on-air score. No events, no deltas, no velocities. |

Nothing else arrives (no options, no chat, no community events).

## 2. Stream characteristics (DDJ-FLX10 connected, `mixer.sourceId: "midi"`)

| Property | Measured |
|---|---|
| Update cadence | event-driven, **throttled to ~100 ms** (54 deduped states, gaps < 1 s: min 87 ms, median 127 ms) |
| Duplication | every state is sent twice; dedupe on the state minus `lastUpdateAt` |
| Latency | ~45 ms from a jog touch to the message |
| Fader resolution | **7-bit** (values are exactly k/127: 63/127, 69/127, 119/127). The "coarse" fader seen earlier is under-sampling by the throttle during a fast throw, not quantization |
| EQ resolution | 1/64 steps on the cut side (0 = flat, −1 = full kill); boost side not yet observed |
| Trim | k/127 |
| Filter knob | never moved `signals.filter` on the FLX10 (mapping gap in NP3) |
| Jog | `jogTouching` boolean only. **No rotation direction or speed.** |
| Pads, hot cues, loops, FX, tempo | not represented at all (`looping` stayed false, `jogMode` null) |
| On-air | `onAir.currentOnAir` flips after a 1875 ms debounce once the weighted score passes 0.3 |

Consequence: the theme can see **continuous controls at ≤10 Hz** and **play/cue/touch
booleans**. It cannot see anything that is a short gesture (backspin, scratch, pad hit,
loop roll, FX stab) unless NP3 names it for us.

## 3. Moves provably detectable from today's payload

Run against the real recording (`python3 tools/detect_moves.py <jsonl>`), BPM 123, bar = 1.95 s:

| Move | Rule (theme side) | Evidence in recording |
|---|---|---|
| **BASSLINE SWAP** | low EQ on channel A crosses below −0.5 while low on channel B crosses above −0.5, within one bar | twice: ch2→ch1 (105 ms apart) and ch1→ch2 (same update) |
| **FULL KILL** | low, mid and high on one channel all cut within one bar | ch2, three bands in 0.7 s |
| **FADER SLAM** | channel fader 0 → ≥0.5 within ≤250 ms | ch1 twice (0 → 1 in one update) |
| **EQ SWEEP IN** | a band restored monotonically through ≥4 intermediate values within 4 bars | ch2 mid, 10 steps over 5.8 s |
| **HIGH DUCK** | high cut and restored on the same channel within two bars | ch1, 488 ms |
| **JOG TOUCH** | `jogTouching` rises while playing | ch1 three taps in 1 s, ch2 once. **Cannot** be classified as scratch vs backspin vs nudge |
| QUICK CUT | fader cut on A within 2 s of a slam on B (both playing) | rule written, no instance in this short recording; the primitives (slam, cut, on-air flip) all fire |
| PLAY / CUE / STOP | boolean edges | all present |

Also derivable from track metadata at a transition: **HARMONIC MIX** (Camelot
neighbour), **ENERGY BOOST** (+1 key or +BPM), **KEY CLASH**, **LONG BLEND** (both
decks open > N bars), **CLEAN TRANSITION** (outgoing fully cut and stopped within a bar
after on-air flips). The shared engine in `../Now Playing 3 Overlays/sdk/src/themes/_shared/`
already has the key parser, transition classifier and bar clock.

## 4. Moves that need NP3 / SDK changes

| Move | Missing data | Smallest change that unlocks it |
|---|---|---|
| **BACKSPIN**, SCRATCH, VINYL BRAKE, NUDGE | jog rotation direction + speed (FLX10 sends it as a relative CC every few ms) | NP3 recognises the gesture in its mix processor and emits a named event (`jog.backspin`, `jog.scratch`, `jog.nudge`) with duration and peak speed. Sending raw ticks through postMessage at ≤10 Hz would not work. |
| HOT CUE JUGGLE, PAD DRUM, SAMPLER HIT | pad presses | `pad.press { deck, mode, index }` events |
| LOOP ROLL, BEAT JUMP | loop/jump buttons | `loop.on/off { beats }`, `beatjump { beats, dir }` |
| ECHO OUT, FX STAB | beat FX on/off, type, level | `fx.on/off { unit, type }`, `fx.level` |
| FILTER RISER | filter knob | fix the FLX10 CFX mapping into `signals.filter` (today constant 0) |
| STEM DROP (FLX10 has per-channel vocal/drums/inst toggles) | stems state | `stems.toggle { deck, part, on }` |
| TEMPO NUDGE, PITCH RIDE | tempo slider / pitch bend | `tempo.change { deck, pct }` |
| CROSSFADER SLAM | crossfader at full rate | present but throttled; fine for slams, too slow for cuts/transforms |
| CHOP / TRANSFORMER (≥4 fader on/offs per bar) | fader at >10 Hz | raise the throttle for faders to ~30 Hz, or have NP3 count the toggles and emit `fader.chop { deck, count }` |

Design conclusion: **gesture recognition belongs in NP3 (the mix-processor-service), not in
the theme.** The theme should receive a stream of named, timestamped events plus the
existing state snapshot, and do combo logic on top. That is exactly Triode's stated plan
("the SDK as a microcosm of the mix-processor-service"), so our job is to specify the event
vocabulary, fields and rates. See `03 Event protocol proposal.md`.

## 5. What the SDK and host can and cannot ship today

- Bundle = `entry.js` + `style.css` + per-theme `index.html` only. **No images or fonts are
  copied.** Sprites must be inlined as data URIs (base64, +33 %) or hosted externally, unless
  the build script is extended to copy an assets folder (Triode owns that script; allowed file
  types already include png/webp/json/woff2; 25 MB zip cap).
- Only `{ track }` reaches the component through the SDK entry; mix state is read straight off
  `window` (our `useMixState`). Options from the dashboard do not reach custom themes.
- Artwork CDN has no CORS header, so album art cannot become a texture; CSS display only.
- OBS 31/32 = Chromium 127: WebGL2, canvas, CSS pixelated scaling all available.
- 127.0.0.1 is a secure context from the overlay page, so a **local bridge** (e.g. for Twitch
  events) is reachable from the theme in both Chrome and OBS.
- Upstream SDK moved to 475e322 (readiness announced once; animation timers cancelled). Local
  clone is at b8ad268 + our sidecar patch; upgrade before building the new theme.

## 6. Renderer spike (verified 2026-10-06, `spike/`)

A scratch clone of upstream + `pixi.js@8.22.0` + a theme importing a PNG:
- The SDK build failed twice for reasons that affect any sprite theme: the meta reader has no esbuild
  loader for image imports, and Pixi's dynamic imports were split into chunks that the bundle script
  never copies (30-byte `entry.js`). Both fixed with one-line patches (`docs/sdk-assets-and-dynamic-imports.patch`).
- After the patches: single `entry.js` of 1,350,649 bytes (332 KB gzip) with the PNG inlined as a
  `data:image/png;base64` URI. Vite library mode inlines imported images regardless of
  `assetsInlineLimit`, so sprites ship today with no host change.
- Not yet rendered inside NP3 or a browser; that is the first task of Phase 1.

## 7. Other rigs

The FLX10 is the measured case. CDJ-3000 + DJM, XDJ all-in-ones, Denon StageLinQ, Serato OSC and
Traktor HID each expose a different subset; the full per-rig matrix, the sample-and-hold measurement
and the capability model are in `06 Hardware matrix and data-path limits.md`.

## 8. What NP3 actually reads from the FLX10 (from Triode's public `autopilot-mappings`)

Per deck: play (Note 11), cue (12), sync (88), volume (CC 19), EQ hi/mid/low (CC 7/11/15), trim (CC 4),
pitch (CC 0), jog_touch (Note 54), jog_turn (CC 33, which is the wheel-side ring, not the platter),
key_lock (Note 65, which is actually TEMPO RESET). Global: crossfader (ch7 CC 31), master, headphones.
**Not mapped:** platter rotation (CC 34/35), pads (channels 8–15), stems (Notes 13/14/15), loops
(Notes 16/17/20), Beat FX (channel 5), Sound Color FX and the COLOR/filter knobs (ch7 CC 23–26).
That is the whole gap list, with numbers, and it is in `03 Event protocol proposal.md` §2.

Pipeline fact that matters: desktop app → Socket.IO → cloud mix processor → SSE → overlay page →
postMessage → theme. Events cross the cloud, so gesture recognition should happen on the desktop or
in the mix processor and only named gestures plus coalesced values should travel.
