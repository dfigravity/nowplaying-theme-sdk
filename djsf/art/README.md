# DJ Street Fighter · art (v1 + v2 asset packs)

The v1 sheets and bitmap fonts from `docs/08 Graphic design brief.md` (HUD, fonts, digits,
callouts, VS card) and the v2 escalation pack (effects, big numerals, the mascot "Wax",
portraits). All pixels are original. They come from the hand-drawn masks in
`src/glyphs.py` and the drawing code in `src/build_v1.py`. Nothing is traced, ripped or taken
from a third-party font. v1 and v2 built 2026-10-06.

## Look at it

- **Animated preview:** `preview/index.html`, served with the `djsf-art` entry in
  `_claude_DJ/.claude/launch.json` at http://localhost:5195. It's a 1920×1080 stage with the
  HUD, combo counter, callouts, specials, a super, chat hits and the VS card, plus buttons for
  every move.
  - `?obs` gives a transparent page with no controls, so it can go straight into OBS as a
    browser source.
  - `?solo` is iteration 1: DJ side only (see "Solo layout" below). Combine as `?solo&obs`.
  - `?at=N` jumps to frame N of the autoplay and holds there.
  - `H` toggles the controls.
- **Stills:** `contact/*_x3.png` and `*_x4.png` are every sheet enlarged on a checker.

## Rebuild

```bash
pip3 install pillow
python3 "art/src/build_v1.py"
python3 "art/src/build_v2.py"
```

Run v1 first. v2 imports v1's lettering helpers and then refreshes `preview/assets.js` and
`contact/` with all sheets. Together the builds rewrite `out/`, `palette/`, `contact/` and
`preview/assets.js`. Each ends with a palette audit: every opaque pixel must be a
12-bit-snapped Endesga 32 colour, with at most 15 colours per sprite (v1 223 sprites, v2 113,
0 failures). Run `dot_clean -m art` before zipping; Ceres is
exFAT.

**The source of truth is the code, not the PNGs.** To change a letter, edit its row in
`src/glyphs.py` and rebuild. There are no `.aseprite` files yet (decided 2026-10-06: Pillow now,
Aseprite only when a human wants to hand-edit pixels). The sheet JSON already uses Aseprite's
json-hash shape, so a short Aseprite Lua import can turn any sheet into an `.aseprite` file later.

## Files in `out/`

The brief's export settings apply to every sheet: 1× virtual pixels, power-of-two, 2 px shape
padding, 1 px extrude, no rotation, no trim. JSON is Aseprite json-hash (`frames`, `duration`
in ms, `meta.frameTags`, `meta.slices`). Fonts are AngelCode BMFont text `.fnt` + PNG.

