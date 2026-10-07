# PRO DJ LINK data model for gesture detection (CDJ-3000 + DJM-V10 / A9 / 900NXS2 / XDJ-AZ / Opus Quad)

Research note for the DJ Street Fighter overlay. Written 2026-10-06 from the actual packet
analyses and source code, not from memory:

- **dysentery** (Deep Symmetry, the canonical Pro DJ Link analysis), repo HEAD f62a24b (2026-08-02), rendered at
  https://djl-analysis.deepsymmetry.org/djl-analysis/ . Pages cited below by their rendered URL
  (`packets.html`, `beats.html`, `vcdj.html`, `mixer_integration.html`, `sync.html`, `stagehand.html`, `startup.html`,
  `track_metadata.html`, `touch_audio.html`).
- **alphatheta-connect** (chrisle / Triode, "used as part of Now Playing"), v0.28.5, repo HEAD 7496991 (2026-10-04),
  https://github.com/chrisle/alphatheta-connect . Files cited as `src/...` / `docs/...`.
- **beat-link** (Deep Symmetry, Java), https://github.com/Deep-Symmetry/beat-link — used as a second decoder to cross-check offsets.
- AlphaTheta MIDI message lists for DJM-V10 and DJM-A9 (PDFs, see §5), NP3 help/changelog pages (see §4.5 and §6).

Anything marked **[unverified]** could not be confirmed from a primary source. Offsets are hex, values decimal unless marked.

---

## 1. Transport basics

**Framing.** Every packet starts with the 10-byte magic `51 73 70 74 31 57 6d 4a 4f 4c` ("Qspt1WmJOL"), then a type byte at
`0x0a`, a 20-byte device name, then a structure/subtype byte and a device number `D` and a length field. Which struct variant
applies depends on the type (dysentery `packets.html#packet-types`).

**Ports and packet families** (dysentery `packets.html`):

| UDP port | Type | Meaning |
|---|---|---|
| 50000 | `0a` `00` `02` `04` `06` `08` `01/03/05` | Announce, three-stage channel claim, keep-alive (`06`), channel conflict, mixer-assignment packets |
| 50001 | `02` | Fader Start command (mixer → players) |
| 50001 | `03` | Channels On Air (mixer → players, broadcast) |
| 50001 | `0b` | **Absolute Position** (CDJ-3000+, every 30 ms) |
| 50001 | `26` / `27` | Tempo-master handoff request / response |
| 50001 | `28` | **Beat** (one per beat) |
| 50001 | `2a` | Sync control (set sync on/off, become master) |
| 50002 | `05` / `06` | Media slot query / response |
| 50002 | `0a` | **CDJ Status** |
| 50002 | `19` / `1a` | Load Track command / ack |
| 50002 | `29` | **Mixer Status** |
| 50002 | `34` | Load Settings command |
| 50004 | `1e` `1f` `20` | Touch Audio data / handover / timing (CDJ-3000 → DJM-900NXS2/V10/A9) |
| TCP 12523 → 1051 | dbserver | Metadata / beat grid / cue list / waveform queries (`track_metadata.html`); port discovered via 12523, has always been 1051 |
| NFS (RPC/portmap) | — | Players export their USB/SD; alphatheta-connect reads `export.pdb` / OneLibrary, ANLZ `.DAT/.EXT/.2EX`, artwork over NFS instead of (or in addition to) dbserver |

**You must pose as a device to get the good stuff.** Status packets (`0a`, `29`) are unicast to devices the players know about.
A "virtual CDJ" binds 50002 and sends CDJ keep-alives to the 50000 broadcast address (`vcdj.html#creating-vcdj`). Beat (`28`),
on-air (`03`), absolute position (`0b`) and fader-start (`02`) are broadcast, so passive pcap capture sees them without joining.
CDJ-3000s need the CDJ-3000-flavoured keep-alive (byte `0x35` = `0x64`), otherwise players set to 5/6 "repeatedly kick
themselves off the network" (`startup.html#startup-3000`).

**Update rates (measured numbers from the analyses):**

| Stream | Rate | Source |
|---|---|---|
| CDJ keep-alive `06` | ~2.0 s, "held tightly" (median 2.0026 s over 78 consecutive packets) | `startup.html#cdj-keep-alive` |
| Mixer keep-alive `06` | ~1.5 s (DJM-A9 observed at ~2 s) | `startup.html#mixer-keep-alive`, `stagehand.html#a9-paired-keepalive` |
| CDJ status `0a` | "roughly every 200 ms, except when using the jog wheel: newer players might send them more frequently during such changes" | `vcdj.html#cdj-status-packets` |
| Mixer status `29` | same ~200 ms ("Each device seems to send status packets roughly every 200 milliseconds") | `vcdj.html#creating-vcdj` |
| Beat `28` | once per beat, only while playing a rekordbox-analysed track (CDJ-3000 can self-analyse); the mixer sends them continuously as a backup metronome | `beats.html#beat-packets` |
| Absolute position `0b` | every 30 ms while a track is loaded, **even when paused** | `beats.html#absolute-position-packets` |
| On-air `03` | not quantified in dysentery **[unverified]**; NP3 changelog says a deck goes on-air "the moment the mixer opens its channel", so it is event-driven or fast | `mixer_integration.html#channels-on-air` |
| Touch-audio timing `20` | every 7 ms from mixer to each touch-capable player | `touch_audio.html` |
| Stagehand unicast (A9 → iPad) | `39` mixer state ~4 Hz, `58` VU ~30 Hz, `6a` ~3.4 Hz, `3b` ~0.24 Hz; total ~38 pkt/s | `stagehand.html#a9-unicast-channel` |
| Stagehand unicast (CDJ-3000 → iPad) | `0b` ~30 Hz, `28` per beat, `20` on 50004 at exactly 142.857 Hz (7.000 ms) | `stagehand.html#cdj-unicast-channel` |

alphatheta-connect's `docs/ABSOLUTE_POSITION.md` summarises the same: position ~30 ms (33 Hz), status ~100–200 ms (5–10 Hz),
beats variable with BPM.

---

## 2. CDJ status packet (`0a`, port 50002) — every known field

Packet lengths: `d0` (pre-nexus), `d4` (nexus), `11c`/`124` (nxs2 / newer firmware), `11b` (XDJ-1000), **`0x200` (512 bytes) on
CDJ-3000**. Subtype byte at `0x20` is `03`–`06` ("may indicate protocol version"). Full source: `vcdj.html#cdj-status-packets`.

