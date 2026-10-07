# Research notes index

Agent-written, sourced research. Each note marks unverified claims. Planning docs in `../docs/`
are the decision layer on top of these.

| File | Covers | Feeds |
|---|---|---|
| `visual_style_street_fighter.md` | HUD anatomy of SF2/Alpha/3S/MvC/KI with 60 fps timings, CPS hardware constraints, typography with licences, sprite production tools and AI generators, palettes, CC0 placeholders, a proposed visual bible, full asset list | `docs/04`, `docs/08` |
| `rendering_stack.md` | PixiJS 8 vs Phaser vs Canvas2D vs DOM vs three.js with measured sizes, pixel-perfect scaling, OBS/CEF facts from source (hw-accel, autoplay, DPR, frame pacing), asset pipeline and inlining math, game loop outside React, SFX, testing, folder layout, SDK asks | `docs/05`, `spike/` |
| `game_mechanics.md` | Combo/streak design precedents with numbers (SF6, KI, DMC, THPS, GH, Beat Saber, Tetris Effect), 30-move vocabulary with detection rules, combo engine with pseudo-code, Twitch EventSub/IRC/bridges and policy, health/KO loop, ranked event list | `docs/02`, `docs/03` |
| `np3_platform_and_flx10_midi.md` | NP3 public surface, architecture (Socket.IO → cloud → SSE), MIDI Bridge, mix processor presets, SDK repo history and contract, live host behaviour, full DDJ-FLX10 MIDI message list, NP3's own FLX10 map, rekordbox limits, Twitch feasibility | `docs/01`, `docs/03` |
| `prodjlink_data_model.md` | Pro DJ Link packet families and rates, CDJ-3000 status fields incl. what is absent, beat `28` and absolute position `0b`, mixer side and the Stagehand/Bridge unicast, DJM-V10 and A9 MIDI lists, alphatheta-connect decoding gaps, gesture availability matrix | `docs/06`, `docs/03` §2b |
| `hardware_ecosystems.md` | Canonical control taxonomy, NP3's 77-name vocabulary, Pioneer controllers and all-in-ones, DJM over MIDI, Denon StageLinQ state map and BeatInfo, Serato Remote OSC, Traktor HID, VDJ/djay/DJUCED/Mixxx, timing facts, capability schema, likely rigs | `docs/06` |
| `ground_truth_2026-10-06_1057.txt` | Slicer output for the first labelled gesture session | `docs/07` |
