# 05 · Build plan (v0.1 draft, 2026-10-06)

Inputs: `01` (measured capability), `02` (game design), `03` (protocol asks), `04` (visual bible),
`research_notes/rendering_stack.md` (engineering). This is a plan, not a commitment; phase
boundaries are where we re-check with Triode.

## 1. What we are building, in one line each

- **A theme** (`street-fighter`) for Now Playing 3: a 384×216 pixel-art fighting-game HUD scaled 5× over the DJ camera, driven by a move/combo engine fed by NP3 events, later with a chat opponent.
- **An SDK/protocol** good enough to build it: named controller events, asset shipping, options, community events, visibility. We specify; Triode implements in NP3 and the SDK; we validate with the recorder.
- **An asset pack** of ≈ 500 hand-finished pixel frames in 13 atlases, original art.

## 2. Stack (decided unless marked)

| Layer | Choice | Why |
|---|---|---|
| Host | NP3 theme SDK (React 18, TS, Vite 6 lib build), upstream 475e322+ | required by the platform |
| Renderer | **PixiJS 8** used imperatively (no `@pixi/react`: it needs React 19) | atlases, AnimatedSprite, BitmapText, NineSlice, ParticleContainer, tint/blend, stoppable ticker; 237 KB gz whole, less tree-shaken |
| Fallback | Canvas2D atlas renderer behind a tiny `Renderer` interface | SwiftShader / hw-accel-off OBS installs |
| Canvas | backing store 384×216, `resolution: 1`, CSS `width/height` ×5 with `image-rendering: pixelated`, `roundPixels`, nearest textures, mipmaps off, `backgroundAlpha: 0`, `preference: 'webgl'`, `gcActive: false` | pixel-perfect, cheapest fill, no late texture re-uploads |
| Loop | fixed-step 60 Hz accumulator outside React; React only for shell/splash/debug HUD | determinism, replay tests |
| Tweens | in-loop tween list; GSAP (already in SDK, PixiPlugin works on v8) only for one-off cinematics | game-clock determinism |
| Assets | **base64 inlined** via Vite lib mode (ships today, no SDK change); Pixi reads data URLs; `public/` shipping requested from Triode for when the payload grows past ~5 MB | zero dependencies on hosting or SDK changes; realistic payload 1–2 MB |
| Fonts | BMFont atlases baked with outline/bevel; runtime `BitmapFont.install` for secondary text | crisp at integer sizes |
| SFX | optional, off by default, `@pixi/sound` or raw Web Audio; "Control audio via OBS" documented | autoplay works in OBS, routing and taste issues |
| Tests | Vitest for the engine on recorded `.jsonl` fixtures; self-postMessage replayer; stress mode; Playwright pixel-exact canvas screenshots on SwiftShader | 3-hour-stream reliability |
| Art tools | Aseprite + CLI export (json-hash), Endesga-32/12-bit palette, Retro Diffusion / PixelLab for reference + VFX, SnowB BMF for fonts | see `04` |
| Not used | three.js (3D is the wrong idiom), Phaser (owns the page, 315–352 KB), DOM/CSS sprites (layer cost), `@pixi/particle-emitter` (peer `<8`) | |

Folder layout and Pixi init snippet: `research_notes/rendering_stack.md` §8.

