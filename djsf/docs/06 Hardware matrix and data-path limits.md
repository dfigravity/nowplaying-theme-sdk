# 06 · Hardware matrix and data-path limits (v0.1 draft, 2026-10-06)

Osh's point: the FLX10 is one rig. NP3's users also play CDJ-3000s with a DJM-V10 or A9, XDJ
all-in-ones, Opus Quad, Denon Prime over StageLinQ, Serato with Rane or DDJ-REV, Traktor with NI
hardware. The theme must be built on a hardware-agnostic control model, learn what the connected rig
can report, and degrade its move set honestly. This doc has three parts: (A) what the current data
path loses, measured; (B) the canonical control taxonomy and variables; (C) the per-rig matrix.
Parts B, C and D draw on `research_notes/prodjlink_data_model.md` and `research_notes/hardware_ecosystems.md`.

## A. What the current path loses (measured on the FLX10 recording)

Path today: controller → MIDI Bridge → desktop app → Socket.IO → cloud mix processor → SSE →
overlay page → postMessage → theme. Each `np:mix` is a full state snapshot (median 2.9 KB, up to
5.6 KB with six loaded channels).

| Property | Measured | Consequence |
|---|---|---|
| Emission cadence | ≤ 1 state per ~100 ms (min gap 87 ms, median 127 ms) | ≤ 10 Hz view of every control |
| Sampling behaviour | **sample-and-hold, intermediate values dropped**: 43 of 47 continuous changes jump > 1 MIDI step; full fader throws arrive as a single 0 → 127 update; EQ turns jump 10–64 steps between states | a gesture that starts and ends inside one window (chop, crab, stab, tap) is **invisible**, not merely late |
| Duplication | every state sent twice | dedupe on state minus `lastUpdateAt` |
| Cloud latency | overlay arrival minus `state.lastUpdateAt`: min 19, median 47, max 126 ms | the hop is fast; the throttle, not the network, is the limiter |
| Timestamps | only `lastUpdateAt` (state assembled), no per-signal time | cannot reconstruct intra-window timing; beat-aligned bonuses need source timestamps |
| Beat phase | none | no "on the one", no phrase bonuses; bar clock is approximated from play edges |
| Track position | none in the state (duration in `np:track`) | end-of-track and progress only by inference |
| On-air | debounced 1875 ms on House/Techno preset; `np:track` can trail the fader move by seconds | track-change moves (Harmonic Mix, Clean Transition) resolve late by design; we evaluate them from the fader edges and attach the track when it arrives |
| Where the throttle lives | measured (A2): upstream of state assembly on the desktop → cloud leg; values are ~60 ms fresh but emitted ≤ 10 Hz with everything between discarded | `tools/midi_tap.html` + `tools/compare_tap.py` |

### A2. Tap results: raw MIDI vs. what the overlay received (session 2026-10-06 10:33, 3 min)

Raw FLX10 MIDI logged by `tools/midi_tap.html` into the same file as the Protocol Spy stream
(`../Now Playing 3 Overlays/recordings/np3-2026-10-06_103312.jsonl`; local copy of the tap in
`midi-tap-2026-10-06T14-36-43-832Z.jsonl`). Rerun with `python3 tools/compare_tap.py <file>`.

| Measure | Value |
|---|---|
| Raw MIDI messages | **22,096** |
| `np:mix` messages received | 124, of which **38 unique** (each state now arrives ~3×, not 2×) |
| Raw CC messages collapsed into one emitted state (active windows) | median **74**, max 6,826 |
| Channel 2 fader | 357 raw MSB messages, 126 distinct values → **7** state changes; up to 122 raw messages between two consecutive states |
| Channel 1 platter | 6,654 messages in 7.2 s, one per **1.0 ms**, deltas −15..+18 (3,847 backward ticks) → **never appears** in any state |
| COLOR knob (ch7 CC 23/55) | 545 messages → never in `signals.filter` (confirms the mapping gap) |
| Pads (ch10 notes 0–7, 25–26), LOOP 4-beat, SHIFT+jog | present raw, absent from every state |
| Raw MIDI → NP3 `lastUpdateAt` | p10 11 ms, median 61 ms, p90 186 ms |
| Raw MIDI → overlay arrival | p10 0 ms, median 52 ms, p90 171 ms |