| Offset | Label | Meaning (dysentery) |
|---|---|---|
| `21`, `24` | D | Player number |
| `27` | A | Activity: `00` idle, `01` playing / searching / loading |
| `28` | D_r | Device the track was loaded from (`00` = none) |
| `29` | S_r | Slot: `00` none, `01` CD, `02` SD, `03` USB, `04` rekordbox, `06` Streaming Direct Play, `07` USB2 (XDJ-AZ 4-deck), `09` Beatport LINK, `05/08` unknown streaming |
| `2a` | T_r | Track type: `00` none, `01` rekordbox, `02` unanalysed, `05` audio CD, `06` streaming |
| `2c`–`2f` | rekordbox | Track ID (rekordbox id, or player-internal id for streaming/unanalysed) |
| `32`–`33` | Track | Track number in the list it was loaded from |
| `35` | t_srt | Sort mode in effect when loaded |
| `37` | t_src | Menu the track was loaded from (`05` playlist, `12` search, `16` history, `32` instant double / previous track …) |
| `38`–`3f` | t_cat1/2 | Menu-path IDs (artist/album, BPM/range, …) |
| `46`–`47` | d_n | Count of tracks in the playlist/menu/disc |
| `58` | ld_1 | `80` briefly on load (nxs2/XDJ-1000 only, **not CDJ-3000**) |
| `5a`–`5b` | u_c1 | **`ffff` for one packet when a hot cue or memory cue is added or deleted** |
| `5e`–`5f` | u_t | Tag-list update trigger (`00ff`, `ff00`, back to `0000`) |
| `66`–`67` | ld_2 | `ffff` for one packet when load finishes (nxs2/XDJ-1000 only) |
| `6a`, `6b` | U_a, S_a | USB / SD activity (alternates `04`/`06`) |
| `6f`, `73` | U_l, S_l | USB / SD local state: `04` empty, `00` loaded, `02`/`03` unmounting |
| `75` | L | Link media available anywhere on network |
| `7b` | **P_1** | Play mode: `00` no track, `02` loading, `03` playing, `04` **looping**, `05` paused, `06` cued (paused at cue), `07` cue play (cue held), `08` **cue scratch**, `09` searching fwd/back, `0e` CD spun down, `11` reached end, `12` emergency loop |
| `7c`–`7f` | Firmware | ASCII firmware version |
| `84`–`87` | Sync_n | Sync counter used in master handoff |
| `89` | **F** | Flags: bit6 Play, bit5 Master, bit4 Sync, bit3 **On-Air**, bit1 **BPM-sync** (synced but pitch-bent / jog-nudged so no longer beat-aligned). alphatheta-connect adds, from CDJ-3000 FW3.20 disassembly: bit0 never set; bit2 a real beat-sync boolean, normally 0; bit7 "sync-master active / handoff in progress", normally 0 (`src/status/types.ts`) |
| `8b` | **P_2** | Second play-state byte: `7a` playing / `7e` stopped (pre-nexus `6a/6e`, nxs2 `fa/fe`, XDJ-XZ `9a/9e`). **When the DJ holds the platter, P_1 stays `03` (playing) but P_2 says stopped** — this is the closest thing to a "jog touch while playing" flag |
| `8c`–`8f` | Pitch_1 | **Effective pitch** (what the BPM display shows; fader or synced master); `0x100000` = 0 %, `0` = −100 %, `0x200000` = +100 % |
| `90`–`91` | M_v | `8000` rekordbox track loaded (tempo is "meaningful" as master), `0000` non-rekordbox, `7fff` empty |
| `92`–`93` | **BPM** | Track BPM at current position × 100 (`ffff` = none); variable-BPM tracks change it over time |
| `94`–`97` | M_slip, BPM_slip | Same as M_v/BPM but for the *slipping* underlying position — **only on XDJ-1000 / nxs2** per dysentery; CDJ-3000 behaviour **[unverified]** |
| `98`–`9b` | Pitch_2 | Local pitch fader position, but **follows the brake/release ramp**: on stop it "drops over time, reflecting the gradual slowdown … controlled by the player's brake speed setting"; on start both Pitch_2 and Pitch_4 "gradually rise … at a speed controlled by the player's release speed setting" |
| `9d` | **P_3** | `00` none, `01` **paused or playing in Reverse**, `09` playing forward, jog in **Vinyl** mode, `0b` **slipping**, `0d` playing forward, jog in **CDJ** mode |
| `9e` | M_m | Master meaningful: `00` not master, `01` master with rekordbox track, `02` master but can't send tempo |
| `9f` | M_h | Master handoff target (`ff` normally) |
| `a0`–`a3` | **Beat** | Beat counter from 1 to end of track (`0` when paused at start, `ffffffff` without a beat grid) |
| `a4`–`a5` | **Cue** | Countdown in beats to the **next memory cue** (`01ff` = none within 64 bars; `0100` = 64 bars; `0000` on the cue beat). It is *memory* cues, not hot cues |
| `a6` | **B_b** | Beat within bar 1–4 (`0` without a grid) |
| `b3` | u_g | `ff` for one packet when the beat grid is edited |
| `b7` | M_p | CDJ-3000 local media presence bits (bit1 USB, bit0 SD) |
| `b8`, `b9` | U_e, S_e | Unsafe-eject flags |
| `ba` | el | Emergency loop / emergency mode active |
| `c0`–`c3`, `c4`–`c7` | Pitch_3, Pitch_4 | Pitch_3 ≈ Pitch_1 (effective); Pitch_4 = fader but **drops to `000000` instantly** on stop / platter hold |
| `c8`–`cb` | Packet | Packet counter — **fixed at 0 on CDJ-3000** (its live counter moved to the 50004 stream) |
| `cc` | nx | Capability byte: `05` old, `0f` nexus, `1f` CDJ-3000 / XDJ-XZ |
| `cd` | t | bit5 = supports Touch Audio |
| `d0`–`ef`, `ff`–`10f` | Settings blocks | Start `12 34 56 78`. Block 1 byte `0a`: **waveform colour** (`01` Blue, `03` RGB, `04` 3-Band); byte `0d`: waveform position (`01` centre, `02` left). CDJ-3000 has two blocks, nothing decoded in block 2 |
| `110`–`112` | edit_menu | (labelled in the diagram, undocumented) |
| `113` | P_4 | "another playback state bit mask, details not yet figured out" |
| `116`–`117` | T_b | Time steps in the current bar (high-res phase meter) — **only sent while paused and tempo master, or in sub-beat loops**; zero during normal play |
| `11a`–`11b` | T_pos | Position within the bar relative to T_b (same conditions) — jog nudges while paused move it |
| `11c` | n_mc | Index of the next memory point (`0a` before first, `0b` second …, `00` none ahead). "The presence of hot cues does not affect this value at all" |
| `11d`, `11e`, `11f` | Buf_f, Buf_b, Buf_s | RAM buffer ahead/behind playhead; `01` when whole track buffered |
| `120`–`123` | NeedleDragPos | Timestamp of the needle-search marker set by dragging the touchscreen waveform; zero when none / passed |
| `158` | M_t | **Master Tempo** on/off |
| `15c`–`15e` | **Key** | Current key *after* master-tempo/slider but *before* key shift: note 0–11 (Am…Abm / C…B), `15d` minor/major, `15e` accidental (`00/01/ff`); `64` when MT off and slider moved outside the original key |
| `164`–`16b` | **KeyShift** | int64, cents; ±100 per semitone (CDJ-3000 key shift / key sync) |
| `1b6`–`1b9` | **Loop_s** | Loop start, non-zero only while a loop is actively playing (stored or dynamic); ms = value × 65536 / 1000 |
| `1be`–`1c1` | **Loop_e** | Loop end, same encoding |
| `1c8`–`1c9` | **Loop_b** | Loop length in whole beats (0 / meaningless for sub-beat loops) |

beat-link (`CdjStatus.java`) decodes the same offsets: `0x7b` P1, `0x8b` P2, `0x9d` P3, `0x8d` pitch (3 bytes), `0x92` BPM,
`0xa0` beat, `0xa4` cue countdown, `0xa6` beat-in-bar, `0x1b6`/`0x1be`/`0x1c8` loop fields (gated on packet length ≥ `0x1ca`),
and derives `isPlayingBackwards() = P1==PLAYING && P3==PAUSED_OR_REVERSE`, `isPlayingVinylMode() = P3==0x09`.

### 2.1 What is **not** in the status packet (important for the overlay)

