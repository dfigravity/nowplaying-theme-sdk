# Hardware ecosystems: what each DJ rig can actually tell us (beyond the FLX10 and Pro DJ Link)

Research note for the DJ Street Fighter overlay. Written 2026-10-06. Scope: every data path into Now Playing 3 (NP3) other than the DDJ-FLX10 MIDI map and Pro DJ Link, which are covered in `np3_platform_and_flx10_midi.md`. Everything below is either read from source (clones in the session scratchpad: `chrisle/autopilot-mappings`, `chrisle/serato-connect`, `chrisle/StageLinq`, `MarByteBeep/StageLinq`, `icedream/go-stagelinq`, `mixxxdj/mixxx` `res/controllers`), from manufacturer PDFs, or from the NP3 help centre. Claims I could not pin to a source are marked **[unverified]**; claims that rest on a secondary summary are marked **[secondary]**.

The one-paragraph version: **MIDI is the only path that carries knobs, pads and jog motion, and it only exists for controllers and mixers that speak MIDI to the computer.** StageLinQ (Denon) and Serato Remote (OSC) carry *derived* deck state (play, position, BPM, loop, channel faders, crossfader) but no EQ, no filter, no pads, no jog rotation. Traktor's own hardware (S4 MK3, S8, D2, Z2) is HID, so NP3's MIDI Bridge sees nothing from it, and Traktor itself only emits track metadata. VirtualDJ, djay, DJUCED and Mixxx are history/database paths in NP3 today. The practical consequence for a fighting-game overlay is that moves should be declared against a *capability set* the host announces per channel, not against a fixed controller.

---

## 1. Canonical control taxonomy

Conventions used in the table:

