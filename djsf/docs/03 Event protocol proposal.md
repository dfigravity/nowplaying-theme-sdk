# 03 · Event protocol proposal for Now Playing 3 and the theme SDK

For Triode, from Osh and Claude, 2026-10-06. Draft v0.2 for discussion (v0.2 adds the hardware-agnostic
naming, `np:capabilities`, source timestamps and coalescing, and the Pro DJ Link / DJM / StageLinQ sources).
Background and evidence: `01 What is possible now.md`, `06 Hardware matrix and data-path limits.md`,
`research_notes/np3_platform_and_flx10_midi.md`, `research_notes/prodjlink_data_model.md`, `research_notes/hardware_ecosystems.md`,
`research_notes/game_mechanics.md` §6, `research_notes/rendering_stack.md` §4 and §8.

## 0. Why

You said the SDK should become a microcosm of the mix-processor-service, with NP3's internal event
names copied into it, and that themes should be consumers of events. We agree, and we have a theme
that needs exactly that. Today a theme gets `np:track` and (if it listens on `window` itself)
`np:mix` state snapshots at ~10 Hz. From those we can already detect fader cuts, bass swaps, EQ kills
and sweeps (proven on a recording). Everything that is a short gesture (backspin, scratch, pad hit,
loop roll, FX stab, filter sweep) is invisible, partly because the snapshot is throttled and partly
because the FLX10 map in NP3 does not read those controls. Below is what we would like to receive, in
priority order, with the exact MIDI the FLX10 sends for each so the mapping work is concrete.

## 1. The envelope: `np:event`

```json
{
  "type": "np:event", "protocol": 1,
  "at": 1791234567890, "seq": 48213,
  "source": "midi", "device": "DDJ-FLX10", "deck": 2,
  "name": "jog.backspin",
  "value": 1, "prev": 0, "delta": 1,
  "meta": { "durationMs": 420, "peakSpeed": -3.4, "beat": { "bpm": 124, "beat": 3, "bar": 7, "phrase": 2, "phaseMs": 112 } }
}
```

- `at`: host epoch ms at MIDI receive; `seq`: per-session counter so a theme can detect drops.
- `deck`: 1-based channel, or null for mixer-wide controls.
- `value` normalised like the mix state today (0..1 unipolar, −1..1 bipolar, booleans); `prev`/`delta` for the same name+deck.
- `meta.beat` attached whenever the host knows the grid (see 2.1).
- Batch when several events land in one frame: `{ type: "np:events", protocol: 1, events: [...] }`.
- Keep `np:mix` as the periodic state for late joiners and for themes that only want state.
- Gate behind a theme opt-in in the manifest, as you proposed for mix: `meta.subscriptions: ["mix", "events", "community"]`.
- **Names are functions, not controls.** `jog.backspin` is the same event whether it was recognised from FLX10 platter ticks (CC 34), from a CDJ-3000's 30 ms absolute-position stream going backwards, or from an S4 MK3 HID wheel if a bridge ever exists. `fader.channel` is the same whether it came from a 14-bit FLX10 pair, a 7-bit DJM CC, a StageLinQ float or the DJM-A9 Stagehand unicast. The theme never sees controller names except in capabilities.
- **Timestamps at the source.** `at` is stamped when the MIDI/link packet is received on the desktop, not when the state is assembled or emitted. This is what makes timing survive any throttle or batching downstream.
- **Coalesce, do not hold.** We measured the current path as sample-and-hold at ~10 Hz (43 of 47 continuous changes jump more than one MIDI step; a full fader throw arrives as one 0→127 update). For continuous controls, if a rate limit is needed, send per window `{ value, min, max, crossings }` or at least every crossing of a coarse grid (e.g. 0, 0.1, 0.5, 0.9, 1), so a chop that begins and ends inside the window is still countable. Buttons, pads and gestures: never coalesced.

## 1b. Capabilities: `np:capabilities`