| File | Size | Contents |
|---|---|---|
| `hud.png/.json` | 512×64 | `bar_frame_l/r` 148×12 · `bar_drain_00`–`07` fill widths 1–8 · `bar_drain_08`–`15` the same widths in damage-flash white · `bar_trail_1`–`8` greyscale trail (tint `#e43b44` at runtime) · `emblem_normal/flash` 32×16 "DJ" badge · `nameplate_normal/hot` 72×10 · `roundwin_empty/won` 8×8 vinyl · `meter_frame_l/r` 116×8 · `meter_seg_charge/full/flash/max` 36×4 · `max_on/off` 20×8 · `ticker_strip` 136×10 (nine-slice in `meta.slices`, stretch horizontally only) · `spark_small_0`–`2` 16×16 (tag `spark_small`) |
| `digits.png/.json` | 256×128 | `hit_0`–`9` 20×28 gold bevel numerals (advance 16 px so stacked digits overlap) · `timer_0`–`9` + `timer_colon` 10×14 chrome · `label_hits/hit/combo/pts/x` |
| `callout.png/.json` | 256×128 | `glyph_XXXX` (code point) slanted 12×16-class glyphs · rank words (set B, decided) in their tier colours: `rank_b_nice/solid/wicked/savage/lethal/maximum/ultra` · DMC-style letters `style_d/c/b/a/s/ss/sss` |
| `callout_font.fnt/.png` | 256×64 | "DJSF Strike": the callout set as a BMFont, for move names (A–Z 0–9 `! ? + x . - ' & : /`, lowercase maps to caps) |
| `font16.fnt/.png` | 256×64 | "DJSF Bold": 12 px caps, 2 px strokes, chrome bevel, navy outline + shadow, line height 16. For names, titles and banners |
| `font8.fnt/.png` | 256×64 | "DJSF Mini": 5×7 caps, white with navy outline, line height 10. Full printable ASCII plus `▶ ◀ • — × ♪`. Lowercase, curly quotes and accented Latin letters (À–ɏ) map to the base caps, so any track title renders |
| `vs.png/.json` | 512×128 | `vs_panel_l` (red, NOW) / `vs_panel_r` (blue, NEXT) 192×56 parallelograms, 28 px lean · `vs_mask_l/r` silhouettes for wipes · `vs_glyph_normal/flash` |
| **v2** `fx.png/.json` | 512×256 | tags `spark_med` 24×24 ×4 · `spark_big` 32×32 ×6 · `lightning` 32×64 ×6 (loop) · `fire_edge` 16×16 ×8 (flames rising from the bottom edge; tiles in x, loops in time; flip vertically for the top edge) · `fire_corner` 16×16 ×8 (bottom-left; mirror for the others) · `super_burst` 64×64 ×8 · `slash` 64×8 ×4 (CROSSFIRE) · `swap_arrows` 16×16 ×3 (FULL HANDOVER) · command icons 8×8 `icon_fader_up/fader_down/fader_slam/eq_kill/eq_restore/filter_up/filter_down/jog_back/pad/loop/hold/then` (`docs/10` §5) |
| **v2** `digits_big.png/.json` | 512×64 | `big_0`–`9` 40×56 gold numerals for tier 4+ (advance 32) · `big_label_hits` |
| **v2** `mascot.png/.json` | 512×512 | Wax, 64×64 frames, feet at (32, 62), faces right: tags `wax_idle` 6 (loop) · `wax_punch` 4 · `wax_super` 8 · `wax_hurt` 3 · `wax_dizzy` 4 (loop) · `wax_ko` 6 (hold last) · `wax_win` 4 (hold last) · `dizzy_record` 8×8 ×4 (orbit three around the head) |
| **v2** `portraits.png/.json` | 128×64 | 24×24 chips: `portrait_dj_idle/hype/hurt/ko` (Wax's face) · `portrait_chat_idle/hype/hurt/ko` (a speech-bubble crowd face) |
| `lut.png/.json` | 16×16 | one ramp per row (outline, highlight, face, mid, shade, deep): gold, yellow, orange, red, magenta, green, cyan, chrome, white, dim |

Palette: `palette/djsf32.gpl` (GIMP/Aseprite), `.hex`, a 32×1 PNG and a swatch.

## Conventions the engine relies on

- **Palette swaps, not tints**, for anything gold. Every gold sprite (numerals, callout glyphs,
  bar fill, labels) uses exactly the five gold ramp colours plus outline `#112`. Escalation maps
  them onto another `lut.json` row by exact colour match. The preview does this in
  `sheetFor()`; a Pixi version is a small colour-map filter.
- **White fonts are tinted.** `font8` and `font16` are white/chrome, so they're multiplied by a
  colour at runtime, skipping the navy outline.
- **Outline is `#111122`** (Endesga `#181425` snapped), never black. Every sprite has it, so it
  reads over a bright wall as well as a dark room (checked in the preview).
- **Text advances** are body width + 1, so neighbouring glyph outlines share a column. Draw a
  line of text left to right.
- **Health fill:** whole tiles of `bar_drain_07`, then one partial tile. The tiles are 8 px
  wide with an 8 px stripe period, so the sheen stays continuous. For the right-hand bar, mirror
  the draw.

## Layout used in the preview (virtual px)

These follow `docs/04` §2, with one change: the **combo block sits at y 44**, not 60. At y 60 the
rank word landed on top of the callout lane at y 104.

| Element | Position |
|---|---|
| bar frames | x 10 / 226, y 8 (fill area x 12–156 / 228–372, y 10) |
| emblem | x 176, y 3 · timer digits x 182 and 192, y 20 |
| name plates | x 12 / 300 (P2 mirrored), y 20 · style letter x 88, y 20 · round markers x 136/146 and 240/230, y 21 |
| combo block | x 20, y 44; numerals every 16 px; `label_hits` after the last digit; rank word at y + 30 |
| callouts | centred x 96 (P1) / 288 (chat), baseline lane y 96, pushed down 18 px per newer callout, max 3 |
| HYPE meters | x 8 / 260, y 198; label and MAX at y 188 |
| ticker | x 124, y 205 · VS card band y 80, panels meet at x 12 + 164 |
| **v2** portraits | x 2 / 358, y 20. Name plates moved right to x 28 / 284 to make room, and the style letter to x 102 |
| **v2** combo block | y 48 (below the portraits). From tier 4 (15 hits) the numerals are `big_*` and the HITS label and rank word sit to the right; the callout lane drops from y 104 to y 124 so it stays clear |
| **v2** mascot | frame at x 0, y 124 (body x 8–56, feet on y 186, above the HYPE label) |
| **v2** fire border | bottom row of `fire_edge` at y 200 behind the HUD, corners at both ends; the top row (flipped) only at tier 6 |

## Solo layout (iteration 1, `?solo`)

Triode, 2026-10-06: iteration 1 is one side only, no PvP. The preview's `?solo` mode is the
proposed HUD for it. It needs no new art; it reuses v1/v2 sprites.

| Element | Solo treatment |
|---|---|
| Top-left bar | The **HYPE bar**: `bar_frame_l` filled with gold `bar_drain_*` tiles from the screen edge toward the centre. Newly gained HYPE flashes white for 6 frames. At full, it alternates magenta/white, with `max_on/off` at x 146, y 21. During the super it drains over 8 bars, flickering yellow/orange, with "x2". "HYPE" sits in the empty end of the well (`font8`, `#0099db`) |
| Centre | Emblem as before; the timer digits show the on-air **BPM** (three `timer_*` digits centred on x 192), with "BPM" in `font8` below. NP3 sends no playback position, so a track countdown would be a guess |
| Kept | DJ portrait, name plate, style letter, combo block, callouts, Wax, ticker, VS card, all escalation effects |
| Removed | Chat bar, chat portrait, both bottom meters (HYPE moved up), round markers, K.O. Wax drops to y 150 (feet on y 212) |
| Right half | Empty; the camera is clearer. The iteration-2 opponent arrives here |

## Motion implemented in the preview (60 fps fixed step)

- Callout pop: 3×, then 2×, both white, then 1× with a 2 px overshoot. Pop scale is capped so
  the word fits in 376 px.
- Hold 36 frames, slide 24 px, then alpha 100 → 50 → 0.
- Hit-stop freezes the HUD: 6 frames for a move, 10 for a special, 14 for a super. Only the pop
  of the thing that just landed keeps playing.
- Numeral slam (1 frame at 2×, white). Tier recolours: gold → yellow (6) → orange (10) → red (25)
  → rainbow (40). Shake of 1/2/3 px.
- Drop: wobble, then a 32 px fall with a 2-step bounce over 12 frames, then the bank summary.
- Health: whole-pixel drain, red trail decaying 1 px every 4 frames, 2 frames of white flash,
  red low-health blink under 25 %.
- HYPE: 3 segments, MAX blinking 8 frames on / 8 off, ×2 while active.
- Super: 14 frames of freeze, 60 % darken, bars white, `SUPER!` then `HYPER <special>!`, 12 sparks.
- VS card: stepped wipe in, VS glyph pop and flash, hold, wipe out.
- **v2 escalation:**
  - Tier 2 (6 hits): `spark_med` on each callout.
  - Tier 3 (10): looping lightning behind the numerals.
  - Tier 4 (15): big numerals plus the fire border along the bottom.
  - Tier 5 (25): red numerals, and the chat portrait turns scared.
  - Tier 6 (40): rainbow numerals, fire top and bottom, and lightning on the chat side too.
- **v2 super:** `super_burst` at the callout, 12 medium and big sparks, Wax's super pose, both
  portraits change mood.
- **v2 mascot reactions:**
  - Every move triggers the punch, starting on the extended frame so hit-stop holds the fist
    out.
  - A chat hit triggers hurt. A big hit (≥ 14 px) makes him dizzy for 150 frames, with orbiting
    records.
  - A KO makes him fall; when chat is knocked out, he plays the win pose.
  - The "K.O.!" callout plays, then the round resets after 5 s.
- **v2 specials:** CROSSFIRE draws three staggered slashes, FULL HANDOVER spins the swap
  arrows, and the other specials burst `spark_big` on the chat bar.
- Extra demo buttons: Jump to 39 hits (shows tier 6), DJ K.O., Chat K.O.

The preview is plain Canvas2D so it needs nothing installed. It is a motion reference for the
engine session, not the engine.

## Not in v1, deliberately

- **Rank words:** set B, chosen 2026-10-06, baked as sprites in the callout style. They are
  16 px tall, not 12: the callout face is the announcer voice.
- **No separate trail tile:** the brief asks for one trail tile. There are eight widths
  (`bar_trail_1`–`8`) so a partial trail tile never has to be cropped.
- **v3 sheets** (`chat`, `banners`, `mascot2`) and the super cut-in panel (`docs/10` §6) are
  not started.
- **Mascot frames are 64×64, not 48×64.** At 48 wide the KO fall and the straight punch clip.
  Engine anchor: feet at (32, 62).
- **Command icons are in `fx`, not `hud`.** That keeps the v1 sheets unchanged.
- **Wax is drawn by a joint skeleton** (`src/mascot.py`): each pose is a set of joint
  positions, and `Figure` in `px.py` shades, seams and outlines the parts. To re-pose a frame,
  move a joint. A pixel artist can later redraw over the PNGs if hand polish is wanted.

## Decisions still open that touch the art

P1 name (the plate prints any string; the preview uses OSH) · whether P1
health anchors at the screen edge or the centre (toggle in the preview) · approval of Wax as
drawn (colours: purple hoodie, blue jeans, red label eye) · timer
semantics (the digits work either way) · which specials to keep (`docs/10` §7).