- **Type**: `edge` (bool press/release, we care about both edges and hold time), `bool` (latched state), `uni` (0..1), `bi` (-1..1, centre-detented), `rel` (signed ticks per message), `enum`, `int`, `float`, `time`.
- **Native res**: what the wire actually carries. 7-bit = 128 steps; 14-bit = MSB/LSB CC pair (16384 steps); HID fields are 8/12/16/32-bit; network protocols carry IEEE floats.
- **Rate**: typical message cadence while the control is in motion.
- **NP3 name**: `npControlType` strings used across the 288 maps in `chrisle/autopilot-mappings` (https://github.com/chrisle/autopilot-mappings; counted with `grep -o '"npControlType": "[^"]+"' Mappings/*.map | sort | uniq -c`). The brief listed 21 names; the maps actually use **77** distinct names. Names in *italics* are proposals where NP3 has none.

NP3's full observed vocabulary, most to least frequent: `hot_cue, tempo, cue, channel_fader, play_pause, eq_low, eq_high, eq_mid, trim, jog_turn, sync, jog_touch, filter, key_lock, loop_out, loop_in, loop_active, master, crossfader, loop_half, loop_double, beat_loop, encoder, headphone_mix, headphone_volume, master_volume, pad_mode, fx_on, fx_param, fx_select, jog_wheel, beat_jump_fwd, beat_jump_rev, hot_cue_mode, slip, quantize, jog_mode, search_rev, search_fwd, reverse, needle_search, track_prev, track_next, tempo_range, encoder_push, tempo_reset, slip_loop, memory, call_prev, back, time_mode, slip_reverse, call_next, booth_volume, touch_brake, fx_wet_dry, tag_track, delete, jog_ring, key_sync, eject, beat_divide, fader_start, track_filter, release_start, vinyl_speed_adjust, loop_mode, key_shift_up, key_shift_down, key_reset, hold, beat_select`. Control IDs are namespaced `mixer.ch<N>.<name>` (per channel) and `header.<name>` (global). Each binding carries `message` (`cc`|`note`), `channel`, `number`, `mode` (`absolute`|`momentary`|`relative`), `pickup`, `invert`, `rangeMin/Max`, `apConfidence` (`verified`|`speculative`). The repo README's own caveat applies: "I have no idea if any of this works ... None of it has been loaded into Autopilot."

### 1.1 Transport

| Control | Type | Native res (MIDI / HID / network) | Rate | NP3 name |
|---|---|---|---|---|
| Play/pause | edge | Note on/off 0/127; StageLinQ `Play` bool + `PlayState` enum; Serato `playRate` float | event | `play_pause` (NP3 themes see `playing`) |
| Cue press / hold | edge + hold time | Note on/off | event | `cue` (themes: `cueActive`) |
| Sync | edge → bool | Note; StageLinQ `SyncMode` enum | event | `sync` |
| Master (tempo master) | bool | Note; StageLinQ `DeckIsMaster` | event | `master` |
| Key lock | bool | Note; StageLinQ `Track/KeyLock` | event | `key_lock` |
| Slip | bool | Note; StageLinQ `Track/SlipModeActive` | event | `slip` |
| Reverse | bool | Note | event | `reverse`, `slip_reverse` |
| Vinyl mode | bool | Note | event | `jog_mode` |
| Quantize | bool | Note | event | `quantize` |

### 1.2 Jog

| Control | Type | Native res | Rate | NP3 name |
|---|---|---|---|---|
| Platter touch | edge | Note; StageLinQ `ExternalScratchWheelTouch` bool; S4 MK3 HID bit | event | `jog_touch` (themes: `jogTouching`) |
| Platter rotation (top, scratch) | rel | Pioneer CC: "Count value difference from previous operation", 0x41 + n CW, 0x3F − n CCW (XDJ-RX3 MIDI list); S4 MK3 HID: 32-bit absolute position 0..2879 + 32-bit timer | one CC per USB poll while moving (≤ 1 kHz) | `jog_turn` |
| Ring / wheel-side rotation (pitch bend) | rel | same encoding, separate CC (RX3: CC 33 side, CC 34 platter) | same | `jog_turn` (Pioneer maps label it "Pitch Bend"), `jog_ring` |
| Jog search (shift + jog) | rel | separate CC (RX3: CC 41/38 with SHIFT) | same | *`jog_search`* |
| Needle / strip search | uni | CC 7-bit | event | `needle_search` |

### 1.3 Tempo

| Control | Type | Native res | Rate | NP3 name |
|---|---|---|---|---|
| Tempo slider | bi (or uni raw) | Pioneer: 14-bit (CC 0 MSB + CC 32 LSB, 0..16383 per XDJ-RX3 list; FLX4 Mixxx script reassembles `(msb<<7)+lsb`); S4 MK3 HID: 12-bit field "0..4096 but only 510 steps"; StageLinQ `Speed` float, `SpeedRange` | up to 2 CCs per step | `tempo` (themes: `pitch`) |
| Tempo range | enum | Note | event | `tempo_range` |
| Tempo reset | edge | Note | event | `tempo_reset` |
| Bend buttons / nudge | edge | Note | event | *`bend_up`*, *`bend_down`* |

### 1.4 Per-channel mixer

| Control | Type | Native res | Rate | NP3 name |
|---|---|---|---|---|
| Channel fader | uni | DJM/XDJ/Prime: 7-bit CC; FLX10: 14-bit pair; S4 MK3 HID: 16-bit field; StageLinQ `/Mixer/CHnfaderPosition` float 0..1; Serato `/Status/Video/Deck/Mixer/Upfader` float 0..1 | one msg per step | `channel_fader` (themes: `channelFader`) |
| Trim / gain | uni | 7-bit CC (14-bit on FLX10) | per step | `trim` |
| EQ high/mid/low | bi | 7-bit CC centred 64 (14-bit on FLX10); S4 MK3 16-bit | per step | `eq_high`, `eq_mid`, `eq_low` |
| 4-band / isolator | bi | 7-bit CC (DJM-V10 has 4-band; its list not published online) | per step | *`eq_lowmid`*, *`isolator_hi/mid/low`* |
| Colour FX / filter knob | bi | 7-bit CC centred 64 | per step | `filter` |
| Colour FX type | enum | Note per type (RX3: Space, Dub Echo, Sweep, Noise, Crush, Filter, Pitch, Helix, Reverb, Trans) | event | *`color_fx_type`* |
| Send / aux | uni | 7-bit CC | per step | *`send`* |
| PFL cue button | bool | Note / CC; StageLinQ `/Engine/Mixer/Channel%d/PFL` | event | *`pfl`* |
| Crossfader assign | enum (A/thru/B) | CC 0/64/127 (DJM-900NXS list) ; StageLinQ `/Mixer/ChannelAssignment%d` | event | *`xf_assign`* (themes already carry `crossfader.assignmentA/B`) |
| On-air | bool | derived (NP3 computes `isOnAir`); Pro DJ Link carries it natively | derived | `isOnAir` (theme field) |
| Channel level meter | uni | XDJ-RX3 list row "CH LEVEL METER ... CC Bn 2" **[unverified direction; appears in the MIDI-OUT column]** | continuous | *`level_meter`* |

### 1.5 Global mixer

| Control | Type | Native res | Rate | NP3 name |
|---|---|---|---|---|
| Crossfader | bi | 7-bit CC (14-bit FLX10); StageLinQ `/Mixer/CrossfaderPosition` float; Serato `/Status/Video/Mixer/Crossfader` float 0..1 (not centred) | per step | `crossfader` |
| Crossfader curve | enum | CC (DJM-900NXS "FADER CURVE"; RX3 "THRU 0/40/7F") | event | *`xf_curve`* |
| Master / booth level | uni | 7-bit CC | per step | `master_volume`, `booth_volume` |
| Mic level / on | uni + bool | 7-bit CC / Note | per step | *`mic_level`*, *`mic_on`* |
| Headphone level / mix | uni | 7-bit CC | per step | `headphone_volume`, `headphone_mix` |
| Beat FX type | enum | one CC/Note per type (RX3 lists 16 types each on its own CC number) | event | `fx_select` |
| Beat FX on | bool | CC 0/127 (RX3: B4 114) | event | `fx_on` |
| Beat FX level/depth | uni | 7-bit CC (RX3: B4 91) | per step | `fx_wet_dry`, `fx_param` |
| Beat FX beats (time) | rel/enum | RX3: "TIME rotate ... Transfer count value difference from previous operation (±1~±30)" | event | *`fx_beats`* |
| Beat FX channel assign | enum | one CC per target (CF.A, CF.B, MIC, AUX, CH1..4, MASTER) | event | *`fx_assign`* |
| X-pad / touch strip | uni | 7-bit CC | per step | *`fx_xpad`* |

### 1.6 Performance

| Control | Type | Native res | Rate | NP3 name |
|---|---|---|---|---|
| Hot cue 1–8 press / set / delete | edge (+ pad mode context) | Note per pad per pad-mode (Pioneer uses separate MIDI channels 6–9 per pad mode); StageLinQ: `HotCue1..8` listed in chrisle docs **[unverified path]** | event | `hot_cue`, `hot_cue_1..8`, `hot_cue_mode`, `delete`, `memory` |
| Loop in / out / exit / active | edge → bool | Note; StageLinQ `Track/LoopEnableState`, `Loop/Active`, `CurrentLoopInPosition/OutPosition`; Serato `AutoLoopOn`, `ManualLoopOn` | event | `loop_in`, `loop_out`, `loop_active` (themes: `looping`) |
| Loop size / half / double | int or edge | Note; StageLinQ `CurrentLoopSizeInBeats`; Serato `BeatLength` | event | `loop_half`, `loop_double`, `beat_loop`, `beat_loop_<n>` |
| Loop roll | bool | Note; Serato `LoopRollOn` | event | `slip_loop` |
| Beat jump | edge | Note; StageLinQ `BeatJump/BeatJumpIndex` | event | `beat_jump_fwd`, `beat_jump_rev` |
| Slicer | edge | Note (pad mode) | event | *`slicer`* |
| Sampler | edge | Note (pad mode) | event | *`sampler`* |
| Pad FX | edge | Note (pad mode) | event | *`pad_fx`* |
| Keyboard / key shift | int | Note per pad | event | `key_shift_up`, `key_shift_down`, `key_reset`, `key_sync` |
| Stems / parts | bool per stem | Note per pad (XDJ-AZ pad page: STEMS VOCAL / INST / DRUMS ON/OFF; FLX10 Track Separation covered in sibling note) | event | *`stem_vocal`*, *`stem_inst`*, *`stem_drums`*, *`stem_solo`* |

### 1.7 Deck / track

| Control | Type | Native res | Rate | NP3 name |
|---|---|---|---|---|
| Load / eject | edge | Note; StageLinQ `Track/SongLoaded`; Serato `Song/Valid` | event | `eject`, *`load`* |
| Position | time | StageLinQ `TrackData/PlayheadPosition` (not subscribed by NP3's library; "update every few milliseconds"); Serato `Playhead` float seconds; djay DB `playback position` (2 s poll) | ms–s | *`position`* |
| Beat / phase / bar | float | StageLinQ BeatInfo `beat` (fractional, ~35 ms); Serato: none; OS2L: `pos` per beat; MIDI: none | 28 Hz / per beat | *`beatPhase`*, *`bar`* |
| Phrase | enum | Pro DJ Link only (CDJ-3000 phrase analysis) | per phrase | *`phrase`* |
| BPM | float | StageLinQ `CurrentBPM`, BeatInfo `bpm`; Serato `Playhead` float 2 (pitch-adjusted); Traktor broadcast tag; MIDI: none | event | theme `track.bpm` |
| Key | string | StageLinQ `Track/CurrentKey`; databases | event | theme `track.key` |
| Duration / remaining | time | StageLinQ `TrackLength`; Serato: none over OSC ("no track-length field is exposed by this protocol at all") | event | theme `track.duration` |

---

## 2. Ecosystem by ecosystem

### 2a. Pioneer / AlphaTheta controllers and all-in-ones with rekordbox (DDJ-FLX4/6/10, DDJ-1000, DDJ-REV7, XDJ-RX3 / XZ / AZ, OPUS-QUAD)

**Transport.** All of these are USB-MIDI class devices. rekordbox itself does not expose deck state to third parties; NP3 reads rekordbox's `master.db` history and gets live control state only from the controller's MIDI, via the MIDI Bridge (https://nowplayingapp.com/help/reference/integrations/midi-bridge/: "MIDI devices are normally locked to a single listening application unless they are set up as multi-client"; the bridge "emits a line of JSON on stdout per message"; mappings "normalize signals into 0–1 linear signals or -1 to 1 bipolar signals"; message types captured are CC, Note On/Off and Pitch Bend; 98 mappings, 61 of them Pioneer; macOS only, Windows pending).

**What the MIDI lists show (XDJ-RX3 as the worked example).** The rekordbox hardware-diagram PDFs double as MIDI message lists. XDJ-RX3 (https://cdn.rekordbox.com/files/20211108182410/XDJ-RX3_Hardware_Diagram_en.pdf; newer revision https://cdn.rekordbox.com/files/20211202183746/XDJ-RX3_HardwareDiagram_en2.pdf):

- Channel plan: Deck 1–4 on MIDI ch 1–4 (`n=0..3`), mixer/effect on ch 5 (`B4`), performance pads on ch 6–9, "OTHERS & JOG DISPLAY" on ch 12. Pads use a *separate MIDI channel per pad mode*, so the same note number means hot cue, beat loop, slip loop or pad FX depending on channel.
- Jog: "Jog dial (Platter) rotate: CC Bn 34 — Count value difference from previous operation. When turned clockwise: increases from (0x41). When turned counterclockwise: decreases from (0x3F)". Wheel side (pitch bend ring) is CC 33 with identical encoding; SHIFT variants are CC 41/38; touch is Note 32 (Note 72 with SHIFT). So jog rotation is **relative, 7-bit, ±63 ticks per message**, not an absolute angle.
- Tempo: "CC Bn 0 (MSB) / CC Bn 32 (LSB) — 0~16383" — the only 14-bit control on the unit.
- Mixer (ch 5, all 7-bit 0..127): crossfader CC 11; channel faders CC 17–20; trim CC 1/6/12/80; EQ HI 2/7/14/81, MID 3/8/15/92, LOW 4/9/21/82; COLOR knob 5/10/22/83 ("Left (LOW): 0, Right (HI): 127"); headphones mix 27 / level 26; master 24; booth 25; CH cue buttons CC 70–73; crossfader-curve/THRU switch CC 95 with values 0/0x40/0x7F.
- Beat FX: on/off CC 114; level/depth CC 91; FX time encoder CC 45 sent as a *relative* count "(±1~±30)"; each FX type (Delay, Echo, Ping Pong, Spiral, Reverb, Trans, Filter, Flanger, Phaser, Pitch, Slip Roll, Roll, Vinyl Brake, Helix) and each channel-select target has its own CC number.
- Colour FX type buttons (Space, Dub Echo, Sweep, Noise, Crush, Filter, Pitch, Helix) each have a CC.
- A row reads "CH LEVEL METER … CC Bn 2 … Refer to MIDI-OUT/CH LEVEL METER" **[unverified]** — if that is an output from the unit, the mixer's channel meters are available over MIDI, which no other path offers.

The XDJ-XZ and XDJ-AZ maps in autopilot-mappings describe the same shape: "jog wheel platter rotation (relative, 0x41=CW, 0x3F=CCW)", "tempo slider MSB (14-bit, paired with CC 32 LSB)", mixer on ch 5, 7-bit EQ/filter/fader (XDJ-AZ channel fader noted "INVERTED: 0=top, 127=bottom"). Diagrams: XDJ-XZ https://cdn.rekordbox.com/files/20200124131237/XDJ-XZ_Hardware_Diagram_en.pdf, XDJ-AZ https://cdn.rekordbox.com/files/20250107172240/XDJ-AZ_HardwareDiagram_en.pdf, OPUS-QUAD https://cdn.rekordbox.com/files/20230726091755/OPUS-QUAD_HardwareDiagram_en2.pdf, DDJ-1000 https://cdn.rekordbox.com/files/20200124131224/DDJ-1000_Hardware_Diagram_en.pdf, DDJ-FLX6 https://cdn.rekordbox.com/files/20201118182446/DDJ-FLX6_Hardware_Diagram_en.pdf, DDJ-REV7 https://cdn.rekordbox.com/files/20240314141400/DDJ-REV7_HardwareDiagram_rekordbox_en.pdf (index: https://rekordbox.com/en/support/diagram/). Text extraction of the XZ/AZ/1000/Opus PDFs only yielded the function tables, not the MIDI rows, so their exact CC numbers here come from the autopilot maps **[secondary]**.

**7-bit vs 14-bit.** Across the 288 autopilot maps only 14 mention 14-bit at all: DDJ-FLX10 (faders, EQ, trim, crossfader, master, headphones — "MSB, 14-bit"), XDJ-XZ/AZ (tempo only), DDJ-S1/T1, Denon Prime 4/4+/GO/SC Live 2/SC5000/SC6000 (tempo and jog MSB), Hercules Inpulse 200 MK3, Numark Mixtrack Platinum FX. Everything else on the Pioneer side — DDJ-1000, DDJ-400/FLX4 (apart from tempo), DJM mixers, XDJ mixer sections — is **7-bit**. So "14-bit faders" is an FLX10 luxury, not a Pioneer norm, and the FLX10 is the exception the sibling note should not generalise from.

**Stems / Track Separation.** The XDJ-AZ pad page lists "STEMS VOCAL ON/OFF(MUTE)", "STEMS INST ON/OFF(MUTE)", "STEMS DRUMS ON/OFF(MUTE)", "STEMS MUTE/SOLO" as pad functions, i.e. plain Notes on a pad-mode channel. Stems are therefore observable as pad presses wherever the unit has a stems pad mode (FLX6-GT/FLX10/AZ/OPUS), but the resulting *audio* state is not reported back.

**Do all-in-ones emit MIDI while standalone?** Partly, and this matters because standalone XDJ users are a big slice of Triode's audience.

- XDJ-XZ manual, Utility, p.126 (https://www.manua.ls/pioneer/xdj-xz/manual?p=126): "Mixer MIDI Message — Turns MIDI on the mixer/effect section on/off. Setting ranges: OFF / SEND* / SEND WITH TIME PARAM" (asterisk = default). This setting exists precisely so the mixer section can control Serato/rekordbox while the decks play from USB (the Serato guide for the XZ needs it: https://support.serato.com/hc/en-us/articles/360001415256-Using-the-Pioneer-DJ-XDJ-XZ-with-Serato-DJ-Pro). So the **mixer section sends MIDI over USB in standalone** by default on the XZ. The RX3's MIDI list header labels the direction "MIDI-OUT (to computer)" without a mode caveat.
- Deck section in standalone: NP3's own (v2) guides for the XDJ-RX3 and XDJ-XZ "USB" path say the unit "can send track metadata to Now Playing via USB drive playback and MIDI for deck control" and list "Transport" and "On-Air Detection" as covered, which only works if the deck buttons and faders emit MIDI while playing from USB. Both guides also say **"Works with Now Playing 3: No"** (https://nowplayingapp.com/help/setup/alphatheta/xdj-rx3/usb/, https://nowplayingapp.com/help/setup/alphatheta/xdj-xz/usb/). The XDJ-XZ guide additionally claims "The XDJ-XZ does not support PRO DJ LINK networking", which contradicts the same page family offering "Link (Same PC)" and "Link (Separate PC)" guides for the XZ and the unit's LINK port; treat the NP3 guide text as stale **[unverified]**. The OPUS-QUAD USB guide says "Works with Now Playing 3: Yes" and "Connect OPUS-QUAD to computer via USB (for MIDI)" (https://nowplayingapp.com/help/setup/alphatheta/opus-quad/usb/). Whether the Opus Quad's deck buttons and jogs transmit MIDI while it plays from its own SSD is **[unverified]**; the autopilot map (33 verified / 118 speculative controls incl. jog, pads, FX) is derived from the rekordbox control diagram, i.e. MIDI-control mode.
- Practical rule: for XZ/AZ (and CDJ-3000 + DJM) in standalone, Pro DJ Link is NP3's path for track/play/BPM/beat/on-air and MIDI (if the unit emits it) fills knobs. For RX3 and OPUS-QUAD (no Link to PC) the only live path is USB MIDI, and NP3 says it does not support the RX3 that way today.

**Controller-mode MIDI with rekordbox (FLX4/6/10, DDJ-1000, REV7).** Everything on the surface is on the wire: play/cue/sync/master, pads in every pad mode, loop in/out/exit/half/double, beat jump, FX select/on/level/beats, colour FX knob, EQ, trim, faders, crossfader, jog touch + two relative rotation streams. Not on the wire: anything rekordbox computes (position, beat phase, BPM, loop size in beats, which hot cue exists). The DDJ-1000 map has 41 verified controls incl. "Scratch", "Pitch Bend", "Touch", "Tempo Control", loops; the REV7 map is thin (10 verified / 19 speculative) and its motorised platters' MIDI format is **[unverified]**.

### 2b. DJM mixers over USB MIDI (DJM-900NXS2, DJM-V10, DJM-A9, DJM-S7/S11)

**Always-on?** No, on the 900NXS2 you must press MIDI ON. Manual, "Operating software by MIDI interface" (https://www.novelty.fr/wp-content/uploads/downloaded/downloads/materiel_manuels/pioneer_djm-900nxs2_manual_EN.pdf, p.15): "This unit outputs the operation information of buttons and controls in universal MIDI format. ... 3 Press the [ON/OFF] button. Turn the MIDI function on. Transmission of the MIDI messages begin. When a fader or control is moved, a message corresponding to the position is sent. When the [ON/OFF] button is pressed again, sending of the MIDI messages is stopped. The MIDI timing clock (BPM information) is sent regardless of the [ON/OFF] button. For mobile devices, MIDI messages and MIDI timing clock is sent constantly." Utility: "MIDI CH 1* to 16 — Sets the MIDI channel. BUTTON TYPE TOGGLE*, TRIGGER". The DJM-V10 manual (https://www.manualslib.com/manual/1824795/Pioneer-Dj-Djm-V10.html) says the same for its [MIDI ON] and [MIDI START/STOP (WAKE UP)] buttons and "The tempo (BPM) of the track is sent as a MIDI timing clock (output range: 40 to 250 BPM)". So for an overlay: the DJ has to switch MIDI on, and the mixer's BPM is available as **MIDI clock** even when they don't (NP3's MIDI Clock feature already "follows that clock" if "a drum machine or DJ mixer that outputs clock" is present: https://nowplayingapp.com/help/reference/integrations/midi-clock/).

**What the lists expose.** The 900NXS list (older NXS page shown on manualslib p.20, https://www.manualslib.com/manual/1056089/Pioneer-Djm-900nxs.html?page=20) is all "VR 0–127": TRIM, HI, MID, LOW, COLOR, channel fader, crossfader, master, booth, headphones, cue buttons (0/127), crossfader assign switch (0/64/127), fader curve, beat FX AUTO/TAP, beat FX type/time/level. The autopilot DJM-900NXS2 and DJM-A9 maps agree on numbers: ch1, trim CC 1, HI 2, MID 3, LOW 4, COLOR 5, faders CC 17–20, crossfader 11, master 24, headphones 26/27, with the A9 description "Sound Color FX knob (0=min, 64=center, 127=max)". Everything is **7-bit**; the NXS list shows an "MSB" column but LSB "—". The NXS2 MIDI addendum lives behind the AlphaTheta help centre (https://support.alphatheta.com/en-US/articles/4404624192665, 403 to fetchers). DJM-V10: no public list found; the autopilot map has just 7 entries (channel faders CC 17–20 plus CC 109/110 for ch 5–6, crossfader CC 11) and is marked speculative — its 4-band EQ, isolator, send/return and compressor numbers are **unknown here**. DJM-S11 (battle mixer for Serato): jog touch Note 54 and "Scratch" CC 65 per deck (the S11 forwards the attached turntable's platter? no — these are its own pad/strip controls **[unverified]**), channel faders CC 19/20, crossfader ch7 CC 31, loop and sync buttons, 18 verified / 31 speculative; diagram https://cdn.rekordbox.com/files/20201016104516/DJM-S11_Hardware_Diagram_en.pdf. DJM-S7: 6 verified controls only.

**NP3 today.** The NP3 setup pages for DJM-V10/A9/900NXS2 list only "Link (Same PC)" and "Link (Separate PC)" guides — no MIDI guide — even though NP3 ships a MIDI map for each (https://nowplayingapp.com/help/setup/alphatheta/). Pro DJ Link from a DJM carries on-air and channel fader/crossfader state; EQ/filter/FX are MIDI-only.

### 2c. Denon DJ / Engine OS over StageLinQ (SC6000/SC5000, Prime 4/GO, X1850)

Protocol facts from the three implementations (chrisle/StageLinq `services/StateMap.ts`, `docs/statemap.md`, `docs/protocol.md`; MarByteBeep/StageLinq; icedream/go-stagelinq `value_names.go`): discovery by UDP broadcast on 51337, per-service TCP; StateMap messages are `"smaa"` + type (`0x00000000` JSON state, `0x000007d2` interval subscription) + UTF-16 state name + JSON value; the client subscribes state-by-state (`subscribeState(name, interval)`; chrisle passes interval 0). NP3's help page: "mDNS service discovery"; data read: track metadata, "file path and database key", "BPM and musical key", "Playback state (playing/paused/cued)", "Channel fader and crossfader positions", "Sync state and master deck designation", "Beat position and live tempo" via BeatInfo, artwork via FileTransfer; "event-driven rather than polling"; "Wired Ethernet is recommended" (https://nowplayingapp.com/help/reference/integrations/stagelinq/). Engine DJ desktop speaks the same protocol.

**State-map paths that exist** (union of the three code bases; `%d` = deck 1–4):

- Transport: `/Engine/Deck%d/Play` (bool), `PlayState` (int enum), `PlayStatePath`, `Track/PlayPauseLEDState`, `Track/SongLoaded`, `Track/SongAnalyzed`, `Track/TrackWasPlayed`, `Track/Bleep`.
- Tempo/sync: `CurrentBPM` (float), `Speed`, `SpeedNeutral`, `SpeedOffsetUp/Down`, `SpeedRange`, `SpeedState`, `SyncMode`, `DeckIsMaster` (chrisle maps it at `/Client/Deck%d/DeckIsMaster`), `/Engine/Master/MasterTempo`, `/Engine/Sync/Network/MasterStatus`.
- Key: `Track/CurrentKey` (string, "the one to read"), `Track/CurrentKeyIndex`, `Track/KeyLock`, plus unsubscribed `OriginalKey`, `CurrentKeyCents`.
- Track: `Track/ArtistName`, `SongName`, `TrackName`, `TrackLength` (s), `TrackBytes`, `TrackNetworkPath`, `TrackUri`, `TrackData`, `Genre`, `SampleRate`, `AlbumArt`, `SoundSwitchGuid`. No label/album/comment ("none has ever existed in any Engine build").
- Position: `Track/TrackData/PlayheadPosition`, `TrackData/TrackLength`; chrisle lists `PlayPosition`, `TrackPosition`, `SongPosition`, `PlayheadPosition`, `Scratching`, `SlipModePosition` as states that "update every few milliseconds while a deck plays" and are deliberately **not subscribed** by NP3's library.
- Loops/cues: `Track/CuePosition`, `CurrentLoopInPosition`, `CurrentLoopOutPosition`, `CurrentLoopSizeInBeats`, `LoopEnableState`, `Loop/Active`, `Loop/LoopEnabledPosition`, `Loop/LoopOutPosition`, `Loop/QuickLoop1..8`, `AutoLoopIndex`, `AutoLoopLabel%d`, `BeatJump/BeatJumpIndex`, `BeatJumpLabel%d`, `SlipModeActive`. `HotCue1..HotCue8` appear in chrisle's docs tables but not in its enum **[unverified path]**.
- Jog: only `ExternalScratchWheelTouch` (bool). **No platter rotation state.**
- Mixer: `/Mixer/CH1..4faderPosition` (float 0..1), `/Mixer/CrossfaderPosition`, `/Mixer/ChannelAssignment1..4`, `/Mixer/NumberOfChannels`, per-deck `ExternalMixerVolume` (0..1), `/Engine/Mixer/Channel%d/{PFL, Line, AutoGain}`, `/Engine/Mixer/AutoPFLDeckIndex`; `/Mixer/CH1OnAir` is mentioned once in chrisle's protocol.md **[unverified]**. **No EQ, trim, filter/sweep, FX or master-level states**, on players or on the X1850 (the X1850 publishes faders and crossfader; its EQ knobs stay local). NP3's Prime 4 guide nevertheless lists "Master volume level" **[unverified]**.
- Pads/UI: `Pads/View`, `/GUI/Decks/Deck/ActiveDeck`, `/GUI/ViewLayer/LayerB`, `/Client/Preferences/{Player, LayerA, LayerB, PlayerJogColorA/B, Profile/Application/PlayerColor1..4(A/B), SyncMode}`, `/Client/Librarian/DevicesController/{CurrentDevice, HasSDCardConnected, HasUsbDeviceConnected}`. No pad-press events.

Engine OS publishes "roughly 115 states per deck"; NP3's library subscribes to 15 per deck plus a dozen device-level ones.

**BeatInfo.** Subscribe with 8 bytes `00 00 00 04 00 00 00 00`; each packet is one snapshot for all decks: `clock` (u64 ns since device start), `deckCount`, per deck `beat` (f64, fractional, counts up), `totalBeats`, `bpm`, then per-deck sample/timeline positions (chrisle `BeatInfo.ts`). Cadence, from the MarByteBeep proof-of-concept thread (https://github.com/MarByteBeep/StageLinq/discussions/12) **[secondary]**: "Packets arrive consistently at approximately 35 milliseconds intervals (≈28–30 Hz), regardless of playback state. The clock increments by roughly 35,000,000 nanoseconds between consecutive packets." Bar and beat-in-bar are derived: `bar = floor(beat/4)+1`, `beatInBar = floor(beat%4)+1`. Not every device advertises BeatInfo; chrisle's docs say devices without it "simply never emit the event" (confirmed on SC6000 and Prime 4 per the thread).

**Denon in controller mode.** Prime 4 / SC6000 / SC Live also act as MIDI controllers for Serato, and the autopilot maps for them are the richest Denon ones (Prime 4: 23 verified / 49 speculative incl. 8 pads, pad modes, sweep FX knob, EQ on ch1, jog touch + "jog wheel turn MSB (high-resolution, 14-bit)", tempo 14-bit). In that mode you lose StageLinQ deck state (Serato owns the decks) and gain knobs via MIDI. The X1850 and LC6000 maps are **empty** (0 bindings) even though NP3 has an "X1850 — MIDI" guide ("Now Playing can read fader positions and mixer state from the X1850 via MIDI", https://nowplayingapp.com/help/setup/denon-dj/x1850/midi/).

### 2d. Serato DJ Pro

**Serato Remote (OSC over TCP).** Fully specified in `chrisle/serato-connect/docs/protocol.md` (https://github.com/chrisle/serato-connect). Bonjour `_SeratoIOSRemote._tcp` with empty TXT; Serato is the TCP *client* and opens two connections (heartbeat `/Ping` every ~10 s; control); auth is `MD5(nonce ‖ secret)` with two 32-byte secrets from the binary; after `/StreamMgmt/Pairing/Pair ... isActive=1` the remote sends `/Register/Status/<topic>` and Serato streams OSC bundles, each followed by a 16-byte sentinel. The complete topic set (verified against the arm64 binary):

- `/Status/Deck/Song/Title`, `Artist`, `Filepath` (`,is`, deck 0..3), `Song/Valid` (`,if`).
- `/Status/Deck/Playhead` `,ifff` = `(deckIndex, positionSeconds, playRate, bpm)` — "the most frequent message during playback"; `playRate` 0.0 when stopped, pitch multiplier when playing; `bpm` pitch-adjusted. Update rate: "[unknown] Maximum frequency for /Status/Deck/Playhead? Tied to audio frame rate, screen refresh, or something else?"
- `/Status/Deck/Loop/AutoLoopOn`, `BeatLength`, `LoopRollOn`, `LoopInOutPoint`, `ManualLoopIn`, `ManualLoopOn`, `ManualLoopOut`, `ManualLoopSetting`, `/Status/Deck/Slicer/Loop`.
- `/Status/Video/Deck/Mixer/Upfader` (`,if`, **1-based** deck, 0..1 linear) and `/Status/Video/Mixer/Crossfader` (`,f`, 0..1 left→right, "not centered on 0").

These are Serato's **internal** mixer values (software faders or whatever the hardware drives into them), so they work even on HID rigs. Not exposed: "Cue points, hot cues, saved loops ... Beatgrid markers ... Per-track key". The README is blunt: "The Serato Remote protocol exposes derived state (track, playhead, loop toggles, faders) — not raw hot-cue/transport button presses or EQ-knob positions, which only exist over MIDI via the desktop app's bridge." There is also an undocumented `/Status/ACI/<id>` namespace.

**NP3 today.** The help page says NP3 "does not use Serato Remote or a network protocol" and watches `_Serato_` (session files, Database V2, crates, GEOB tags), so "does not read live controller state" (https://nowplayingapp.com/help/reference/integrations/serato/). But serato-connect's `open-questions.md` refers to "`emitOscControllerState` in the desktop Serato connector" and a rescale of the crossfader "see ... the desktop Serato connector", which indicates the desktop app already consumes the OSC stream or is about to; treat the help page as lagging **[unverified]**. The documented fusion is: "Serato-branded controllers report state through MIDI the same as any other controller, so fader and EQ data flow through the MIDI Bridge." On a DDJ-REV7/REV5/FLX10 + Serato rig that gives: MIDI for knobs/pads/jog + (if OSC lands) playhead/BPM/loop from Serato + history for metadata. On a Rane Twelve/Seventy-Two or CDJ-HID rig, OSC + history is all there is.

### 2e. Native Instruments Traktor Pro + Kontrol S4 MK3 / S8 / D2 / Z2

**The hardware is not MIDI.** Mixxx's S4 MK3 mapping binds `<product protocol="hid" vendor_id="0x17cc" product_id="0x1720" usage_page="0xff01" .../>` for controls and a separate `protocol="bulk"` interface (`out_epaddr 0x03`, interface 4) for the screens (`res/controllers/Traktor Kontrol S4 MK3.hid.xml`, `.bulk.xml`). The Mixxx manual: "The S4 MK3 uses the standard HID protocol for the Buttons, Knobs, Faders and LEDs, and extends it for the motorized Jog-Wheels. The screens use a USB Bulk transfer" (https://manual.mixxx.org/2.5/pt/hardware/controllers/native_instruments_traktor_kontrol_s4_mk3) **[secondary]**. The S4 MK1 used NI's proprietary NHL protocol (handled on Linux by `snd-usb-caiaq`; Mixxx wiki). A CoreMIDI client therefore sees **nothing** from an S4 MK3 — there is no MIDI endpoint to open. NI never shipped a MIDI mode for it: "It's now an anomaly that Midi mapping is still locked off for the Kontrol S4 Mk3" (https://www.digitaldjtips.com/more-integrations-for-traktor-pro-3-3-kontrol-s3-s2-mk3-get-midi-mode/), confirmed by NI community threads in 2023–24 ("chances are very low that MIDI mode will ever be added to the S4", https://community.native-instruments.com/discussion/9022/why-does-the-s4mk3-still-not-have-midi-mode). The S2 MK3 and S3 did get MIDI mode by firmware. Z1, F1, X1 (MK2) and S4 MK2 are also HID in Mixxx; the X1 MK1 has a MIDI mapping. S8/D2/S5 are HID with screens and have a Traktor-only "MIDI mode" that NI documents for the S8/D2 **[unverified]**. NP3's setup pages for every NI product list the same generic "Rekordbox, Serato, Traktor, djay Pro, VirtualDJ" guides and the S4 MK3 Traktor guide only promises that onboarding "will show whether USB MIDI is available for capturing fader and knob data" (https://nowplayingapp.com/help/setup/native-instruments/s4-mk3/traktor/) — on an S4 MK3 it will not be.

The S4 MK3 HID data is rich if someone wrote an HID bridge: Mixxx parses report 1 (buttons, bits), report 2 (pots/faders as 16-bit fields; tempo "Value range is 0..4096, but we only get 510 steps"), report 3 (per wheel: a 32-bit microsecond timer at byte 8/36 and a 32-bit position at byte 12/40; `wheelAbsoluteMax = 2879`, i.e. 2880 positions per revolution; motor torque is written back on report 49 from a 1 ms timer).

**What Traktor itself can output.**
- Broadcast: an Ogg Vorbis Icecast-style stream whose Vorbis comments carry title/artist/album/genre/BPM; NP3 listens on 127.0.0.1:8000 and discards the audio (https://nowplayingapp.com/help/reference/integrations/traktor/: "The broadcast stream reports track metadata only. Controller state (faders, EQ, crossfader) is not in the stream."; https://github.com/chrisle/traktor-connect). Duration comes from the stream header.
- MIDI clock out and Ableton Link (Traktor Pro 3/4). No native OSC was found for Traktor Pro 4 **[searched, none found]**.
- Controller Manager "Out" assignments to a virtual port: NI's manual says the Out-Port can be "a virtual MIDI port if you use this for software MIDI routing between two applications on the same computer", and "Add Out…" offers categories such as Deck Common ▸ Loop ▸ Loop Active On, Transport ▸ Play/Pause, Mixer, FX Unit (https://docs.native-instruments.com/online-guides/traktor-pro-manual/en/configuring-midi-controller-for-controlling-traktor). This is a **viable tap**: a user-installed TSI that emits Play/Pause, Cue, Loop Active, Sync, Deck Volume, Filter, EQ, Crossfader and tempo as 7-bit CC/Note on an IAC bus, which the MIDI Bridge sees like any controller. Caveats: it is opt-in per user (a `.tsi` to distribute), Traktor only sends on change, continuous outs are 7-bit, NI documents Out controls as "LED states ... for visual feedback" so continuous-value emission for faders should be confirmed on a real install **[unverified but widely used in community mappings]**, and NP3 would need a "Traktor virtual device" mapping. Jog rotation and pads are not exposed as Out controls in a useful form.

### 2f. VirtualDJ, djay Pro, DJUCED, Mixxx

- **VirtualDJ.** NP3: default "Watches VirtualDJ's M3U history files" (post-hoc, "there is no real-time deck state"); optional "Network Control" mode "Polls the Network Control plugin over HTTP" every second for all four decks with "sub-second" latency, adding album/genre/key/deck/audible deck (https://nowplayingapp.com/help/reference/integrations/virtualdj/). Beyond NP3: **OS2L** (Open Sound-to-Light, https://os2l.org/) — VDJ discovers `_os2l._tcp` and pushes JSON over TCP: `{"evt":"beat","change":false,"pos":42,"bpm":120.0,"strength":...}` on every beat, `{"evt":"btn","name":"...","state":"on"}` for mapped buttons, `{"evt":"cmd","id":42,"param":100.0}` for mapped knobs 0–100; nothing about track time, deck state or faders unless the DJ maps them to `cmd`s via VDJScript (QLC+ docs: "OS2L sends an update every beat so you have no idea of the exact track time", https://docs.qlcplus.org/v4/plugins/os2l). VDJScript can also emit arbitrary MIDI to a virtual port (`send_midi`-style actions) **[unverified detail]**. Any MIDI controller used with VDJ is visible to the MIDI Bridge as usual.
- **djay Pro.** NP3 polls `MediaLibrary.db` (mtime, ≥2 s) and gets title/artist/album/duration/path/ISRC/streaming source, "deck number, and playback position" but "djay Pro does not expose channel fader or EQ state in the library database" (https://nowplayingapp.com/help/reference/integrations/djay/). djay's only sync output is Ableton Link (no MIDI clock; Algoriddim community threads) and NP3's Link integration is **send-only** ("Now Playing pushes BPM to Link peers; it does not pull tempo from them", https://nowplayingapp.com/help/reference/integrations/ableton-link/), so no beat phase from djay today. A controller under djay is MIDI-visible.
- **DJUCED.** NP3 watches `~/Documents/DJUCED/playing.txt` written with the `%TI% | %DE% | %AR% | %AL% | %FL%` template, with `fs.watch` plus polling and a 2 s settle delay (https://nowplayingapp.com/help/reference/integrations/djuced/). Deck attribution yes, no transport/mixer. Hercules controllers are MIDI.
- **Mixxx.** NP3 polls `mixxxdb.sqlite` every 10 s for the year-bucketed played-tracks playlist; "Mixxx does not expose a live 'currently playing' deck signal" and "there is no deck channel attribution" (https://nowplayingapp.com/help/reference/integrations/mixxx/). Mixxx has no MIDI clock out (Launchpad blueprint `midi-beat-clock`; Arduino workaround https://github.com/apmiller108/mixxx_midi_clock) and cannot route MIDI output to arbitrary ports — "none of the mixxx midi ports will accept manual connections", each controller has "an isolated Javascript engine dedicated to it", unresolved (https://bugs.launchpad.net/mixxx/+bug/1131460, GitHub #6925). A mapping script can still `midi.sendShortMsg` to its *own* controller's out port, and a loopback device could be configured as that controller; clunky. The Mixxx `res/controllers` tree is nonetheless the best public reference for Pioneer/Denon/Numark/NI message formats.

### 2g. HID controllers generally

HID devices never appear in CoreMIDI, so the MIDI Bridge cannot see them. Serato's HID-mode list (https://support.serato.com/hc/en-us/articles/115002472573-Using-Serato-DJ-CDJ-s-Media-players-with-HID-mode, quoted via search snippet **[secondary]**): "Pioneer DJ CDJ-3000, CDJ-850, CDJ-900, CDJ-900NXS, CDJ-2000, CDJ-2000NXS, CDJ-2000NXS2, XDJ-1000, Numark NDX-500, Denon DJ SC5000 Prime, SC5000M, SC6000 Prime, SC6000M, Rane Twelve, and Rane Twelve mkII." CDJ-3000 HID for Serato arrived in 2021 (https://djtechtools.com/2021/10/01/pioneer-djs-cdj-3000s-become-usb-hid-compatible-for-serato-dj-pro/). CDJs do also present a MIDI interface (NP3 ships CDJ-2000NXS2 and CDJ-3000 maps: play Note 0, cue Note 1, jog "touch surface speed" CC 16 centred 64, tempo CC 29 7-bit, hot cues Notes 27–34); which interface is active depends on the player's control mode and the software **[unverified]**. Mixxx's `Pioneer CDJ HID` mapping reads the CDJ HID report: `jog_wheel` as a signed 16-bit field at byte 14, `jog_touch` bit, pitch slider, with `scratchintervalsPerRev = 2048`. Rane Twelve/Twelve MKII are HID-only to Serato (the Twelve MKII additionally advertises "DVS/USB MIDI control for Serato DJ Pro, Traktor and Virtual DJ" — i.e. a MIDI mode exists **[secondary]**). The Rane Seventy-Two / Seventy-Two MKII mixers are described as USB class-compliant audio and MIDI; the Full Compass datasheet text I extracted confirms dual USB and the TWELVE controller inputs but not the MIDI line **[unverified]**, and autopilot-mappings' `rane-seventy-two-mkii.map` and `rane-twelve-mkii.map` are **empty**. Traktor Kontrol S2/S3/S4 MK2/MK3, Z1, Z2, F1, X1 MK2, S5, S8, D2 are HID (Mixxx has `.hid.xml` for S2 MK1–3, S3, S4 MK2/MK3, Z1, F1, MX2). Numark NS7/V7 and Hercules consoles are MIDI (Mixxx `.midi.xml`), some Hercules units have both.

---

## 3. Timing and resolution facts for gesture recognition

- **MIDI 1.0 serial**: 31.25 kbaud ±1 %, 10-bit frames → 320 µs per byte, 960 µs per 3-byte message (Cornell ECE 4760 MIDI spec summary, https://people.ece.cornell.edu/land/courses/ece4760/FinalProjects/s2000/selan/midi.html). Running status trims repeated CCs to 2 bytes (640 µs). This only bounds DIN-MIDI; every device here is USB.
- **USB-MIDI**: full-speed USB frames are 1 ms, so a class-compliant controller delivers at most one interrupt transfer per millisecond per endpoint (each transfer can carry several 4-byte USB-MIDI event packets); high-speed devices can be polled every 125 µs ("USB 2.0 polls devices for MIDI data eight times per millisecond, whereas version 1.1 polls once every millisecond", LAU list, https://lists.linuxaudio.org/archives/linux-audio-user/2018-June/110091.html). Effective cadence for Pioneer gear is therefore ≤ 1 kHz per endpoint; CoreMIDI timestamps are per packet.
- **USB HID**: the interrupt endpoint's `bInterval` is in ms for full-speed and `2^(bInterval−1) × 125 µs` for high-speed; hosts may poll faster ("up to every millisecond") (https://at.or.at/hans/research/nime/hid/usbhid.html). The S4 MK3's own descriptors were not inspected here; Mixxx's motor loop runs on a 1 ms timer and the wheel report carries its own µs timestamp, which is the right thing to use for velocity instead of host arrival time **[report interval unverified, assume 1 ms]**.
- **Jog resolution** (Mixxx `intervalsPerRev` arguments, which are the ticks per revolution the controller emits): Pioneer CDJ HID 2048; DDJ-SX 2048; DDJ-400 / DDJ-FLX4 / DDJ-SB3 720; DDJ-200 128; Denon DN-SC2000 2048, DN-HS5500 1480, MC7000 894, MC4000 605; Numark Mixtrack Platinum 1240, Mixtrack 3 1200, Mixtrack 2/Pro 600, V7 (motorised) 37056; S4 MK3 2880 absolute positions. At 33⅓ rpm (0.556 rev/s) a 720-tick platter produces 400 ticks/s and a 2048-tick one 1138 ticks/s. Because Pioneer sends a **signed delta per message** (0x40 ± n, |n| ≤ 63), the message rate is bounded by the USB poll, not the tick rate: at steady play you see one CC per poll carrying a delta of 0–2; a hard backspin (say 3 rev/s on a 2048-tick platter ≈ 6000 ticks/s) shows up as deltas of ~6 per 1 ms message, so the *value*, not the *count*, is the velocity signal. A 0.5 s backspin is therefore on the order of a few hundred CCs, and the stop/reverse edge is visible as the sign flip around 0x40 **[estimates from the above numbers]**. DDJ-1000/FLX10 ticks-per-rev is not published; the FLX10 note should measure it.
- **Fader throw**: a 7-bit fader emits ≤ 128 distinct values per full throw (one CC per changed value; a fast 150 ms cut produces 20–60 messages because values skip); a 14-bit Pioneer pair emits two CCs per step and up to 16384 steps, so the FLX10 can emit several hundred messages during the same cut. StageLinQ fader floats and Serato Upfader floats are event-driven on change with no documented rate limit. NP3's measured `np:mix` cadence with the FLX10 was a median of ~0.3 s between controller-driven updates with ~45 ms latency and duplicated states (project measurement 2026-10-05, see `np3_platform_and_flx10_midi.md`), i.e. NP3 currently decimates heavily on the way to themes.
- **StageLinQ**: StateMap is change-driven (position states "update every few milliseconds"); BeatInfo ≈ every 35 ms (≈28.6 Hz) regardless of play state **[secondary]**; `clock` is a device-local ns counter, so cross-device alignment needs the TimeSync service.
- **Serato Remote**: `/Status/Deck/Playhead` is "the most frequent message during playback", rate unknown; `/Ping` every ~10 s; the library replies within ~1 ms.
- **OS2L**: one `beat` event per beat (0.5 s at 120 BPM). **Ableton Link** (djay): continuous phase, but NP3 does not receive it.
- **Serial-order caveat for 14-bit**: Pioneer sends MSB then LSB as separate CCs; a bridge that forwards each CC independently will show a saw-tooth (MSB jumps, LSB fills in). Pair them by (channel, number, number+32) before publishing.

---

## 4. Universal vs ecosystem-specific gestures, and a capability model

### 4.1 What is detectable where

| Gesture family | MIDI controller/mixer (FLX, DDJ, XDJ MIDI, DJM, Prime-as-controller) | Pro DJ Link (CDJ/XDJ/DJM) | StageLinQ (Denon) | Serato Remote OSC | Traktor broadcast | History/DB (VDJ, djay, DJUCED, Mixxx) |
|---|---|---|---|---|---|---|
| Play / pause / cue press | yes (edge, hold) | play state | `Play`/`PlayState` | `playRate` ≠ 0 | no | no (djay: position) |
| Fader cut, crossfader cut | yes | fader + XF position | yes (float) | yes (float) | no | no |
| EQ kill / sweep, filter sweep | yes | no | **no** | **no** | no | no |
| Trim / gain | yes (FLX10 14-bit) | no | no | no | no | no |
| Jog touch | yes | no | `ExternalScratchWheelTouch` | no | no | no |
| Scratch / backspin / nudge | yes (relative ticks) | no | **no** | **no** | no | no |
| Hot cue hits / juggling | yes (pad notes) | no | **[unverified]** `HotCue%d` | no | no | no |
| Loop set / exit / roll | yes (buttons only) | loop state | yes (positions, size, active) | yes (auto/manual/roll, beats) | no | no |
| Beat jump, slicer, sampler, pad FX | yes | no | beat-jump index only | slicer loop flag | no | no |
| Stems mute/solo | pad notes (FLX6-GT/FLX10/AZ/OPUS) | no | no | no | no | no |
| Beat FX / colour FX type, on, level | yes (DJM, XDJ, DDJ) | no | no | no | no | no |
| Tempo slider, range, sync, master | yes (14-bit on most Pioneer) | BPM, sync, master | `Speed`, `SyncMode`, `DeckIsMaster`, `MasterTempo` | `bpm` | BPM tag | BPM |
| Position / remaining / beat phase | no | yes (beat grid + beat packets) | position (unsubscribed), BeatInfo phase | position seconds, no length | no | djay position (2 s) |
| Track identity / key / duration | no | yes | yes | title/artist/path | title/artist/album/genre | yes |
| On-air | derived from faders | native | derived from faders (+ `CH1OnAir` [unverified]) | derived | no | no |

Universal in the strong sense (every live path has it): **play state, which channel is loud (fader/crossfader), BPM, and track change**. Universal in the weak sense (every *controller* path has it): button edges and 7-bit knobs. Ecosystem-specific: jog motion and EQ/filter (MIDI only), beat phase (Pro DJ Link, StageLinQ BeatInfo, OS2L), loop geometry (StageLinQ, Serato), stems (pads on four Pioneer units), HID rigs (nothing without a new bridge).

### 4.2 Proposed capability announcement

The host (NP3 desktop) should emit one `np:capabilities` document on connect, on any device/source change, and on request, and themes should gate moves and explain to viewers from it. Shape:

```jsonc
{
  "type": "np:capabilities",
  "version": 1,
  "generatedAt": "2026-10-06T14:00:00Z",
  "sources": [                       // every live data path currently feeding the mixer model
    { "id": "midi:ddj-flx10", "kind": "midi", "transport": "usb-midi",
      "device": "Pioneer DJ DDJ-FLX10", "mapConfidence": "verified",
      "latencyMs": 45, "maxRateHz": 1000 },
    { "id": "prodjlink", "kind": "prodjlink", "transport": "lan", "latencyMs": 30, "maxRateHz": 5 },
    { "id": "stagelinq:sc6000-1", "kind": "stagelinq", "transport": "lan",
      "services": ["StateMap", "BeatInfo"], "beatInfoHz": 28 },
    { "id": "serato:osc", "kind": "serato-remote", "transport": "tcp-osc" },
    { "id": "history:rekordbox", "kind": "history", "pollMs": 2000 }
  ],
  "global": {                        // header controls
    "crossfader":   { "present": true, "type": "bi",  "bits": 14, "source": "midi:ddj-flx10" },
    "xfAssign":     { "present": true, "type": "enum", "source": "midi:ddj-flx10" },
    "masterVolume": { "present": true, "type": "uni", "bits": 14, "source": "midi:ddj-flx10" },
    "beatFx":       { "present": true, "type": "enum+bool+uni", "types": ["echo","reverb","flanger"] },
    "masterClock":  { "present": false }
  },
  "channels": [
    { "ch": 1, "deck": "1", "device": "Pioneer DJ DDJ-FLX10", "software": "rekordbox",
      "transport":   { "play": "edge", "cue": "edge+hold", "sync": "edge", "keyLock": "bool", "slip": "bool", "reverse": "edge", "vinylMode": "bool", "quantize": "bool" },
      "jog":         { "touch": true, "platter": "rel", "ring": "rel", "search": "rel", "ticksPerRev": null, "deltaBits": 7 },
      "tempo":       { "slider": "bi", "bits": 14, "range": true, "nudge": true },
      "mixer":       { "fader": { "type": "uni", "bits": 14 }, "trim": { "bits": 14 }, "eq": "3band", "eqBits": 14,
                       "filter": true, "colorFxType": true, "pfl": true, "levelMeter": false },
      "performance": { "hotCues": 8, "hotCueSet": true, "hotCueDelete": true, "loop": ["in","out","exit","half","double","roll"],
                       "beatJump": true, "slicer": true, "sampler": true, "padFx": true, "keyboard": true, "keyShift": true,
                       "stems": ["vocal","drums","inst"] },
      "deck":        { "trackIdentity": "history:rekordbox", "position": "none", "beatPhase": "none",
                       "bpm": "track", "key": "track", "duration": "track", "loopState": "button-only" },
      "sources":     ["midi:ddj-flx10", "history:rekordbox"] },
    { "ch": 3, "deck": "A", "device": "Denon SC6000", "software": "engine-os",
      "transport":   { "play": "bool", "cue": "none", "sync": "bool", "keyLock": "bool", "slip": "bool" },
      "jog":         { "touch": true, "platter": "none", "ring": "none" },
      "tempo":       { "slider": "float", "range": true },
      "mixer":       { "fader": { "type": "uni", "bits": 32 }, "eq": "none", "filter": false, "pfl": true },
      "performance": { "hotCues": 0, "loop": ["active","size","in","out"], "beatJump": "index", "stems": [] },
      "deck":        { "trackIdentity": "stagelinq", "position": "stagelinq", "beatPhase": "beatinfo", "beatPhaseHz": 28,
                       "bpm": "live", "key": "live", "duration": "live", "loopState": "geometry" },
      "sources":     ["stagelinq:sc6000-1"] }
  ],
  "unsupported": [                    // visible devices NP3 cannot read, so the theme can say so
    { "device": "Traktor Kontrol S4 MK3", "reason": "hid-only", "hint": "Traktor Controller Manager MIDI-out to IAC bus" },
    { "device": "Rane Twelve MKII", "reason": "hid-only" }
  ]
}
```

Rules for the enum values: `"edge"` means both press and release arrive with timestamps; `"bool"` means only latched state (a cue *tap* cannot be timed); `"rel"` means signed deltas; `"none"` means absent; `bits` is the native resolution so a theme can pick thresholds (a 7-bit fader cannot distinguish a 2 % crack from noise; a 14-bit one can). `beatPhase` ∈ `"beatinfo" | "prodjlink" | "os2l" | "link" | "grid" | "none"`; `position` ∈ `"stagelinq" | "serato" | "djay-db" | "prodjlink" | "none"`. Every leaf carries, or inherits, a `source` id so the theme can show "EQ moves disabled: your SC6000 does not publish EQ over StageLinQ; connect the X1850 by USB and enable MIDI".

Companion event: `np:capabilities:changed` with a diff (`added`, `removed`, `changed` paths) when a device appears or a source drops, and a request message `np:capabilities:get` from the theme. The existing `np:mix` payload already carries `mixer.sourceId: "midi" | "simulated"`; `np:capabilities` is where the per-control truth lives so `np:mix` can stay flat.

Gesture gating table a theme can derive from it: fader cut needs `mixer.fader` (any bits); EQ kill needs `mixer.eq ≠ none` and `eqBits ≥ 7`; backspin needs `jog.platter == "rel"`; cue juggle needs `transport.cue == "edge+hold"` and `performance.hotCues ≥ 4`; drop detection on beat needs `deck.beatPhase ≠ none` or falls back to fader + BPM timing; stems combo needs `performance.stems` non-empty; perfect-sync taunt needs `deck.bpm == "live"` on both channels.

---

## 5. Likely rigs in Triode's user base

| Rig | Data path(s) NP3 has today | Taxonomy groups observable | Gaps that block moves |
|---|---|---|---|
| DDJ-FLX4 / FLX6 + rekordbox | MIDI Bridge (7-bit faders/EQ/filter, 14-bit tempo, relative jog, pads on per-mode channels) + rekordbox `master.db` history | transport, jog, tempo, per-channel mixer, global mixer, performance (incl. stems pads on FLX6-GT) | no position, no beat phase, no loop geometry; 7-bit faders make fine fader tricks noisy |
| DDJ-FLX10 + rekordbox | as above but 14-bit mixer; measured in sibling note | all MIDI groups | same deck-side gaps; NP3 decimates `np:mix` to ~3 Hz |
| DDJ-1000 + rekordbox | MIDI (41 verified / 58 speculative map) + history | transport, jog (scratch + bend), tempo, mixer, loops, pads | 7-bit; REV7-style pad modes partially mapped |
| XDJ-RX3 standalone | USB MIDI *if* the unit emits in standalone; NP3 guide says "Works with Now Playing 3: No"; no Pro DJ Link port | mixer section (7-bit), transport buttons, jog (relative), FX type/on/level, colour FX | no track identity at all for NP3 (USB-stick play); no position/phase; needs NP3 to accept XDJ-RX3 as a MIDI device |
| XDJ-XZ / XDJ-AZ standalone | Pro DJ Link (track, play, BPM, beat, on-air, faders) + USB MIDI mixer section ("Mixer MIDI Message: SEND" default) and deck buttons **[unverified in standalone]** | transport, mixer, FX, jog if deck MIDI is on, beat phase via Link, stems pads (AZ) | NP3's XZ "USB" guide marked unsupported; verify deck-section MIDI while standalone |
| XDJ-XZ/AZ + rekordbox (controller mode) | MIDI (XZ map 33 verified / 55 speculative; AZ same) + history | all MIDI groups | position/phase only if Link is also used |
| OPUS-QUAD standalone | USB MIDI + rekordbox DB per NP3 guide; no Pro DJ Link to PC | transport, mixer, FX, pads, jog **[standalone emission unverified]** | position/phase; map is 118/151 speculative |
| CDJ-3000 ×2 + DJM-V10 / A9 / 900NXS2 | Pro DJ Link for decks and mixer (faders, XF, on-air, beat, position) + DJM USB MIDI after pressing MIDI ON (7-bit trim/EQ/colour/faders/XF/FX) + DJM MIDI clock | transport state, tempo, mixer incl. EQ/filter/FX (MIDI), beat phase + position (Link) | **no jog rotation** (CDJ MIDI/HID goes to a DJ app only), no pads/hot-cue presses (Link reports cue state only); V10 4-band/isolator CC numbers unknown; DJM MIDI not always-on |
| Denon SC6000 + X1850, Prime 4 / Prime GO (Engine OS) | StageLinQ StateMap + BeatInfo (+ X1850 USB MIDI for faders per NP3; map empty) | play, sync/master, tempo (`Speed`), faders + crossfader, loop geometry, beat phase at ~28 Hz, position, key, track | **no EQ, filter, trim, FX, jog rotation, pad presses**; `HotCue%d` unverified; X1850 EQ needs a MIDI map that does not exist yet |
| Serato + Rane Seventy-Two/Twelve or DDJ-REV | Serato history files (+ Serato Remote OSC per serato-connect: playhead/playRate/bpm, loop flags, Upfader, Crossfader) + MIDI Bridge for MIDI controllers (REV5/REV7, S11) | position, play, BPM, loop state, software faders (OSC); plus full MIDI groups on MIDI rigs | Twelve/CDJ-HID rigs: no jog, no pads, no EQ; Seventy-Two MIDI map empty; OSC playhead rate unknown; help page still says file-only |
| Traktor Pro + Kontrol S4 MK3 (or S8/D2/Z2) | Traktor broadcast metadata only (+ collection DB) | track identity, BPM, duration | **everything else**: HID hardware is invisible to CoreMIDI; no NI MIDI mode; the only tap is a user-installed Controller-Manager MIDI-out TSI to an IAC bus (7-bit, change-driven) or a future HID bridge |
| VirtualDJ / djay / DJUCED / Mixxx + any MIDI controller | history/DB/text (+ VDJ Network Control, djay position) + MIDI Bridge for the controller | controller groups via MIDI; track identity; djay position; VDJ deck audibility | software-side state (loops, phase) absent; OS2L (VDJ) could add per-beat phase; djay's Link phase not received by NP3 |

### Things to verify on hardware before building moves on them

1. XDJ-XZ/AZ/RX3/OPUS deck-section MIDI while playing from USB (connect by USB, watch MIDI Monitor, press play).
2. The RX3 "CH LEVEL METER" row — if the mixer meters stream over MIDI, every XDJ/DJM user gets an audio-level signal for free.
3. DJM-V10 and DJM-A9 MIDI lists (behind the AlphaTheta help centre) for isolator/4-band/send numbers and whether MIDI ON is required on the A9.
4. StageLinQ `HotCue1..8` and `/Mixer/CH%dOnAir` existence on current Engine OS; BeatInfo cadence on Prime GO and SC Live.
5. Serato Remote `/Status/Deck/Playhead` rate, and whether NP3 desktop already consumes it (`emitOscControllerState`).
6. Traktor Controller Manager: does an Out assignment on "Deck Volume" emit CC values continuously to an IAC bus? If yes, publish a TSI.
7. DDJ-1000/FLX10 platter ticks per revolution (spin at 33⅓ for 10 s, sum the deltas).

### Source index

- NP3 help: midi-bridge, stagelinq, serato, traktor, mixxx, virtualdj, djay, djuced, ableton-link, midi-clock, theme-sdk under https://nowplayingapp.com/help/reference/integrations/; setup pages under https://nowplayingapp.com/help/setup/{alphatheta,denon-dj,native-instruments,rane}/.
- Code: https://github.com/chrisle/autopilot-mappings, https://github.com/chrisle/serato-connect (docs/protocol.md, docs/open-questions.md), https://github.com/chrisle/StageLinq (services/StateMap.ts, services/BeatInfo.ts, types/common.ts, docs/*), https://github.com/MarByteBeep/StageLinq (discussions/12), https://github.com/icedream/go-stagelinq, https://github.com/chrisle/traktor-connect, https://github.com/mixxxdj/mixxx/tree/main/res/controllers (Pioneer-DDJ-FLX4-script.js, Pioneer-CDJ-HID.js, Pioneer-DDJ-SX-scripts.js, Traktor-Kontrol-S4-MK3.js, Traktor Kontrol S4 MK3.hid.xml/.bulk.xml, Denon-MC7000-scripts.js, Numark-*).
- Manufacturer: XDJ-RX3 MIDI list https://cdn.rekordbox.com/files/20211108182410/XDJ-RX3_Hardware_Diagram_en.pdf; rekordbox diagram index https://rekordbox.com/en/support/diagram/; XDJ-XZ manual p.126 https://www.manua.ls/pioneer/xdj-xz/manual?p=126; DJM-900NXS2 manual https://www.novelty.fr/wp-content/uploads/downloaded/downloads/materiel_manuels/pioneer_djm-900nxs2_manual_EN.pdf; DJM-900NXS MIDI list https://www.manualslib.com/manual/1056089/Pioneer-Djm-900nxs.html?page=20; DJM-V10 manual https://www.manualslib.com/manual/1824795/Pioneer-Dj-Djm-V10.html; Serato HID mode https://support.serato.com/hc/en-us/articles/115002472573; Serato XDJ-XZ guide https://support.serato.com/hc/en-us/articles/360001415256; NI Controller Manager https://docs.native-instruments.com/online-guides/traktor-pro-manual/en/configuring-midi-controller-for-controlling-traktor; Mixxx S4 MK3 manual https://manual.mixxx.org/2.5/pt/hardware/controllers/native_instruments_traktor_kontrol_s4_mk3; OS2L https://os2l.org/ and https://docs.qlcplus.org/v4/plugins/os2l.
- Timing: https://people.ece.cornell.edu/land/courses/ece4760/FinalProjects/s2000/selan/midi.html; https://lists.linuxaudio.org/archives/linux-audio-user/2018-June/110091.html; https://at.or.at/hans/research/nime/hid/usbhid.html.
- Commentary: https://www.digitaldjtips.com/more-integrations-for-traktor-pro-3-3-kontrol-s3-s2-mk3-get-midi-mode/; https://community.native-instruments.com/discussion/9022/why-does-the-s4mk3-still-not-have-midi-mode; https://djtechtools.com/2021/10/01/pioneer-djs-cdj-3000s-become-usb-hid-compatible-for-serato-dj-pro/; https://bugs.launchpad.net/mixxx/+bug/1131460; https://github.com/apmiller108/mixxx_midi_clock.