- **No jog touch flag and no jog rotation / velocity / direction.** The only platter evidence is indirect: P_1=`03` with P_2 "stopped"
  (platter held while playing), P_1=`08` (cue scratch), P_3=`01` (reverse), bit1 of F (BPM-sync, i.e. a nudge happened while synced),
  Pitch_1 wobbling while Pitch_2/4 don't (pitch bend), and — the real signal — the 30 ms absolute-position stream (§3.2).
  T_b/T_pos exist but only while paused-as-master.
- **No hot-cue press events and no hot-cue set/unset bitmap.** `u_c1` flashes `ffff` once when a hot or memory cue is *added or deleted*,
  nothing fires on a *press*. Which hot cues exist must come from dbserver `GetCueAndLoops` / `GetAdvCueAndLoops` or the ANLZ files
  over NFS (alphatheta-connect `getTrackAnalysis()`). A hot-cue press is only visible as a position jump (status `Beat` / `0b` playhead).
- **No beat-jump event** — visible only as a position discontinuity (beat counter jumps by ±N while playing).
- **No loop-roll / slip distinction** beyond P_3=`0b` (slipping) plus the loop fields; "which loop button" is not transmitted.
- **No pad / performance-mode state, no phrase.** Phrase data (PSSI) is in the `.EXT` ANLZ file; current phrase is derived by
  combining it with position.
- **No touch-screen, browse, or needle-drop events** beyond `NeedleDragPos` and the load-source fields.
- **No fader / EQ / crossfader** (those are mixer-side; see §4).
- CDJ-3000 does not increment the packet counter, so you cannot detect dropped status packets from `0xc8`.

---

## 3. Beat packets and absolute position

### 3.1 Beat (`28`, port 50001, 0x60 bytes) — `beats.html#beat-packets`

| Offset | Field | Notes |
|---|---|---|
| `21` | D | Player number (`21` for the mixer) |
| `22`–`23` | len_r | `003c` |
| `24`–`27` | nextBeat | ms until next beat |
| `28`–`2b` | 2ndBeat | ms until the beat after |
| `2c`–`2f` | nextBar | ms until next downbeat (1–4 beats away) |
| `30`–`33` | 4thBeat | |
| `34`–`37` | 2ndBar | 5–8 beats away |
| `38`–`3b` | 8thBeat | |
| `3c`–`53` | `ff` × 24 | |
| `54`–`57` | Pitch | same `0x100000` = 0 % encoding (mixer always +0 %) |
| `5a`–`5b` | BPM | × 100 |
| `5c` | B_b | beat within bar 1–4 |
| `5f` | D | duplicate |

