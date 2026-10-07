# 07 · Gesture ground truth (labelled session 2026-10-06 10:57–11:01)

Osh labelled each gesture on the tap page, then performed it on the DDJ-FLX10 while the raw MIDI tap
and the Protocol Spy overlay both wrote into one recorder file. This is the first labelled dataset for
Triode's recognisers and our matchers.

- Recording (raw MIDI batches + markers + `np:mix` states): `recordings/np3-2026-10-06_105733.jsonl`
  (copy of `../Now Playing 3 Overlays/recordings/np3-2026-10-06_105733.jsonl`, 4.5 MB)
- Slicer output: `research_notes/ground_truth_2026-10-06_1057.txt`
- Reproduce: `python3 tools/slice_markers.py recordings/np3-2026-10-06_105733.jsonl --window 8`
- FLX10 MIDI: deck channels 1–4; platter CC 34 (vinyl on) relative around 0x40; wheel side CC 33;
  touch Note 54; channel fader CC 19/51; EQ CC 7/11/15 (+32 LSB); crossfader ch7 CC 31/63; Beat FX
  level ch5 CC 2/34.

## Signatures (raw MIDI) vs. what NP3 emitted

| Label | Raw MIDI in the window | What NP3's state stream showed | Recogniser signature |
|---|---|---|---|
| quick cut (done on the crossfader) | crossfader 596 MSB msgs over 5.9 s, full travel 0↔127, ~100 msgs/s | 22 states | crossfader MSB passes 0.1 and 0.9 within one bar |
| fader slam (both decks) | deck1 fader 391 msgs / 5.0 s, deck2 372 msgs / 6.0 s, full travel | 12 states; ch1 1→0, ch2 0→1 | fader MSB 0→≥100 in ≤ 250 ms (the throw itself is 20–60 msgs) |
| bassline swap | deck2 eqLow 158 msgs, deck1 eqLow 101 msgs | 14 states; ch1 low 0→−1, ch2 low −1→−0.03 | low on A crosses −0.5 downward while low on B crosses −0.5 upward within 2 bars |
| vocal swap | deck1 eqMid 226, deck2 eqMid 192 | 18 states; ch1 mid −1→−0.05, ch2 mid −0.03→−1 | mirror on mid |
| eq kill sweep | deck2 eqHigh 280, eqLow 278, deck1 eqMid 117, eqLow 107, deck2 eqMid 103 (1,770 msgs) | 67 states (busiest window, ≈ 8 states/s incl. triplicates) | all three bands ≤ −0.8 then restored L→M→H within 2 bars |
| **nudge** (platter edge) | deck2 **ring 3,552 msgs over 7.0 s at 504/s**, ticks −23,273, peak |delta| 25, mostly backward | **0 states** | ring ticks with |delta| ≤ ~25 for > 0.5 s while touch is off |
| crossfader slam | crossfader 570 msgs / 6.3 s, 0→127→64 | 32 states | as quick cut, in ≤ 1 beat |
| echo out | Beat FX level ch5 175 msg pairs; deck1 play once | 4 states (play edge only) | `fx.level` rising/held while deck fader drops; FX type and on/off are Notes on ch5 |
| **backspin** | deck2 **touch on; platter 87 msgs in 86 ms at 1,012/s, ticks −4,276, every delta negative, peak −63 (saturated)**; then touch off and **ring 3,051 msgs over 3.05 s, all negative, peak −63** (the platter free-spinning after release) | **2 states** (touch on, touch off) | touch on → ≥ 50 ms of platter deltas ≤ −30 → touch off → decaying negative ring ticks. Duration and peak speed come from the ticks; the free spin after release is the "tail" |

Everything the engine needs for Backspin, Scratch, Nudge and Vinyl Brake is in the platter/ring
streams at 1 kHz, and none of it survives into `np:mix`. The EQ and fader gestures survive as
threshold crossings only.

## Observations worth passing to Triode

1. During a backspin the FLX10 saturates the platter delta at −63 for the whole burst (87 ms here), so velocity above ~63 ticks/ms is not resolvable; the recogniser should use burst duration × saturation rather than peak value for "how hard".
2. After release the FLX10 reports the free-spinning platter on the **wheel-side CC 33**, not the platter CC 34, because touch is off. A recogniser must treat ring ticks immediately after a touch-off as the backspin tail, not as a nudge.
3. The ring runs at exactly 1 message per ms for seconds at a time (3,051 msgs in 3,050 ms). Any path that forwards raw jog ticks will be swamped; coalesce per 10–30 ms with summed ticks and peak delta, or emit gestures.
4. A full fader throw is 20–60 MSB messages; today's state stream shows one or two values of it. Per-control coalescing with `{min, max, last, crossings}` per emission window would preserve the throw without raising the rate.
5. `np:mix` arrived up to ~8 messages/s in the busiest window (67 in 8 s), of which about a third are unique: the cap is closer to 3 unique states per second under load than 10.

## Not yet labelled (next session)

transformer chop · full kill · high duck · the drop · filter riser / wobble (COLOR knob, unmapped) ·
scratch (alternating platter) · vinyl brake · hot cue juggle (pads ch 10) · loop roll · beat jump ·
stem drop (Notes 13/14/15) · trim boost · cue stutter · long blend · clean transition · idle.