**Spike result (2026-10-06, `spike/`):** the stack builds inside the real SDK after two one-line SDK
fixes (image imports broke the meta scanner; Pixi's dynamic imports were dropped from the bundle).
`entry.js` = 1.35 MB raw / 332 KB gzip with a PNG inlined. The patch is in
`docs/sdk-assets-and-dynamic-imports.patch` and is item 1–2 of the asks in `03`. Until Triode merges
it we carry the patch locally (same as the sidecar fix). Rendering inside NP3 is not yet verified.

## 3. Phases

### Phase 0 · Alignment with Triode (this week)
- Send `03 Event protocol proposal.md`  plus `docs/sdk-assets-and-dynamic-imports.patch`. Agree on: event envelope, the first batch of events (beat.tick, jog gestures, unthrottled faders/EQ/filter, pads, loops, FX, play/cue edges, onair.change, sourceChange), `np:community`, `np:options`, `np:visibility`, `public/` asset shipping, `subscriptions` opt-in key.
- Agree `np:capabilities` and function-named events so one theme serves FLX10, CDJ + DJM, XDJ, Denon and Serato rigs (`06`).
- Agree the division: we own the theme, engine, asset pack, SDK patches as PRs; Triode owns NP3's mix-processor events and the host side of the protocol.
- Osh answers the decisions list at the end of this doc.
- Exit: a written event list with names Triode will use, so our types match NP3's internal names from day one.

### Phase 1 · Engine on today's data (1–2 weeks of sessions)
- Upgrade the SDK clone to upstream 475e322; apply the two build patches; scaffold `src/themes/street-fighter/` per the layout from the spike; add `pixi.js`. First milestone: the spike renders transparent over camera in OBS via the real overlay URL.
- Input layer takes a capability document and gates matchers per channel; a built-in capability profile per known rig for development (FLX10, CDJ-3000 + V10, SC6000 + X1850).
- Port `tools/detect_moves.py` into TypeScript: delta extraction, ring buffer, matchers for the 22 "today" moves, combo engine (window, freshness, scaling, variety, tiers, drop, bank, rank, HYPE), per-track stats.
- Replay harness: feed `recordings/*.jsonl` in real time and instantly; Vitest fixtures asserting the 6 moves proven in `01`.
- Placeholder art (CC0) and runtime BitmapFont so the HUD works end to end: bars, counter, callouts, ticker, VS card.
- Record a new, longer FLX10 session with the recorder covering every "today" move deliberately (and jog taps, pads, loops, FX so we have ground truth for Triode's events).
- Exit: the theme runs in OBS on a real set, counts combos from faders/EQs, nothing pops late (warm-up pass), idle CPU low.

### Phase 2 · Art v1 + v2 and the real event stream (2–4 weeks, overlaps Triode's work)
- Draw v1 sheets (HUD, fonts, digits, callouts, VS card), then v2 (FX, mascot, big digits, portraits). Palette LUT shader for escalation recolours. Hit-stop, shake, super flash.
- As Triode ships `np:event`: add BACKSPIN, SCRATCH, VINYL BRAKE, HOT CUE JUGGLE, LOOP ROLL, ECHO OUT, FILTER RISER, STEM DROP, NUDGE, ON THE ONE. Keep the state-snapshot path as fallback so the theme still works on older NP3.
- SDK PRs: `public/` shipping (if agreed), `np:options`, sidecar fix (already sent), types for the event protocol, a `useEvents()` hook in `_shared` so other theme authors benefit.
- Exit: full combo experience on stream with original art; Triode has a theme that exercises every event he emits.

### Phase 3 · Chat fight-back (2–3 weeks) — iteration 2 candidate, not iteration 1 (Triode, 2026-10-06)
- Community event source: `np:community` from NP3 if agreed; otherwise the Streamer.bot adapter on 127.0.0.1:8080 (same internal event shape either way).
- Health bars, damage table, caps, guard/heal, breaker, rounds, KO sequence, round and match cards, `!rules`. Twitch policy checklist from `02` §5.
- v3 art: crowd strip, projectiles, banners, KO/win mascot frames.
- Exit: a full match on stream; test events from the dashboard drive the overlay with a TEST watermark.

### Phase 4 · Polish, options, release
- Dashboard options once `np:options` exists (P1 name, SFX, intensity, timer mode, damage scale).
- Performance pass in the real CEF via remote debugging (`--remote-debugging-port=9222`), stats dock baselines hidden/visible/stress.
- Docs, credits (CC-BY fonts), a demo page in `USE/demo`, a stream-ready OBS setup note (1920×1080 source, hw-accel on, 60 fps canvas).

## 4. Risks and mitigations

| Risk | Mitigation |
|---|---|
| Triode's event work slips | Phase 1 is fully viable on today's snapshots; the engine's input layer takes both shapes |
| Current path is sample-and-hold at ~10 Hz (measured: 43 of 47 continuous changes skip steps) | protocol asks for source timestamps and coalescing; theme designs its rhythmic moves around counts from the source, never from arrival rate |
| Rig diversity (CDJ, XDJ, Denon, Serato, Traktor) | capability gating per channel; HUD shows the live move list; test profiles per rig |
| Events cross the cloud (desktop → Socket.IO → mix processor → SSE) | ask for gesture recognition on the desktop/mix processor and coalesced values, not raw ticks; measured jog-touch latency today is ~45 ms, so the path is fast enough for named events |
| Late texture uploads mid-stream | `gcActive: false`, warm-up render after load and after context restore |
| OBS hw-accel off / SwiftShader | detect via `UNMASKED_RENDERER_WEBGL`, warn, Canvas2D fallback |
| Hidden-scene CPU burn | pause on `document.hidden`, idle throttle after 60 s with no events, ask for `np:visibility` |
| Bundle growth from base64 | monitor `entry.js`; move to `public/` once shipped |
| Art consistency / volume | small frame counts by design (≈ 500 total); AI for reference and VFX, hand clean-up; mascot small (48×64) |
| Chat abuse | deterministic damage, per-user and global caps, dedupe, intro immunity |
| Policy | no bits-as-currency, no wagers, no prizes; overlay only reacts to cheers |
| OBS 33 moves to Chromium 150 | nothing exotic used; retest transparency and audio on release |

## 5. Division of work

| Us (Osh + Claude) | Triode |
|---|---|
| Theme, engine, matchers, tests, replay tooling | NP3 mix-processor gesture recognition and `np:event` emission |
| Asset pack and pipeline | Host: `np:community`, `np:options`, `np:visibility`, `public/` serving, `subscriptions` gating |
| SDK PRs (shared hooks, types, build changes) | SDK merges and the `upgrade` path |
| Ground-truth recordings of the FLX10 for each gesture | Mapping fixes (FLX10 filter knob, fader throttle) |
| Streamer.bot adapter (if needed) | Twitch event forwarding (if agreed) |

## 6. Decisions needed from Osh (collected)

1. ~~Tier word set~~ — decided 2026-10-06: set B (NICE … ULTRA), `02` §4.
2. P1 name and the character approach (portraits + corner mascot "Wax" + crowd, recommended; or a full fighter) — `04` §6.
3. Twitch source: ask Triode for `np:community`, build the Streamer.bot adapter, or both.
4. Rounds per track vs fixed-length rounds; timer = track remaining or round clock.
5. SFX option: ship off by default, or drop.
6. Which gestures matter most in Osh's playing (faders yes, crossfader no; hot cues? loops? FX? stems? scratching?) to rank the event asks.
7. Who draws: Osh in Aseprite, AI-assisted with Claude cleanup, or commission a pixel artist (budget).
8. Whether tiers scale with the rig's move set (`02` §3.3).
9. ~~Where the theme repo lives~~ — decided by Triode 2026-10-06: a **GitHub fork of
   `chrisle/nowplaying-theme-sdk`**, created as https://github.com/dfigravity/nowplaying-theme-sdk
   and cloned to `sdk/`; we modify the fork, and that fork is the shared surface.
   SDK changes go back upstream as PRs from it.

Triode's answers (Discord, 2026-10-06): **fork the SDK and modify the fork** (that fork is
the shared surface, so neither side handles the other's private source), and **iteration 1 is one
side only, no PvP**; "2nd iteration, we add something" (chat or DJ vs DJ, still open).
Consequence: Phase 3 (chat fight-back) is no longer iteration 1. Iteration 1 ships the DJ side
only (moves, combos, specials, supers, HYPE, rank, mascot, VS card); the second side is
iteration 2.