Reading: the value inside a state is fresh (about 60 ms old), so the path is not slow; it is
**decimated**. Emission is capped near 10 Hz and everything between emissions is discarded. Because
`lastUpdateAt` is already ~60 ms behind the raw message and arrival follows within milliseconds, the
decimation happens before or at the state assembly on the desktop → cloud leg, not in the SSE or the
overlay page. Only Triode can say which component holds the timer; the numbers above are what he
needs. A platter at 1 kHz could never be forwarded raw through this path anyway, which is why gesture
recognition has to run on the desktop.

### Impedance per move class (requirement vs. what today's path delivers)

| Move class | Needs | Today | Verdict |
|---|---|---|---|
| Slow continuous (sweep in, slow burn, long blend, riser over bars) | ≤ 2 Hz, monotonic trend | 10 Hz hold | fine |
| Threshold crossings (bass swap, full kill, quick cut, duck, slam) | the crossing within ~1 beat | crossing visible, time quantised to 100 ms | fine for detection; timing ±100 ms |
| Rhythmic fast (transformer ≥ 4 chops/bar, crab, filter wobble, cue stutter) | ≥ 20–30 Hz or counted at source | 10 Hz hold | **lost or under-counted**; at 128 BPM 8th-note chops are 234 ms apart (borderline), 16ths 117 ms (gone) |
| Jog gestures (backspin, scratch, brake, nudge) | tick direction + speed at ≥ 30 Hz, or a gesture event | touch boolean only | **impossible** without a new event |
| Button bursts (hot-cue juggle, pad drumming, loop roll, beat jump) | edges unthrottled | not in the state at all | **impossible** without mapping + event |
| Beat-aligned bonuses (on the one, phrase drop) | beat phase ± 30 ms and source timestamps | none | **impossible** today |
| Track-metadata moves (harmonic, energy boost, gear change) | `np:track` | present, late | fine |

Conclusion for the protocol (`03`): (1) events must carry a **source timestamp** (`at` at MIDI/link
receive) so timing survives any throttle; (2) continuous controls should be **coalesced, not held**
(per emission window send min/max/last, or send every crossing of a configurable threshold grid),
or sent unthrottled; (3) **gesture recognition at the source** for jog and button bursts; (4) a
**capability announcement** so the theme knows what the rig can report (part C).

## B. Canonical control taxonomy and variables

Source: `research_notes/hardware_ecosystems.md` §1 (built from NP3's own 77-name control
vocabulary in `autopilot-mappings`, the Pioneer MIDI lists, StageLinQ state maps, Serato Remote OSC,
Mixxx HID maps). Types: `edge` = press and release both timestamped · `bool` = latched state only ·
`uni` 0..1 · `bi` −1..1 · `rel` = signed delta per message · `enum` · `int` · `time` · `float`.
Names in the "ours" column are the function-named events we propose; NP3 names are the existing
`npControlType` strings where one exists.