Caveats straight from the analysis: the look-ahead times are **always computed at 0 % pitch** ("you will need to perform the
calculation to scale the beat timing values based on that adjustment yourself"), `0xffffffff` where the track ends first, and CDJs
emit beats **only while playing a track with a beat grid**. The mixer's own beat packets are a free-running metronome at the
master's BPM, "not synchronized with the master player" — use the beats from the player whose F byte has bit5 set.

**Is the arrival time good enough for `beat.tick` with phase?** The packet is emitted *at* the beat ("even the arrival of the packet
is interesting information, it means that the player is starting a new beat") over broadcast UDP on a wired segment, so arrival
latency is sub-millisecond-to-low-ms in practice; dysentery does not publish jitter figures **[unverified]**. Phase between
beats has to be interpolated from BPM × pitch; between packets you have status (200 ms) and, on CDJ-3000, the 30 ms position stream,
which is what Beat Link's `TimeFinder` uses. The CDJ-3000 Stagehand channel additionally carries a 7.000 ms timebase tick
(`stagehand.html#timing-stream`), but that is unicast to a Stagehand peer only.

### 3.2 Absolute position (`0b`, port 50001, CDJ-3000 and later) — `beats.html#absolute-position-packets`

Discovered by David Ng (nudge). "Absolute Position packets are only transmitted while a track is loaded on a player, but unlike
Beat packets, they are sent even while not playing. This packet is sent to all connected devices on port 50001 every 30
milliseconds, which is often enough to keep good tabs on what the player is up to, even when playing backwards, scratching,
looping, or needle jumping in between beats."

| Offset | Field | Encoding |
|---|---|---|
| `21` | D | player |
| `22`–`23` | len_r | |
| `24`–`27` | TrackLength | seconds, rounded down |
| `28`–`2b` | **Playhead** | milliseconds |
| `2c`–`2f` | Pitch | int32 signed, slider % × 100 (3.26 % → `0146` = 326) |
| `30`–`37` | zeros | |
| `38`–`3b` | BPM | effective (displayed) BPM × 10; `ffffffff` unknown |

beat-link `PrecisePosition.java` reads exactly this: position `0x28`, pitch `0x2c` (signed, /100), **BPM at `0x38`**.

**Discrepancy to be aware of:** alphatheta-connect `src/status/utils.ts::positionFromPacket` reads BPM at **`0x30`** and divides the
raw pitch by **6400** ("pitch × 64 × 100"), and its unit test (`tests/status/position.spec.ts`) writes the BPM at `0x30` as well, so
the test is self-consistent rather than hardware-derived. dysentery and beat-link both say `0x38` and ÷100. If NP3 position events
ever show `bpm: null`/0 or a 64× too-small pitch from a real CDJ-3000, this is why **[unverified against a capture]**. The `playhead`
field is at the same offset in all three, so position itself is safe.

Only CDJ-3000 / 3000X emit `0b`. Not CDJ-2000NXS2, not XDJ-XZ, not rekordbox (`docs/ABSOLUTE_POSITION.md` table); Opus Quad
"does not send high-precision position packets like the CDJ-3000 does" (kyleawayan analysis, §6.4). Also note the *unicast*
68-byte `0b` the CDJ-3000 sends to a Stagehand peer is a different, multiplexed telemetry packet, not the playhead
(`stagehand.html#cdj-0b-multiplex`).

**Derivations this enables (30 ms cadence, ~33 samples/s):** playhead velocity = Δplayhead/Δt; forward at pitch → normal play;
velocity ≈ 0 while P_1 says playing → platter held; strongly negative velocity → **backspin / reverse**; rapid sign changes →
**scratch**; velocity decaying smoothly to 0 while Pitch_2 ramps down → **vinyl brake**; jump of exactly N beats of the grid →
**beat jump** or **hot cue**; position wrapping between two points → **loop** (confirmed by Loop_s/Loop_e); velocity briefly
> pitch then back → **pitch nudge / jog bend** (also F bit1 if synced).

---

## 4. Mixer side

### 4.1 Mixer status (`29`, port 50002, 0x38 bytes) — `vcdj.html#mixer-status-packets`

`21`/`24` D (`21` = 33 for a mixer; rekordbox uses `11`, rekordbox mobile `29`); `27` F (`f0` tempo master, `d0` not — "the mixer
always considers itself to be playing and synced, but never on-air"); `28`–`2b` Pitch (always `100000`); `2e`–`2f` BPM × 100;
`36` M_h; `37` B_b. Two big caveats: the BPM "seems to only be valid when a rekordbox-analyzed source is playing; when the mixer is
doing its own beat detection from unanalyzed audio sources … it does not send that value", and the beat-in-bar "is not synchronized
with the master player, and these packets do not arrive at the same time as the beat started anyway, so this value is not useful
for much." **Nothing about faders, EQ, FX or crossfader is in this packet.**

### 4.2 Channels On Air (`03`, port 50001) — `mixer_integration.html#channels-on-air`

4-channel form: subtype `00`, len_r `0009`, flags F1–F4 at `24`–`27`, five zero bytes. **6-channel form (DJM-V10 + CDJ-3000s):**
subtype `03`, len_r `0011`, F1–F4 at `24`–`27`, F5–F6 at **`2e`–`2f`**, then `30 00 00 00 00 00` (captures by @AhnHEL).

**Definition of on-air** (verbatim): "A flag value of `00` tells the corresponding player it is off the air (silenced, due to the
cross fader, channel fader, trim, filters, or input source switch for that channel, or the master level for the entire mix), while
`01` means the player's channel is on the air." So the DJM already folds channel fader, crossfader cut, trim, filter and master
into one boolean per channel. It drives the red platter ring (nexus) / a small screen indicator (XDJ-XZ). If no DJM is present
anyone can broadcast it; a real DJM "will quickly reassert its own on-air state." It is a per-channel boolean — the fader
*position* is not transmitted. beat-link also tracks on-air from the XDJ-AZ (`BeatFinder.java`, `lastSeenXdjAzChannelsOnAir`).

### 4.3 Fader Start (`02`, port 50001) — `mixer_integration.html#fader-start`

Mixer → players (or broadcast): C1–C4 at `24`–`27`, `00` = start (if at cue), `01` = stop and return to cue, `02` = no change. In
principle a fader-open / crossfader-open edge for channels with Fader Start enabled. **But:** "The XDJ-XZ does not support fader
start … Sadly, the newer CDJ-3000 does not support fader start either, it is starting to look like an abandoned feature." Whether a
DJM-V10/A9 still transmits `02` on a CDJ-3000 network is **[unverified]**; do not plan on it.

### 4.4 Fader / EQ / crossfader positions — only via the Stagehand unicast channel (DJM-A9 verified)

**Standard Pro DJ Link broadcasts carry no continuous mixer controls.** The one place they exist on the wire is the unicast push a
DJM-A9 sends to a Pioneer **Stagehand** peer (the iPad "PRO DJ LINK Manager" app, bundle `com.pioneerdj.nma`, for DJM-A9 +
CDJ-3000/3000X — https://www.pioneerdj.com/en/product/software-interfaces/stagehand/ ). dysentery's `stagehand.html` page was
written by Chris Le (Triode) from May-2026 MITM captures of a single A9 + CDJ-3000 + iPad rig.

**`0x39` mixer state, port 50002, 266 bytes, ~4 Hz, not change-triggered** (`stagehand.html#a9-mixer-state`). Per-channel 24-byte
blocks for CH1–4 at packet offsets 36 / 60 / 84 / 108:

| Block offset | Control | Encoding |
|---|---|---|
| +00 | input source selector (hypothesis) | per-channel codes |
| +01 | TRIM | `00`–`ff`, unity `80` |
| +03 | EQ HI | `00` cut, `80` unity, `ff` boost |
| +04 | EQ MID (or MID-HIGH on a 4-band V10, hypothesis) | same |
| +05 | centre-detented unknown — hypothesis: **MID-LOW band of a DJM-V10** | `80` baseline on the A9 |
| +06 | EQ LOW | same |
| +07 | **Color FX knob** | `00`–`ff`, centre `80` |
| +0b | **Channel fader** | `00` down – `ff` max, linear |
| +0c | Crossfader assign | `00` THRU, `01` A, `02` B |

Global: **crossfader position at packet offset `0xb4` (180)**, `00` A … `ff` B, centred ~`78`. The ~94-byte master/FX block from
`0xac` ("almost certainly encodes the master fader, booth knob, headphone level / CUE mix, BEAT FX type / depth / level, Color FX
selector, and MASTER EQ") is **undecoded**. The low byte of the length field also ticks on some control changes.

**`0x58` VU stream, port 50001, 584 bytes, ~30 Hz.** alphatheta-connect parses it as 15 stereo u16 frames per channel from offset
44, stride 60 (`vuFromPacket`); dysentery marks the semantics "hypothesis (strong)" because no capture with audio was made.
GitHub issue Deep-Symmetry/dysentery#78 (https://github.com/Deep-Symmetry/dysentery/issues/78) reports the `a5 38` prefix bytes
falsely trip clip indicators and that master/booth meter positions are unknown.

Resolution is 8-bit (0–255) at 4 Hz — fine for "fader open/closed/moving" and EQ kills, too slow for fader-flick transforms. The
layout is **A9-only**; alphatheta-connect refuses to apply it outside Stagehand mode: "the 0x39 layout is reverse-engineered from a
DJM-A9 and must not be applied to other mixers (e.g. XDJ-AZ) that were never captured" (`src/status/index.ts`, ticket NP3-327).
DJM-V10 over Stagehand is **[unverified]** (the V10 is not a Stagehand-supported mixer per Pioneer's product page, which lists
DJM-A9 + CDJ-3000/3000X only).

Stagehand also lets the peer *write* a few things (`0x07` transport play/pause/skip/seek, `0x6b` on-air-display and quantize
prefs), but alphatheta-connect's own real-hardware notes (`docs/STAGEHAND.md` §6, CDJ-3000 FW 3.18) say the CDJ silently ignores
their transport commands and never opens the `0x69`/`0x0b` unicast streams to the emulated peer; the mixer push is what NP3 relies
on.

### 4.5 "Bridge mode" in NP3 vs. AlphaTheta's "PRO DJ LINK Bridge" — two different things

**NP3 Bridge mode = alphatheta-connect `connectMethod: 'stagehand'`.** Evidence: alphatheta-connect CHANGELOG v0.25.0 "feat: bridge
mode now unicasts keep-alives so the mixer and players push live state back"; NP3 changelog (https://nowplayingapp.com/help/changelog/ ):

- 3.0.0-beta.4496 (2026-08-30): "Pro DJ Link setups can run in Bridge mode (experimental): pick it as the operating mode and the
  DJM-A9's real channel faders drive on-air detection."
- 3.0.0-beta.4609 (2026-09-13): "Pro DJ Link Bridge mode keeps showing live CDJ-3000 track and position updates after the app reconnects."
- 3.0.0-beta.4622 (2026-09-18): "players 5 and 6 on a DJM-V10 or V10-LF can be wired to their own mixer channels … both the
  Stagehand bridge and the V10 MIDI maps now read channels 5 and 6."
- 3.0.0-beta.4554/4580 (2026-09-06/07): "With a DJM on your Pro DJ Link network, a track goes on-air the moment the mixer opens its channel."

NP3's mix-processor reference (https://nowplayingapp.com/help/reference/concepts/mix-processor/ ) lists channel fader from "MIDI,
StageLinQ, PRO DJ LINK", crossfader from "MIDI, StageLinQ", EQ from MIDI, on-air flag from "PRO DJ LINK + DJM mixer", and also
"jog touch detection, loop engagement status, tempo master detection" as inputs. The on-air guide
(https://nowplayingapp.com/help/guide/settings/on-air-detection/ ) says of DJM mixers: "Fader and crossfader values exposed via
PRO DJ LINK when connected to Rekordbox, or via MIDI. Supported models also expose the on-air flag directly." The XDJ-AZ fix in
beta.4473 ("Channel faders were read upside down") shows NP3 also reads faders from the XDJ-AZ's rekordbox-bound packets in passive
mode; that layout is not published anywhere I could find **[unverified]**. The public integration page
(https://nowplayingapp.com/help/reference/integrations/prodjlink/ ) only documents Active (virtual CDJ, binds 50000) and Passive
(libpcap/Npcap) modes and lists CDJ-2000NXS/NXS2/3000, XDJ-XZ, DJM-V10/900NXS2 and rekordbox.

**AlphaTheta "PRO DJ LINK Bridge"** is a different product: a free desktop app (v1.1.8, 2024-11-05; macOS/Windows) that joins the
Pro DJ Link network and **re-publishes it as TCNet** to licensed lighting/video software (Avolites, ChamSys MagicQ, Resolume Arena,
SoundSwitch, TC Supply ShowKontrol). Manual: "an application that allows you to synchronize real time information present on a PRO
DJ LINK network to external lighting, video, SFX applications and devices via a protocol called TCNet"
(https://assets.pioneerdjhub.com/PRO_DJ_LINK_Bridge_Instruction_Manual_EN.pdf ; newer v1.2 manual at
https://downloads.support.alphatheta.com/other/PRO_DJ_LINK_Bridge/PRO_DJ_LINK_BRIDGE_manual_v12_en.pdf ). Supported hardware per
https://www.pioneerdj.com/en-us/product/software/pro-dj-link-bridge/software/overview/ : CDJ-3000X, CDJ-3000, CDJ-1500X, DJM-V10/V10-LF,
DJM-A9 (legacy: CDJ-2000NXS2, CDJ/DJM-TOUR1, DJM-900NXS2 — https://support.alphatheta.com/en-US/articles/7292587209113 ). The
Sept-2026 SoundSwitch announcement (https://rekordbox.com/en/2026/09/rekordbox-for-mac-windows-and-pro-dj-link-bridge-support-soundswitch/ )
advertises "Integration with faders on compatible DJ equipment", so the TCNet feed evidently carries some fader/on-air state from
V10/A9 **[which fields, unverified]**. It is not something NP3 consumes; it is irrelevant to the overlay unless you want a TCNet client.

### 4.6 Mixers summarised

| Mixer | On-air `03` | Mixer status `29` | Fader/EQ over link | Touch audio | USB MIDI |
|---|---|---|---|---|---|
| DJM-V10 / V10-LF | yes, 6-channel variant | yes | not in broadcasts; Stagehand not supported by Pioneer **[unverified]** | yes | yes, 6 ch (§5.1) |
| DJM-A9 | yes (4 ch) | yes (model code `31`) | **yes via Stagehand `0x39`/`0x58` unicast** | yes | yes (§5.2) |
| DJM-900NXS2 | yes (4 ch) | yes | no | yes | yes (MIDI addendum exists; §5.3) |
| DJM-750MK2 | has Pro DJ Link? — the 750MK2 has no LINK port; it only offers USB MIDI **[unverified beyond spec sheets]** | — | — | — | yes |
| XDJ-AZ / XZ (built-in mixer, device 33) | yes (XDJ-AZ on-air seen by beat-link) | yes | AZ: faders readable from rekordbox-bound packets (NP3 passive) **[layout unverified]** | — | yes (controller MIDI) |

---

## 5. USB side

**General DJM behaviour** (AlphaTheta FAQ https://support.alphatheta.com/en-US/articles/4408487552153 , for the V10 but the
pattern is the same family-wide): "MIDI messages are sent when you use buttons or knobs on the DJM-V10. You can send MIDI clock
messages too. … The DJM-V10 does not support the input of MIDI signals." So: output-only, **sent on movement/press** (no periodic
snapshot — whether a snapshot is sent when MIDI is switched on is **[unverified]**), MIDI channel set in MY SETTINGS/UTILITY, a
MIDI ON button and a MIDI START/STOP button on the V10, MIDI clock `F8` follows the active channel's BPM (DIN and USB) — see
https://cdm.link/2024/01/pioneer-v10-midi . The DJM keeps mixing audio normally while sending MIDI, so this is a genuine passive
tap on a CDJ+DJM rig, readable by NP3's MIDI Bridge (which captures CC, Note On/Off and Pitch Bend —
https://nowplayingapp.com/help/reference/integrations/midi-bridge/ ; "V10 MIDI maps now read channels 5 and 6" per the changelog).

### 5.1 DJM-V10 MIDI message list (official PDF, addendum E1, 2020-02-04)

Source: https://downloads.support.alphatheta.com/manuals/DJM_V10_DJM_V10_MIDI_Message_List_E1_addendum.pdf (linked from
https://support.alphatheta.com/en-US/articles/4404659749145 ). `Bn` = CC on the configured channel, `9n` = note; **all continuous
controls are 7-bit (00–7F) except Beat FX TIME, which is 14-bit (CC `0D` MSB + CC `2D` LSB)**.

Per-channel CC numbers (hex):

| Control | CH1 | CH2 | CH3 | CH4 | CH5 | CH6 |
|---|---|---|---|---|---|---|
| TRIM | 01 | 06 | 0C | 50 | 60 | 77 |
| COMP | 46 | 47 | 48 | 49 | 4A | 4B |
| EQ HI | 02 | 07 | 0E | 51 | 30 | 38 |
| EQ HI-MID | 03 | 08 | 0F | 5C | 31 | 3C |
| EQ LOW-MID | 1C | 1D | 10 | 5D | 34 | 59 |
| EQ LOW | 04 | 09 | 15 | 52 | 3F | 5A |
| FILTER (per-channel) | 20 | 21 | 22 | 23 | 24 | 25 |
| SEND level | 05 | 0A | 16 | 53 | 65 | 76 |
| **CH FADER** | **11** | **12** | **13** | **14** | **6D** | **6E** |
| Crossfader assign (0/40/7F = A/THRU/B) | 41 | 42 | 43 | 44 | 58 | 54 |
| CUE A (note) | 07 | 08 | 09 | 0A | 0B | 0C |
| CUE B (note) | 16 | 17 | 18 | 19 | 1A | 1B |
| Beat FX CH SELECT (note) | 01 | 02 | 03 | 04 | 05 | 06 |
| Input selector (notes, prev OFF / new ON) | 32–35, 42, 51–53 | 36–39, 44–45, 54–56 | 3A–3D, 46, 57–59 | 3E–41, 48, 5A–5C | 5D–64 | 65–6C |

Global: **CROSSFADER CC `0B`**; MASTER LEVEL `18`; master FILTER `26`; BOOTH `19`; master EQ HI `6F` / LOW `73`; **MASTER ISOLATOR**
on/off note `12`, HI `27` MID `28` LOW `29`; headphones A mixing `1B` / level `1A`, B mixing `55` / level `56`; LINK CUE A/B notes
`1F`/`1D`; MIC EQ `1E`/`1F`, talkover CC `4F`; **SEND FX**: LPF note `0D`, HPF note `0E`, resonance `2C`, selects SHORT DELAY `13`,
LONG DELAY `14`, REVERB `2D`, DUB ECHO `2F`, EXT1 `2E`, EXT2 `15`, size/feedback `6C`, time `69`, tone `6A`, MASTER MIX note `2C`, level
`6B`; **BEAT FX**: beat ◀/▶ CC `4C`/`4D`, TAP `4E`, AUTO/TAP note `2A`, QUANTIZE note `76`, freq LOW/MID/HI CC `68`/`67`/`66`, effect
select (prev OFF / new ON, CC) DELAY `2A`, ECHO `37`, PING PONG `33`, SPIRAL `2B`, HELIX `3E`, REVERB `36`, SHIMMER `3A`, FLANGER `32`,
PHASER `39`, FILTER `3B`, TRANS `35`, ROLL `2E`, PITCH `2F`, **VINYL BRAKE `3D`**, TIME `0D`/`2D` (14-bit; halved for
flanger/phaser/filter), LEVEL/DEPTH `5B`, **ON/OFF CC `72`**, X-PAD position CC `74` (slider mode) / `75` (beat mode), X-PAD touch note
`2B`, Beat FX channel-select notes MIC `10`, CH1–6 `01`–`06`, MASTER `11`; MULTI I/O level `71`, on/off CC `40`, mode `70`, CH select
notes `22`–`29`; GUI fader-curve sliders `5E`/`5F`; **Timing Clock `F8`**.

(The V10's "VINYL BRAKE" is a Beat FX, i.e. the *mixer* braking its channel audio; it is distinct from a CDJ vinyl-stop.)

### 5.2 DJM-A9 MIDI message list (official PDF, E_10)

Source: https://downloads.support.alphatheta.com/midi-mapping/dj-mixers/DJM-A9/DJM-A9_MIDI_Message_List_E_10.pdf (from
https://support.alphatheta.com/en-us/articles/16006872025369 ). Same conventions, 4 channels, 3-band EQ, Sound Color FX:

| Control | CH1 | CH2 | CH3 | CH4 |
|---|---|---|---|---|
| TRIM | 01 | 06 | 0C | 50 |
| EQ HI / MID / LOW | 02 / 03 / 04 | 07 / 08 / 09 | 0E / 0F / 15 | 51 / 5C / 52 |
| **COLOR** (Sound Color FX knob) | 05 | 0A | 16 | 53 |
| **CH FADER** | **11** | **12** | **13** | **14** |
| Crossfader assign | 41 | 42 | 43 | 44 |
| CUE A / CUE B (notes) | 0A / 10 | 0B / 11 | 0C / 12 | 0D / 13 |

Global: **CROSSFADER CC `0B`**; MASTER `18`, master EQ HI `6D` / LOW `6E`, BOOTH `19`; Sound Color FX type buttons (notes) SPACE `55`,
DUB ECHO `69`, CRUSH `6A`, SWEEP `6B`, NOISE `56`, FILTER `57`, PARAMETER CC `6C`; MIC section (talkover note `61`, FX notes/CCs
`61`–`65`, reverb note `60`); Beat FX identical family: beat ◀/▶ `4C`/`4D`, TAP `4E`, AUTO/TAP CC `45`, QUANTIZE note `76`, freq
`68`/`67`/`66`, effect selects (DELAY `2A`, ECHO `37`, PING PONG `33`, SPIRAL `2B`, HELIX `3E`, REVERB `36`, FLANGER `32`, PHASER `39`,
FILTER `3B`, TRIPLET FILTER `3A`, TRANS `35`, ROLL `2E`, TRIPLET ROLL `2F`, MOBIUS `3D`), TIME `0D`/`2D` 14-bit, LEVEL/DEPTH `5B`, ON/OFF
CC `72`, X-PAD slide CC `74` / touch CC `72`, CH-select notes `01`–`08`; SEND level `71`, INSERT CC `40`, insert source `6F`; Multi
I/O notes `22`–`29`; fader-curve GUI `5E`/`5F`; Timing Clock `F8`. (Two cells in the PDF text extraction were column-shifted —
CH2 CUE B / CH FADER — I have listed the obvious intended values; verify against the PDF before mapping.)

### 5.3 DJM-900NXS2

The support page https://support.alphatheta.com/en-us/articles/4404624192665 lists a "DJM-900NXS2 addendum MIDI Message EN
(295 kB), 09/Feb/2016"; the download endpoint returned an HTML shell for me, so **its contents are not verified here**. It is the
same 4-channel / 3-band / Color FX / Beat FX family, 7-bit CCs; expect fader CCs 11–14 and crossfader 0B like the A9, but check.

### 5.4 CDJ-3000 over USB: HID (and MIDI) only in CONTROL MODE

The CDJ-3000 manual ("Using a DJ application (MIDI/HID)", p.71 of the instruction manual,
https://www.manualslib.com/manual/1909473/Pioneer-Dj-Cdj-3000.html?page=71 ): "If you use a USB cable to connect a PC/Mac with
MIDI or HID compatible software (DJ application) installed, you can control the application from the unit." You must select
**[CONTROL MODE]**, and "To use MIDI software, set the MIDI channel in [MIDI CHANNEL] in the [UTILITY] settings. The setting is not
needed when using HID software." The MIDI message list is referenced to pioneerdj.com/support; I could not locate the CDJ-3000
MIDI PDF (the A9/V10-style `downloads.support.alphatheta.com/midi-mapping/...` guesses 404) **[CDJ-3000 MIDI note/CC map
unverified]**. In HID mode (rekordbox Performance, Serato, Traktor, VirtualDJ) the deck exposes jog (vinyl/CDJ modes, scratch,
bend, loop adjust), play/cue, pitch fader, 8 hot cues, loop 4/8/in/out, beat jump, sync, key sync, master tempo, slip, quantize,
reverse, browse encoder, master button; **not** the touchscreen, USB/SD sources or playlist UI (VirtualDJ's control list,
https://virtualdj.com/manuals/hardware/pioneer/cdj3k/controls.html ).

The decisive point for the overlay: **control mode turns the CDJ into a controller for the laptop software; the deck's own media
playback is not what you're watching any more.** A CDJ-3000 playing from USB/Link does not stream its button presses or jog
motion out of its USB-B port, and HID is a proprietary report format that NP3's MIDI Bridge (CC/Note/Pitch-Bend only) cannot read.
So "CDJ over USB" is not a passive tap on a normal CDJ+DJM set; it is a different rig (rekordbox/Serato in HID mode), in which
case the software, not the CDJ, is the thing to instrument.

---

## 6. alphatheta-connect (v0.28.5) — what it actually decodes and emits

Connection modes (`src/network.ts`): `connectMethod: 'active' | 'stagehand'` (plus a separate passive pcap stack in `src/passive/`).
Active = virtual CDJ (default id 5, name "ProLink-Connect"; "player number auto-picks from the mixer's channel count"). Stagehand
= virtual iPad: random device id 141–211, protocol MAC `c8:3d:fc` + low 3 bytes of the host NIC, startup `0x0a`×3 → `0x02`×3 at
305 ms, keep-alive every 2000 ms (`src/virtualcdj/stagehand.ts`), `DeviceType.Stagehand = 0x05`, model code `0x20`.

**Events:**

- `network.deviceManager` — `connected(device)` (and disconnection) from keep-alives.
- `network.statusEmitter` (`src/status/index.ts`): `status(CDJStatus.State)` for every `0a`; `mediaSlot(MediaSlotInfo)`; `onAir(OnAirStatus)`
  (4- and 6-channel); `mixerState(MixerState)` — **Stagehand mode only**, from `0x39`.
- `network.positionEmitter` (`src/status/position.ts`): `position(PositionState)` from `0b`; `vu(VUState)` — Stagehand only, from `0x58`.
- `MixstatusProcessor` (`src/mixstatus/index.ts`): `nowPlaying(state)`, `stopped({deviceId})`, `setStarted()`, `setEnded()` — a
  debounced "which deck is live" layer using `isOnAir`, play state and beat counts (`beatsUntilReported` default 128,
  `allowedInterruptBeats` 8, `timeBetweenSets` 30 s).

**Not handled at all:** beat packets `0x28` (no parser anywhere in `src/`; the 50001 socket only yields position/VU), mixer status
`0x29` (dropped by `statusFromPacket`'s `< 0xc8` length guard), fader-start `0x02`, sync/master handoff, touch audio. So NP3 does
not get a per-beat tick from this library; it gets beat-in-bar at the 200 ms status cadence and, on CDJ-3000, the 30 ms playhead.

**Subset of the status packet decoded** (`src/status/utils.ts::statusFromPacket`): `deviceId 0x21`, `trackId 0x2c`, `trackDeviceId 0x28`,
`trackSlot 0x29`, `trackType 0x2a`, `playState 0x7b`, `isOnAir/isSync/isBpmSync/isMaster` from `0x89`, `isEmergencyMode 0xba`,
`trackBPM 0x92`, `effectivePitch 0x8d..` (Pitch_1), `sliderPitch 0x99..` (Pitch_2; the two were swapped before v0.24.0),
`beatInMeasure 0xa6`, `beatsUntilCue 0xa4`, `beat 0xa0`, `deviceType 0xcc`, `packetNum 0xc8`. **Not decoded:** P_2, P_3 (reverse / slip /
vinyl-vs-CDJ), M_m/M_h, Sync_n, loop start/end/beats, Key, KeyShift, Master Tempo, NeedleDragPos, buffer, T_b/T_pos, the `u_c1`
cue-edit trigger, firmware, settings blocks. Those are all in the raw buffer; a fork or a sidecar parser can add them.

Quoted types (`src/status/types.ts`):

```ts
export enum StatusFlag { BpmSync = 1 << 1, OnAir = 1 << 3, Sync = 1 << 4, Master = 1 << 5, Playing = 1 << 6 }

export enum PlayState {
  Empty = 0x00, Loading = 0x02, Playing = 0x03, Looping = 0x04, Paused = 0x05, Cued = 0x06,
  Cuing = 0x07, PlatterHeld = 0x08, Searching = 0x09, SpunDown = 0x0e, Ended = 0x11,
}

export interface State {
  deviceId: number; trackId: number; trackDeviceId: DeviceID; trackSlot: MediaSlot; trackType: TrackType;
  playState: PlayState; isOnAir: boolean; isSync: boolean; isBpmSync: boolean; isMaster: boolean;
  isEmergencyMode: boolean; trackBPM: number | null; effectivePitch: number; sliderPitch: number;
  beatInMeasure: number; beatsUntilCue: number | null; beat: number | null; deviceType: number; packetNum: number;
}

export interface PositionState { deviceId: number; trackLength: number; playhead: number; pitch: number; bpm: number | null; }

export interface OnAirStatus {
  deviceId: number;
  channels: { 1: boolean; 2: boolean; 3: boolean; 4: boolean; 5?: boolean; 6?: boolean };
  isSixChannel: boolean;
}

export interface ChannelState {
  trim: number; eqHi: number; eqMid: number; eqLow: number; colorFx: number; fader: number;
  crossfaderAssign: 'thru' | 'A' | 'B';
}
export interface MixerState { deviceId: number; deviceName: string; channels: Record<number, ChannelState>; crossfader: number; }

export interface VUFrame { left: number; right: number }           // 0-65535
export interface VUState { deviceId: number; channels: Record<number, VUFrame[]> }  // 15 frames per channel
```

Note `PlayState.PlatterHeld = 0x08` is what dysentery calls "Cue scratch is in progress"; `ChannelState` maps A9 block offsets +01/+03/+04/+06/+07/+0b/+0c
and deliberately skips the +05 slot (the suspected V10 MID-LOW band).

**Device quirks handled:**

- *Opus Quad* — no virtual-CDJ path; passive pcap only. The repo's `docs/opus-quad-support-plan.md` (deck ids 9–12, `0x56` multi-packet
  artwork/PSSI pushes, OneLibrary DB) is a plan; `src/passive/devices.ts` still comments "1-6 are CDJ slots, 17 is Rekordbox, 33+ are
  mixer", so Opus deck-id mapping in this version is **[unverified]**. Per kyleawayan's analysis (https://github.com/kyleawayan/opus-quad-pro-dj-link-analysis )
  the Opus sends CDJ-status-like packets to rekordbox lighting mode with beat numbers but **no USB slot, no looping status, and no
  `0b` absolute position** ("The OPUS-QUAD does not send high-precision position packets like the CDJ-3000 does"); beat-link gets at it
  by posing as rekordbox (`VirtualRekordbox.java`). Expect only play state / BPM / beat for Opus decks.
- *XDJ-XZ / XDJ-AZ / RX* — passive mode; one IP hosting players 1–2 and mixer 33; USB1→SD slot, USB2→USB slot (AZ 4-deck adds `S_r`=`07`);
  P_2 values `9a/9e`; no `mediaSlot` broadcasts, so the DB is fetched blind over NFS (`docs/ALL_IN_ONE_UNITS.md`).
- *CDJ-3000 on channels 5/6* — needs the `0x64` keep-alive variant (`docs/FULL_STARTUP.md`).
- *Streaming tracks* — `MediaSlot.StreamingDirectPlay = 0x06`, `Beatport = 0x09`, metadata via `2002` query only from a vcdj id ≤ 6.

---

## 7. Gesture availability matrix

Legend: **A** = directly available as a field/event · **D** = derivable (how) · **–** = not available. Rates are the stream you'd
derive it from. "Link" = CDJ-3000 + DJM-V10 over Pro DJ Link in NP3 Active/Passive mode; "Link+SH" = adds the Stagehand/Bridge
unicast (DJM-A9 verified, V10 unverified); "DJM MIDI" = mixer USB MIDI into NP3 MIDI Bridge (V10/A9 lists above); "CDJ USB" =
CDJ-3000 in CONTROL MODE (HID; MIDI map unverified).

| Gesture / signal | Link (3000 + V10) | Link + Stagehand (A9) | DJM over USB MIDI | CDJ over USB |
|---|---|---|---|---|
| Channel fader move | – (only on-air boolean `03`, event-rate) | **A** 8-bit @ ~4 Hz (`0x39` +0b) | **A** 7-bit CC 11–14 (+6D/6E on V10), on movement, ~ms | – |
| EQ move (per band) | – | **A** HI/MID/LOW 8-bit @ 4 Hz; V10 4th band hypothesised | **A** 7-bit CCs (V10 4-band incl. LOW-MID; A9 3-band), on movement | – |
| Filter / Color FX knob | – (filter *cut* only shows up inside on-air) | **A** colour knob @ 4 Hz; FX *type* undecoded | **A** V10 per-ch FILTER CC 20–25, master filter 26; A9 COLOR CC 05/0A/16/53 + type notes | – |
| Crossfader | – (folded into on-air) | **A** 8-bit @ 4 Hz (offset 0xb4) + per-ch assign | **A** CC 0B + assign CCs | – |
| Beat FX type / on / level / beats / channel | – | master/FX block undecoded | **A** all (type CCs, ON/OFF 72, level 5B, beats 4C/4D, CH-select notes, TIME 14-bit) | – |
| Isolator / compressor / sends (V10) | – | – | **A** CCs | – |
| Play / pause / cue edges | **A** P_1 (`03/05/06/07`) + F bit6, 200 ms (faster while jogging); exact edge also in `0b` velocity | same | – (DJM Fader Start `02` not supported by CDJ-3000) | HID (control mode) |
| Hot-cue press | **D** position jump in `0b` (30 ms) / `Beat` (200 ms) to a known hot-cue time (cue list via dbserver/ANLZ); no button id | same | – | HID |
| Hot-cue set / delete | **A** `u_c1` flashes `ffff` once (both hot & memory cues); which one via re-query | same | – | HID |
| Loop active | **A** P_1=`04` + Loop_s/Loop_e/Loop_b (CDJ-3000, 200 ms) | same | – | HID |
| Loop in / out / size change | **D** Loop_s/Loop_e/Loop_b transitions at 200 ms | same | – | HID |
| Loop roll (slip-loop) | **D** P_3=`0b` (slip) together with loop fields; nxs2-era M_slip/BPM_slip — CDJ-3000 slip fields **[unverified]** | same | – | HID |
| Beat jump | **D** `Beat` counter / `0b` playhead jumps by ±N beats while P_1 stays `03` | same | – | HID |
| Slip mode on | **D** P_3=`0b` only while actually slipping; not the armed state | same | – | HID |
| Reverse | **A** P_3=`01` with P_1=`03` (beat-link `isPlayingBackwards`); **D** negative `0b` velocity | same | – | HID |
| Jog touch (platter held) | **D** P_1=`03` & P_2 "stopped" (`7e`-family); `0b` velocity ≈ 0 while playing; Pitch_4 → 0 instantly | same | – | HID touch |
| Jog rotation / backspin / scratch | **D** from `0b` playhead velocity at 33 Hz (negative = backspin; sign flips = scratch); nothing in status | same | – | HID jog ticks |
| Vinyl brake | **D** `0b` velocity decays to 0 over the brake time; Pitch_2 ramps down while Pitch_4 drops to 0 | same | (V10 "VINYL BRAKE" Beat FX = mixer effect, CC 3D select + 72 on) | HID |
| Pitch nudge / bend | **D** Pitch_1 ≠ Pitch_2 transiently; F bit1 (BPM-sync) if synced; `0b` velocity ≠ pitch | same | – | HID |
| Tempo slider | **A** Pitch_2 / Pitch_4 (fader), Pitch_1 (effective), 200 ms; `0b` Pitch (× 100) at 30 ms | same | – | HID |
| Key shift / key sync / master tempo | **A** KeyShift `0x164` (cents), Key `0x15c`, M_t `0x158` — CDJ-3000, 200 ms | same | – | HID |
| Sync / master | **A** F bit4/bit5, M_m, handoff via M_h and `26`/`27` packets | same | – | HID |
| Stems | – (nothing in any packet) | – | – | – |
| Beat tick | **A** `28` per beat (phase by interpolation); mixer `28` as fallback metronome | same | **D** MIDI clock `F8` at 24 ppqn (follows the Beat FX channel) | – |
| Beat phase / bar position | **A** B_b (status 200 ms, beat 1/beat); **D** continuous phase from `0b` + beat grid | same | **D** count `F8` ticks from MIDI start | – |
| Track position | **A** `0b` playhead ms @ 30 ms (CDJ-3000 only); **D** `Beat`×grid at 200 ms on older players | same | – | – |
| Track load / source | **A** D_r/S_r/T_r/rekordbox id, t_src menu, P_1=`02` loading | same | – | – |
| On-air (audible) | **A** DJM `03` per channel (6-ch on V10) + F bit3 in each CDJ | **A** + real fader values | **D** fader > threshold & crossfader & master (NP3 mix-processor does this) | – |
| VU level | – | **A** `0x58` ~30 Hz, 15 frames/pkt (semantics "hypothesis (strong)") | – | – |

**Practical reading for the Street-Fighter overlay on a CDJ-3000 + DJM-V10 rig:** everything *deck-side* that matters (scratch,
backspin, brake, hot-cue hits, beat jumps, loops, reverse, slip-roll, nudges) is derivable, and most of it only because of the
CDJ-3000's 30 ms `0b` stream plus the 200 ms status fields that alphatheta-connect currently leaves undecoded (P_2, P_3, loop
fields, key shift). Everything *mixer-side* (fader throws, EQ kills, filter sweeps, crossfader cuts, Beat FX hits) is **not on the
link at all** for a V10; the honest options are (a) the V10's USB MIDI into NP3's MIDI Bridge (7-bit, on-movement, 6 channels,
14-bit FX time, MIDI clock), or (b) swapping in a DJM-A9 and using NP3 Bridge/Stagehand mode (8-bit @ 4 Hz, no FX decode yet).
Beat ticks themselves come from `28` packets that NP3's library ignores today, so a `beat.tick` event needs either a small
50001 listener or the MIDI clock from the DJM.

---

### Source index

- dysentery analysis: https://djl-analysis.deepsymmetry.org/djl-analysis/packets.html , `beats.html#beat-packets`, `beats.html#absolute-position-packets`,
  `vcdj.html#cdj-status-packets`, `vcdj.html#mixer-status-packets`, `vcdj.html#cdj-status-flag-bits`, `vcdj.html#known-p1-values`, `vcdj.html#known-p3-values`,
  `vcdj.html#cdj-settings-block`, `mixer_integration.html#fader-start`, `mixer_integration.html#channels-on-air`, `sync.html#tempo-master-handoff`,
  `startup.html#cdj-keep-alive`, `startup.html#startup-3000`, `stagehand.html` (`#a9-mixer-state`, `#a9-vu-stream`, `#cdj-0b-multiplex`, `#timing-stream`),
  `track_metadata.html`, `touch_audio.html`; repo https://github.com/Deep-Symmetry/dysentery ; Wireshark dissectors https://github.com/nudge/wireshark-prodj-dissectors
- alphatheta-connect: https://github.com/chrisle/alphatheta-connect — `src/status/types.ts`, `src/status/utils.ts`, `src/status/index.ts`, `src/status/position.ts`,
  `src/virtualcdj/stagehand.ts`, `src/network.ts`, `src/mixstatus/index.ts`, `src/passive/*`, `docs/STAGEHAND.md`, `docs/ABSOLUTE_POSITION.md`,
  `docs/ON_AIR_CHANNELS.md`, `docs/ALL_IN_ONE_UNITS.md`, `docs/opus-quad-support-plan.md`, `CHANGELOG.md`
- beat-link: https://github.com/Deep-Symmetry/beat-link — `CdjStatus.java`, `PrecisePosition.java`, `Beat.java`, `BeatFinder.java`, `VirtualRekordbox.java`
- Now Playing 3: https://nowplayingapp.com/help/reference/integrations/prodjlink/ , https://nowplayingapp.com/help/changelog/ ,
  https://nowplayingapp.com/help/reference/integrations/midi-bridge/ , https://nowplayingapp.com/help/guide/settings/on-air-detection/ ,
  https://nowplayingapp.com/help/reference/concepts/mix-processor/
- AlphaTheta / Pioneer DJ: DJM-V10 MIDI list https://downloads.support.alphatheta.com/manuals/DJM_V10_DJM_V10_MIDI_Message_List_E1_addendum.pdf ;
  DJM-A9 MIDI list https://downloads.support.alphatheta.com/midi-mapping/dj-mixers/DJM-A9/DJM-A9_MIDI_Message_List_E_10.pdf ;
  MIDI FAQ https://support.alphatheta.com/en-US/articles/4408487552153 ; DJM-900NXS2 manuals page https://support.alphatheta.com/en-us/articles/4404624192665 ;
  PRO DJ LINK Bridge https://support.alphatheta.com/en-US/articles/7292587209113 , https://www.pioneerdj.com/en-us/product/software/pro-dj-link-bridge/software/overview/ ,
  https://assets.pioneerdjhub.com/PRO_DJ_LINK_Bridge_Instruction_Manual_EN.pdf ; Stagehand https://www.pioneerdj.com/en/product/software-interfaces/stagehand/ ;
  CDJ-3000 manual (MIDI/HID) https://www.manualslib.com/manual/1909473/Pioneer-Dj-Cdj-3000.html?page=71 ; VirtualDJ CDJ-3000 HID controls
  https://virtualdj.com/manuals/hardware/pioneer/cdj3k/controls.html ; CDM on V10 MIDI clock https://cdm.link/2024/01/pioneer-v10-midi
- Opus Quad: https://github.com/kyleawayan/opus-quad-pro-dj-link-analysis ; Stagehand captures issue https://github.com/Deep-Symmetry/dysentery/issues/78
