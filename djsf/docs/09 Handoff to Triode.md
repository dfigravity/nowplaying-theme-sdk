# 09 · Handoff to Triode (cover note)

Hi Chris. This folder is the result of two days of measuring NP3 from the theme side and planning
the Street Fighter theme against what we found. Nothing here is a demand; it is what we would need,
ranked, with evidence, so you can decide what is cheap and what is not.

## Read in this order

1. **`03 Event protocol proposal.md`** (20 min): the `np:event` envelope, twelve ranked events with
   the FLX10 MIDI behind each, how the same events arise on CDJ/DJM/Denon/Serato rigs,
   `np:capabilities`, `np:community`, and twelve SDK/host asks.
2. **`06 Hardware matrix and data-path limits.md`** §A and §A2 (10 min): the measured decimation.
   22,096 raw MIDI messages became 38 distinct states in three minutes; values are about 60 ms
   fresh, so the timer sits before or at state assembly on the desktop → cloud leg. Where is it,
   and can it become per-control coalescing?
3. **`07 Gesture ground truth.md`** (5 min) and `recordings/np3-2026-10-06_105733.jsonl`: nine
   labelled gestures with raw MIDI, markers and your `np:mix` states in one file. The backspin and
   nudge rows are the ones that matter for recognisers. `tools/slice_markers.py` reproduces the
   tables.
4. **`sdk-assets-and-dynamic-imports.patch`**: two one-line fixes without which any sprite theme
   fails to build (image imports in `theme-meta.mjs`; `inlineDynamicImports` in the bundle Vite
   config). `spike/` is the Pixi 8 theme that proved it.
5. Background if useful: `01` (what reaches a theme today), `research_notes/prodjlink_data_model.md`
   (your alphatheta-connect against dysentery/beat-link: the `0b` offset question, unparsed `28`
   packets), `research_notes/hardware_ecosystems.md` (StageLinQ, Serato OSC, Traktor HID,
   the 77-name control vocabulary from autopilot-mappings).

## What we are asking, shortest form

- Named gesture events with timestamps at packet receive; coalesced continuous values; `np:mix`
  kept for late joiners; gated by `meta.subscriptions`.
- `np:capabilities` per channel so one theme serves every rig honestly.
- The two SDK patches; confirmation that `public/` files can ship and that `entry.js` is compressed.
- `np:options` and `np:visibility`.
- Community events (`np:community`) if in scope; your bot-in-channel approach from the Check-In
  globe covers cheers, subs, gifts and raids without broadcaster scopes.
- Mapping fixes: FLX10 platter (CC 34/35) and COLOR knobs (ch7 CC 23–26); DJM-V10 map from the
  official list; X1850 and Seventy-Two maps.
- Pro DJ Link library: parse `28` and `29`, decode P_2/P_3/loop/key-shift fields, verify `0b`
  offsets; subscribe StageLinQ position states.

## What we are offering

- The theme as a real consumer that exercises every event you emit, with replay fixtures from the
  recordings.
- SDK pull requests: the patches above, protocol types, shared hooks (`useMixState` exists;
  `useEvents`, `useCommunity` next), the sidecar fix already sent.
- More labelled sessions on request (the remaining gesture list is at the end of `07`), and the
  tap tooling if you want to measure the decimation from your side.

## Questions

The full, numbered list across design, functionality, platform and workflow is
**`11 Questions for Triode.md`**; answer by number there or in Discord. The four below are the
protocol ones and are repeated in it.

1. The full `mix-processor:update` schema.
2. Whether per-channel `track` is populated for rekordbox + FLX10 in all cases.
3. Where you want gesture recognition: desktop app, mix processor, or SDK-side on raw events. Our
   vote: desktop or mix processor emits gestures; the SDK ships the same recogniser for the
   playground.
4. Which events are cheap for you this month, so we can sequence the theme around them.