The theme must know what the rig can report so it can enable the right moves and tell viewers why a
CDJ set has no BACKSPIN callout but has ON THE ONE. Sent on connect, on device or source change, and
on request (`np:capabilities:get`). Full schema and enum rules in `06 Hardware matrix and data-path limits.md` §D;
the essentials: a `sources[]` list (midi / prodjlink / stagelinq / serato-remote / history / simulated,
with latency and max rate), per-channel blocks for transport, jog, tempo, mixer, performance and deck,
each leaf typed `edge | bool | rel | uni | bi | none` with `bits` and a `source` id, a `rates` block
(`hold@10Hz | coalesced@30Hz | unthrottled`), `timestamps: state | perEvent`, and an `unsupported[]`
list for visible devices NP3 cannot read (HID-only gear) with a reason string.

## 2. Events, ranked, with the FLX10 MIDI behind each

Deck controls are on MIDI channels 1–4 (`n`), pads on 8/10/12/14 (SHIFT: 9/11/13/15), Beat FX on 5,
mixer-global on 7. Faders and knobs are 14-bit (LSB CC = MSB + 32). Source: AlphaTheta's official
DDJ-FLX10 MIDI message list; the full transcription is in the platform research note §3.

| # | Event | Fields | FLX10 source | Why |
|---|---|---|---|---|
| 1 | `beat.tick` | bpm, beat 1–4, bar, phrase, phaseMs, deck (master/on-air) | not MIDI-visible on the FLX10 input side; from the source's beat grid or `track.position` + grid | all "on the one" / phrase rules; our combo windows are in bars |
| 2 | `jog.backspin`, `jog.scratch`, `jog.brake`, `jog.nudge` (gestures recognised in the mix processor) and/or `jog.rotate` coalesced ≤ 30 Hz with direction and speed ratio | deck, direction, speed, touching, mode, durationMs | platter rotate **CC 34** (vinyl on) / **CC 35** (vinyl off), relative around 0x40; touch **Note 54**; wheel-side ring CC 33 (nudge). NP3's map currently binds `jog_turn` to CC 33, which is the ring, not the platter | Backspin, Scratch, Vinyl Brake, Nudge. Recognition belongs in NP3: raw ticks through the cloud and a 10 Hz snapshot cannot carry them |
| 3 | continuous mixer values as events, unthrottled (or ≥ 30 Hz), 7-bit minimum, 14-bit if cheap: `fader.channel`, `fader.cross`, `eq.low/mid/high`, `trim`, `filter` | deck, value, prev, delta, raw | CH fader CC 19/51; crossfader ch7 CC 31/63; trim CC 4/36; EQ hi/mid/low CC 7/39, 11/43, 15/47; **COLOR (filter) knobs ch7 CC 23–26 / 55–58, currently unmapped** (`signals.filter` is always 0 on the FLX10) | Transformer, Crab, Filter Riser/Wobble; today's fader readings are under-sampled by the ~100 ms throttle |
| 4 | `pad.press` / `pad.release` | deck, mode, page, index 1–8, shift | pad channels; note = mode base + 8×page + pad: HOT CUE 0, PAD FX 1 16, BEAT JUMP 32, SAMPLER 48, KEYBOARD 64, PAD FX 2 80, BEAT LOOP 96, KEY SHIFT 112; mode buttons Notes 27/30/32/34 and PAGE ◀/▶ 36–51 encode the active mode | Hot Cue Juggle, Cue Drum, Beat Jump, Loop Roll, Sampler hits |
| 5 | `loop.in`, `loop.out`, `loop.exit`, `loop.active`, `loop.size` | deck, beats | LOOP IN Note 16, LOOP OUT 17, 4 BEAT/EXIT 20 (+SHIFT 76/77/80); BEAT LOOP pads (base 96) | Loop Roll, balance state that extends a combo |
| 6 | `fx.toggle`, `fx.select`, `fx.level`, `fx.beats`, `fx.assign`, `colorfx.toggle` | unit, on, effectName, channel, value | Beat FX ON/OFF ch5 Note 71; select ch5 Notes 32–45 (echo 33, roll 43 …); LEVEL/DEPTH ch5 CC 2/34; CH SELECT ch5 Notes 16–22; Sound Color FX ch7 Notes 0–5 | Echo Out, FX stabs, named callouts ("ECHO OUT" not "FX") |
| 7 | `stems.toggle` | deck, part drums/vocal/inst, on | ACTIVE PART Notes **13/14/15** on the deck channel | Stem Drop, Acapella Swap (FLX10-specific, very visual) |
| 8 | `deck.play`, `deck.cue`, `deck.sync`, `deck.keylock`, `deck.slip`, `deck.vinylMode` as edges | deck, on | PLAY 11, CUE 12, SYNC 88, SHIFT+KEY SYNC 100 (key lock; NP3's map has `key_lock` on 65, which is TEMPO RESET), SLIP 64; vinyl mode inferred from CC 34 vs 35 | cheaper than diffing state; Dead Stop, Cue Stutter |
| 9 | `tempo.slider`, `tempo.bend` | deck, value, bpm | TEMPO CC 0/32 (14-bit); wheel-side ring CC 33; beat jump Notes 94/95 | Nudge, Gear Change |
| 10 | `deck.load` / `deck.eject` with the track object, and `track.position` every 500 ms | deck, track, elapsedMs | from the source (rekordbox history + grid) | end-of-track awareness; phase if `beat.tick` is impossible |
| 11 | `onair.change` | current, previous, reason | already inside the state | the trigger for Harmonic Mix / Energy Boost evaluation |
| 12 | `mixer.sourceChange` | midi / simulated / bypass | — | the theme stops scoring when the mixer is simulated |

Rates: faders/EQ/filter/trim/crossfader unthrottled or ≥ 30 Hz; jog rotate coalesced ≤ 30 Hz (or
gesture events only); buttons/pads/loops/FX unthrottled edges; `beat.tick` once per beat;
`track.position` 2 Hz. A busy minute is a few hundred events; fine for postMessage, but since
desktop → cloud → SSE is the path, gesture recognition in the desktop app or mix processor and
coalesced continuous values keep the cloud hop cheap.

## 2b. Where the same events come from on other rigs

| Event | FLX / DDJ / XDJ (MIDI) | CDJ-3000 + DJM over Pro DJ Link | DJM over USB MIDI | Denon (StageLinQ) | Serato Remote (OSC) |
|---|---|---|---|---|---|
| `beat.tick` | none (grid needed) | beat packet `28` once per beat; phase by interpolation; **alphatheta-connect does not parse `28` today** | MIDI clock `F8`, 24 ppqn | BeatInfo ≈ 28 Hz | none |
| `track.position` | none | absolute position `0b` every 30 ms (CDJ-3000; not Opus Quad); older players: beat count × grid at 200 ms | — | `PlayheadPosition` state (ms cadence; **unsubscribed by NP3's library today**) | `Playhead` seconds, rate unknown |
| `jog.*` gestures | platter CC ticks (CC 34/35 on FLX10) | **derive from `0b` velocity**: negative = backspin, sign flips = scratch, decay to 0 = brake; touch from P_1/P_2 flags | — | touch only (`ExternalScratchWheelTouch`) | — |
| `fader.channel`, `fader.cross` | CC (7-bit; 14-bit on FLX10) | **not on the link** for V10/NXS2; on-air boolean only. DJM-A9 via Stagehand unicast `0x39` at ~4 Hz, 8-bit | CC on movement after **MIDI ON** (V10 CC 11–14, 6D/6E; XF 0B) | `/Mixer/CHnfaderPosition`, `CrossfaderPosition` floats | `Upfader`, `Crossfader` floats |
| `eq.*`, `filter`, `trim` | CC | not on the link (A9 Stagehand: EQ/colour at 4 Hz) | CC (V10 4-band incl. LOW-MID, per-channel filter CC 20–25, isolator, sends) | **not published** by Engine OS (X1850 EQ stays local) | not exposed |
| `fx.*` | CC/Note | not on the link | V10/A9 type, on/off (72), level (5B), beats (4C/4D), channel select notes, TIME 14-bit | none | none |
| `pad.press` (hot cues etc.) | Note on pad channels | **derive**: position jump in `0b` to a known cue time (cue list via dbserver/ANLZ); no button id; set/delete flashes `u_c1` | — | `HotCue%d` unverified; `BeatJumpIndex` | none |
| `loop.*` | Note (buttons only) | loop in/out/beats fields in CDJ-3000 status (200 ms), P_1 = 04 active; slip from P_3 | — | `CurrentLoopIn/Out`, `SizeInBeats`, `LoopEnableState`, `QuickLoop1..8` | `AutoLoopOn`, `ManualLoopOn`, `LoopRollOn`, `BeatLength` |
| `stems.toggle` | Notes 13/14/15 (FLX10), pads (FLX6-GT, AZ, Opus) | nothing in any packet | — | none | none |
| `deck.play/cue` edges | Notes | P_1 flags at 200 ms (faster while jogging); exact edge from `0b` | — | `Play`, `PlayState` | `playRate` ≠ 0 |
| `onair.change` | scored | native per-channel on-air `03` (6-ch variant for V10) | derived | derived (`CH1OnAir` unverified) | derived |
| `tempo.*`, key, sync, master | CC / Notes | pitch ×4, key, key shift (cents), master tempo, sync flags in status | — | `Speed`, `SyncMode`, `DeckIsMaster`, `CurrentKey` | `bpm` |

Three library-level gaps on your side fall out of this table: parse beat packets `28` (and `29`) in
alphatheta-connect; decode the CDJ-3000 status fields you skip today (P_2, P_3, loop start/end/beats,
key shift); and check the `0b` BPM/pitch offsets (alphatheta-connect reads BPM at 0x30 and divides
pitch by 6400, where dysentery and beat-link document 0x38 and ÷100; the unit test is self-consistent
rather than hardware-derived). On the Denon side, subscribe the position states; on the MIDI side,
the DJM-V10 map has seven speculative entries while the official list is public and complete, and the
X1850 and Rane Seventy-Two maps are empty.

## 3. Community events: `np:community`

For the chat fight-back layer we need cheers, subs, gift subs, resubs, raids, channel-point
redemptions and plain chat (for a free `!punch`). Two observations from your stack:

- NP3's Twitch service holds an OAuth token with chat-post scopes only. Reading cheers (IRC PRIVMSG
  `bits=` tag), subs/gifts/resubs/raids (IRC USERNOTICE) and chat needs **no broadcaster scopes** when a
  bot account is in the channel, which is exactly how the Check-In globe works (mod the bot). Only
  channel-point redemptions without text input and hype trains need EventSub with broadcaster scopes.
- You already run a Socket.IO fan-out of chat-derived events to browser sources for the globe.

Proposed message (one per event, `test: true` from a dashboard test button):

```json
{ "type": "np:community", "protocol": 1, "at": 1791234567890, "id": "twitch:abc123", "platform": "twitch",
  "kind": "cheer", "user": { "id": "1", "login": "osh", "display": "Osh", "isSub": true, "isMod": false },
  "amount": 500, "unit": "bits", "tier": null, "message": "take that", "reward": null, "test": false }
```

`kind` ∈ cheer · sub · resub · gift · redeem · raid · follow · hype · chat, with amount/unit/tier per
kind (table in `research_notes/game_mechanics.md` §4.4). If this is out of scope for NP3, we will
build a Streamer.bot adapter on 127.0.0.1 and the theme will not know the difference; the schema above
is what the engine consumes either way.

## 4. SDK and host changes (small, most already verified)

1. **Asset imports break the build** (verified): `scripts/theme-meta.mjs` has no esbuild loader for relative image imports, so any theme importing a PNG fails before Vite runs. Patch: stub non-code relative imports like CSS. `docs/sdk-assets-and-dynamic-imports.patch`.
2. **Dynamic imports ship as a stub** (verified): Vite library mode splits code-split libraries (Pixi) into chunks and `build-bundle.mjs` copies only `entry.js`, so the bundle had a 30-byte `entry.js`. Patch: `inlineDynamicImports: true` in `vite.bundle.config.ts`. Same patch file.
3. **Inlined assets work today** (verified): library mode base64-inlines imported images regardless of `assetsInlineLimit`; our spike's `entry.js` is 1.35 MB / 332 KB gzip with the PNG inside. For when art grows: copy `src/themes/<id>/public/**` into `themes/<id>/public/**` and serve it (patch sketch in the rendering note §4b). Please confirm the host serves arbitrary files from the ZIP at their paths and that `entry.js` is served brotli/gzip (Cloudflare suggests yes).
4. **Options**: build copies `meta.fields` into the manifest; host renders them and posts `np:options { protocol, values }` on load and change. Our theme needs P1 name, intensity, SFX toggle, damage scale.
5. **Visibility**: forward OBS `obsSourceVisibleChanged` / `obsSourceActiveChanged` as `np:visibility { visible, active }` so a long-running theme can idle in hidden scenes.
6. **Protocol types in the SDK**: `EnrichedTrack` gains `duration`, `remixer`, `releaseDate`, store URLs; add `MixState`, `NpEvent`, `NpCommunity` types; `entry.tsx` forwards `mix`, `events`, `community` to the component (or via a `useNowPlaying()` hook) so themes stop listening on `window` themselves.
7. **`np:ready`**: the host component we read does not react to it yet; if it will resend buffered state, say so; otherwise themes should not wait on it.
8. **Mapping fixes** in NP3's FLX10 map: `jog_turn` → platter CC 34/35 (ring CC 33 as `jog_bend`), `key_lock` → Note 100, add `filter` on ch7 CC 23–26, LSBs for 14-bit faders if resolution matters.
9. **Source timestamps and coalescing** (section 1): per-event `at` at packet receive; continuous values coalesced with min/max/crossings or unthrottled; never hold-and-drop. Measured with a raw MIDI tap next to the overlay (2026-10-06): 22,096 MIDI messages in 3 minutes became 38 distinct states; a median of 74 raw messages collapse into each emitted state; a fader ride of 357 messages became 7 updates; a 1 kHz platter stream never appears at all. The value inside each state is only ~60 ms old, so the decimation sits before or at state assembly on the desktop → cloud leg, not in SSE or the page. Which component holds that timer, and can it become per-control coalescing?
10. **`np:capabilities`** (section 1b) with `unsupported[]` for HID-only gear.
11. **Pro DJ Link decoding** (section 2b): `28` beat packets, undecoded status fields, `0b` offsets; StageLinQ position subscription; DJM-V10 / X1850 / Seventy-Two MIDI maps.
12. **Docs**: the help-center Theme SDK page still describes `registerTheme` / `phase`; the SDK README says "subscription" while the purchases page says one-time. Small things, but theme authors will trip on them.

## 5. What we will do on our side

- Build the theme so it runs on today's snapshots and upgrades itself when `np:event` appears.
- Record ground truth: a Protocol Spy session where Osh performs every gesture on the FLX10 (named, timestamped) so you can validate recognisers against real data. Recorder and spy theme already exist.
- Send SDK PRs: the two build fixes above, protocol types, shared hooks (`useMixState` exists; `useEvents`, `useCommunity` next), and the sidecar fix already sent.
- Keep this document updated as the contract; the theme's types will use your event names verbatim once you share them.

## 6. Questions

1. Full `mix-processor:update` schema (the shared types) so our parser stops guessing.
2. Is per-channel `track` populated for rekordbox + FLX10 in all cases? Two help pages disagree on whether a MIDI controller affects on-air timing with rekordbox.
3. Where do you want gesture recognition: desktop app, mix processor, or SDK-side with raw events? Our vote: desktop/mix processor emits gestures; SDK ships the same recogniser code for the playground.
4. Which of the events in §2 are cheap for you this month? We can sequence the theme around that.