| Group | Control | Type | Native resolution by path | Typical rate | NP3 name → ours | Moves that consume it |
|---|---|---|---|---|---|---|
| transport | play/pause | edge | Note; StageLinQ `Play`/`PlayState`; Serato `playRate` ≠ 0 | event | `play_pause` → `deck.play` | Dead Stop, openers, bar-clock anchor |
| transport | cue press / hold | edge + hold | Note; not on StageLinQ/Serato | event | `cue` → `deck.cue` | Cue Stutter |
| transport | sync / master / keylock / slip / reverse / quantize / vinyl mode | bool | Note; StageLinQ `SyncMode`, `DeckIsMaster`, `KeyLock`, `SlipModeActive` | event | `sync`, `master`, `key_lock`, `slip`, `reverse`, `quantize`, `jog_mode` → `deck.*` | Nudge context, Slip Roll, flavour callouts |
| jog | platter touch | edge | Note; StageLinQ `ExternalScratchWheelTouch`; HID bit | event | `jog_touch` → `jog.touch` | gates every jog move |
| jog | platter rotation | rel | Pioneer CC 0x40 ± n (|n| ≤ 63), one message per USB poll (≤ 1 kHz); S4 MK3 HID absolute 0..2879 + µs timer; **absent** on Link, StageLinQ, Serato | ≤ 1 kHz while moving | `jog_turn` → `jog.rotate` (+ host gestures `jog.backspin/scratch/brake`) | Backspin, Scratch, Vinyl Brake |
| jog | ring / bend rotation | rel | separate CC, same encoding | same | `jog_ring` → `jog.bend` | Nudge |
| jog | search (shift+jog), needle strip | rel / uni | CC | event | `needle_search` → `jog.search` | none (ignore) |
| tempo | slider | bi | Pioneer 14-bit (CC 0/32) incl. FLX4/XZ/AZ; HID 12-bit; StageLinQ `Speed` float; Link BPM | per step | `tempo` → `tempo.slider` | Gear Change refinement |
| tempo | range / reset / bend buttons | enum / edge | Note | event | `tempo_range`, `tempo_reset` → `tempo.range`, `tempo.bend` | Nudge |
| channel mixer | fader | uni | **7-bit** on DJM, XDJ, DDJ-1000/400/FLX4, Prime; 14-bit on FLX10 only; float on StageLinQ `/Mixer/CHnfaderPosition`, Serato `Upfader`, Link mixer status | per step | `channel_fader` → `fader.channel` | Quick Cut, Slam, Transformer, blends, openers |
| channel mixer | trim | uni | 7-bit (14 on FLX10); MIDI only | per step | `trim` → `trim` | Trim Boost |
| channel mixer | EQ hi / mid / low (+ 4-band / isolator on V10) | bi | 7-bit centred 64 (14 on FLX10); **MIDI only**, absent on Link, StageLinQ, Serato | per step | `eq_high/mid/low` → `eq.high/mid/low` (+ `eq.lowmid`, `iso.*`) | Bassline Swap, Vocal Swap, Full Kill, Sweep, Duck |
| channel mixer | colour/filter knob + type | bi + enum | 7-bit centred; MIDI only; unmapped on FLX10 today | per step | `filter` → `filter`, new `colorfx.type` | Riser, Dive, Wobble |
| channel mixer | PFL, crossfader assign, send | bool / enum / uni | Note or CC; StageLinQ `PFL`, `ChannelAssignment` | event | → `pfl`, `xf.assign`, `send` | Crossfader context |
| channel mixer | on-air | bool | native on Pro DJ Link; derived elsewhere | derived | `isOnAir` | Harmonic Mix trigger |
| channel mixer | level meter | uni | XDJ-RX3 list row "CH LEVEL METER CC 2" (direction unverified) | continuous | new `level` | audio-reactive fallback |
| global mixer | crossfader | bi | 7-bit (14 FLX10); float on StageLinQ, Serato (0..1 uncentred), Link | per step | `crossfader` → `fader.cross` | Crossfader Slam, Crab |
| global mixer | master / booth / mic / headphones | uni | 7-bit; MIDI only | per step | `master_volume`, `booth_volume`, `headphone_*` | none |
| FX | beat FX type / on / level / beats / assign | enum / bool / uni / rel | DJM, XDJ, DDJ via MIDI (one CC per type; beats as ±1..30 relative); absent elsewhere | event | `fx_select`, `fx_on`, `fx_wet_dry`, `fx_param` → `fx.select/toggle/level/beats/assign` | Echo Out, FX stabs |
| performance | hot cue 1–8 press / set / delete | edge | Note on a pad-mode channel; StageLinQ `HotCue%d` unverified; absent on Link/Serato | event | `hot_cue`, `hot_cue_mode`, `delete`, `memory` → `pad.press {mode:"hotcue"}` | Hot Cue Juggle, Cue Drum |
| performance | loop in / out / exit / active / size / half / double / roll | edge → bool / int | Note; StageLinQ geometry (`CurrentLoopIn/Out`, `SizeInBeats`, `LoopEnableState`); Serato `AutoLoopOn`, `ManualLoopOn`, `LoopRollOn`, `BeatLength`; Link loop status (CDJ-3000) | event | `loop_in/out/active`, `loop_half/double`, `beat_loop`, `slip_loop` → `loop.*` | Loop Roll, balance-state extension |
| performance | beat jump, slicer, sampler, pad FX, keyboard, key shift | edge / int | Note (pad-mode channel); StageLinQ `BeatJumpIndex`; Serato slicer flag | event | `beat_jump_fwd/rev`, `key_shift_*` → `beatjump`, `pad.press {mode}` | Beat Jump, pad moves |
| performance | stems / parts (vocal, drums, inst; mute/solo) | bool per part | pad Notes on FLX6-GT / FLX10 (deck Notes 13/14/15) / XDJ-AZ / OPUS; audio state not reported back | event | new `stems.toggle` | Stem Drop, Acapella Swap |
| deck/track | load / eject | edge | Note; StageLinQ `SongLoaded`; Serato `Song/Valid`; Link | event | `eject` → `deck.load/eject` | round boundaries |
| deck/track | position / remaining | time | StageLinQ `PlayheadPosition` (ms cadence, unsubscribed by NP3 today); Serato `Playhead` seconds; Link absolute position; djay DB 2 s; **none** on MIDI | ms–s | new `track.position` | end-of-track, phase fallback |
| deck/track | beat phase / bar / phrase | float / int | StageLinQ BeatInfo ≈ 28 Hz; Pro DJ Link beat packets per beat (+ phrase on CDJ-3000); OS2L per beat; **none** on MIDI/Serato | 28 Hz / per beat | new `beat.tick` | On the One, phrase drops, every bar window |
| deck/track | bpm / key / duration | float / string / time | StageLinQ live; Link live; Serato pitch-adjusted bpm; otherwise from `np:track` | event | → `track.*` | Harmonic Mix, Energy Boost, Gear Change |

Resolution notes that change thresholds: a 7-bit fader cannot separate a 2 % crack from noise, so
hysteresis bands must be ≥ 2 steps; 14-bit pairs arrive MSB then LSB and must be paired by
(channel, cc, cc+32) before publishing or they saw-tooth; Pioneer jog velocity is the **delta value**,
not the message count, because the rate is pinned by USB polling.

## C. Per-rig matrix

Sources: `research_notes/prodjlink_data_model.md` §7 and `research_notes/hardware_ecosystems.md` §5.
"Today" = what reaches a theme through NP3 now. "With NP3 work" = reachable once Triode maps or
decodes it (no new hardware). "Never" = not on any wire NP3 can read without a new bridge.

| Rig | Data paths | Today | With NP3 work | Never (without a new bridge) | Beat phase · position | Moves that drop out |
|---|---|---|---|---|---|---|
| DDJ-FLX4 / FLX6 (+ rekordbox) | USB MIDI (7-bit mixer, 14-bit tempo, relative jog, pads on per-mode channels) + rekordbox history | fader, EQ, trim, play, cue, sync, jog touch | jog rotation, pads, loops, FX, colour knob, stems pads (FLX6-GT) | position, beat phase, loop geometry, hot-cue *existence* | none · none | On the One; 7-bit faders make fine fader tricks noisy |
| DDJ-FLX10 (+ rekordbox) | as above with 14-bit faders/EQ/trim, stem Notes 13/14/15, COLOR knobs ch7 | same (measured) | same list; filter needs the ch7 mapping | same | none · none | On the One, Riser until filter is mapped |
| DDJ-1000 / REV7 (+ rekordbox or Serato) | USB MIDI 7-bit | same core set | jog scratch + bend, loops, pads | same | none · none (REV7 motorised platter format unverified) | as FLX4 |
| XDJ-RX3 standalone | USB MIDI only if the unit emits it standalone; **no Link to PC**; NP3 guide says unsupported | nothing (no track identity either: media plays from USB stick, so no `np:track`) | mixer section, transport, jog, FX if NP3 accepts the device | position, phase, track identity | none · none | everything until NP3 supports it; even then no track card |
| XDJ-XZ / XDJ-AZ standalone | Pro DJ Link (track, play, BPM, beat, on-air) + USB MIDI mixer section (XZ "Mixer MIDI Message: SEND" default); deck-section MIDI standalone unverified | track, on-air, play state | EQ/filter/FX via mixer MIDI; beat tick from Link `28`; stems pads (AZ) | jog rotation unless deck MIDI emits standalone | Link beat · Link (no `0b` on XZ) | Backspin/Scratch unless deck MIDI confirmed |
| OPUS-QUAD standalone | USB MIDI + rekordbox DB (NP3 guide: supported); no `0b` position packets | core MIDI set per NP3 map (118/151 speculative) | pads, FX, jog if emitted standalone (unverified) | position | none · none | On the One |
| **CDJ-3000 ×2 + DJM-V10** | Pro DJ Link (CDJ status 200 ms, beat `28` per beat, **absolute position `0b` every 30 ms**, on-air per channel 6-ch); DJM-V10 **USB MIDI after pressing MIDI ON** (7-bit, 6 ch, 4-band EQ incl. LOW-MID, per-channel filter CC 20–25, isolator, sends, Beat FX type/on/level/beats/channel, TIME 14-bit, MIDI clock F8) | track, play state, on-air boolean, BPM, pitch (NP3's library decodes a subset; ignores `28`, `29`, loop/key fields) | **deck side: derivable** from `0b` velocity + undecoded status fields: backspin, scratch, brake, reverse, nudge, hot-cue hits (position jump to a known cue), beat jump, loops, slip-roll, key shift; `beat.tick` from `28`; **mixer side only via V10 MIDI**: faders, EQ, filter, crossfader, FX | stems; hot-cue *button id* (only the jump is visible); anything mixer-side if MIDI ON is off | Link `28` + `0b` · `0b` 30 ms | Stem Drop; mixer moves when MIDI is off; Cue Drum (which pad) |
| CDJ-3000 ×2 + DJM-A9 (NP3 "Bridge mode" = alphatheta-connect Stagehand unicast) | as above, plus `0x39` mixer unicast ~4 Hz 8-bit (trim, EQ hi/mid/low, colour, fader, xf assign, crossfader) and `0x58` VU ~30 Hz; A9 USB MIDI also available | NP3 already drives on-air from real faders here | faders/EQ/colour at 4 Hz without MIDI ON; FX only via MIDI | stems | Link · `0b` | 4 Hz is too slow for Transformer/Crab; otherwise full set |
| CDJ-3000 + DJM-900NXS2 | Link as above; NXS2 USB MIDI after MIDI ON (7-bit; list unverified online) | same Link subset | mixer via MIDI | stems | Link · `0b` | as V10 |
| Denon SC6000 + X1850 / Prime 4 / Prime GO (Engine OS) | StageLinQ StateMap (play, PlayState, sync, master, Speed, key, loop geometry, faders, crossfader, assignment, PFL) + BeatInfo ≈ 28 Hz; position states exist but NP3 unsubscribes them; X1850 MIDI map empty | track, play, BPM, key, faders, crossfader, sync | position, loop geometry, beat phase at 28 Hz, beat jump index, jog touch | **EQ, filter, trim, FX, jog rotation, pad presses** (not published by Engine OS; X1850 EQ stays local) | BeatInfo 28 Hz · StateMap ms | Bassline Swap, Full Kill, Riser, Backspin, Scratch, Cue Drum: the EQ/jog/pad family is gone unless the X1850 is read over MIDI with a map that does not exist yet |
| Serato + Rane Seventy-Two / Twelve (HID) | Serato history + Serato Remote OSC (playhead s, playRate, bpm, loop flags, Upfader, Crossfader 0..1); NP3 help says file-only, code suggests OSC is coming | track | position, play, loops, software faders, crossfader | EQ, jog, pads, FX (HID is invisible to a MIDI bridge; Seventy-Two map empty) | none · OSC playhead | EQ/jog/pad family |
| Serato + DDJ-REV5/REV7/FLX10 or DJM-S11 | OSC as above + controller USB MIDI | MIDI core set | full MIDI groups + OSC position/loops | none significant | none · OSC | On the One (no phase) |
| Traktor Pro + Kontrol S4 MK3 / S8 / D2 / Z2 | Traktor broadcast metadata only; hardware is **HID**, no MIDI mode ever shipped for S4 MK3 | track, BPM, duration | only via a user-installed Controller Manager MIDI-out TSI to an IAC bus (7-bit, change-driven, needs an NP3 "Traktor virtual device" map) | everything else, unless someone writes an HID bridge | none · none | all gesture moves; track moves only |
| VirtualDJ / djay / DJUCED / Mixxx + any MIDI controller | history/DB/text (+ VDJ Network Control 1 s, djay position 2 s) + controller MIDI | controller core set, track | controller full MIDI groups; VDJ OS2L per-beat phase | software-side loops/phase (except OS2L) | OS2L per beat (VDJ) · djay 2 s | On the One except VDJ with OS2L |

Reading the matrix: the **universal** signals are play state, which channel is loud, BPM and track
change. **Controller-class** signals (button edges, 7-bit knobs, relative jog) exist only over MIDI.
**Player-class** signals (position, beat phase, loop geometry, key) exist only over Pro DJ Link and
StageLinQ. A CDJ rig and a controller rig therefore have **complementary** strengths: the controller
sees the hands, the player sees the music. The move table in `02` must be gated per channel by the
capability set, and the HUD should tell viewers which move list is live.

Specific gaps to hand Triode (also in `03`): alphatheta-connect ignores beat packets `28` and mixer
status `29`, decodes only part of the CDJ status (no P_2/P_3, loop, key-shift fields), and reads the
`0b` BPM field at offset 0x30 ÷ 6400 where dysentery and beat-link document 0x38 ÷ 100 (its unit test
is self-consistent rather than hardware-derived; verify on a CDJ-3000). The DJM-V10 MIDI map in NP3
has seven speculative entries although the official list is public and complete. StageLinQ position
states are unsubscribed. The X1850 and Seventy-Two MIDI maps are empty.

## D. Capability model (proposal, merged into `03` §1b)

The host announces what the connected rig can report, on connect, on device change, and on request.
Condensed shape (full example with every field in `research_notes/hardware_ecosystems.md` §4.2):

```jsonc
{ "type": "np:capabilities", "protocol": 1, "generatedAt": "…",
  "sources": [ { "id": "midi:ddj-flx10", "kind": "midi", "latencyMs": 45, "maxRateHz": 1000, "mapConfidence": "verified" },
               { "id": "prodjlink", "kind": "prodjlink", "services": ["status","beat","position","onair"] } ],
  "global":   { "crossfader": { "type": "bi", "bits": 14, "source": "midi:ddj-flx10" }, "beatFx": { "present": true }, "masterClock": { "present": false } },
  "channels": [ { "ch": 1, "deck": "1", "device": "DDJ-FLX10", "software": "rekordbox",
      "transport":   { "play": "edge", "cue": "edge+hold", "sync": "edge", "keyLock": "bool", "slip": "bool" },
      "jog":         { "touch": true, "platter": "rel", "ring": "rel", "deltaBits": 7 },
      "tempo":       { "slider": "bi", "bits": 14 },
      "mixer":       { "fader": { "type": "uni", "bits": 14 }, "trim": { "bits": 14 }, "eq": "3band", "filter": false, "pfl": true },
      "performance": { "hotCues": 8, "loop": ["in","out","exit","half","double","roll"], "beatJump": true, "stems": ["vocal","drums","inst"] },
      "deck":        { "position": "none", "beatPhase": "none", "bpm": "track", "key": "track", "loopState": "button-only" },
      "sources":     ["midi:ddj-flx10", "history:rekordbox"] } ],
  "rates":    { "continuous": "hold@10Hz" | "coalesced@30Hz" | "unthrottled", "events": "unthrottled" },
  "timestamps": "state" | "perEvent",
  "unsupported": [ { "device": "Traktor Kontrol S4 MK3", "reason": "hid-only" } ] }
```

Enum rules: `edge` = press and release timestamped; `bool` = latched only (a tap cannot be timed);
`rel` = signed deltas; `none` = absent; `bits` = native resolution (sets hysteresis); `beatPhase` ∈
`beatinfo | prodjlink | os2l | link | grid | none`; `position` ∈ `stagelinq | serato | prodjlink | djay-db | none`.
Companions: `np:capabilities:changed` (diff) and a theme request `np:capabilities:get`.

Gating a theme derives from it: fader cut needs `mixer.fader`; EQ kill needs `mixer.eq ≠ none`;
backspin needs `jog.platter == "rel"` **or** `deck.position` at ≥ 20 Hz (CDJ-3000 `0b`); cue juggle
needs `performance.hotCues ≥ 4` with `transport.cue == "edge+hold"` or position jumps to known cues;
On the One needs `deck.beatPhase ≠ none`; stems needs `performance.stems` non-empty. The HUD shows the
rig name and its live move list, and says why a move is off ("EQ moves off: SC6000 does not publish
EQ over StageLinQ; connect the X1850 by USB and enable MIDI").
