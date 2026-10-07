# 04 · Visual bible and asset list (v0.1, 2026-10-06)

Evidence and sources: `research_notes/visual_style_street_fighter.md`. Several reference facts there
are marked [FROM MEMORY] or [UNVERIFIED] because the fan wikis were bot-walled; they are good enough
to design against and must be checked on 60 fps footage before they become frame-exact specs.

## 1. Rules

- **Idiom, not assets.** Two bars growing inward, centre emblem and timer, stacked hit numerals,
  slanted callouts, hit sparks, hit-stop freeze, super flash. No Capcom sprites, HUD art, ripped fonts,
  logos, "KO" emblem art, character names or likenesses. Our own words for every banner.
- **Virtual CRT 384×216, integer scale 5 → 1920×1080.** Everything authored in virtual pixels;
  no sub-pixel positions, no fractional scales, no rotation except 90°. OBS browser source created
  at exactly 1920×1080 and never resized.
- **Palette:** Endesga 32 snapped to 12-bit (channels in 0x11 steps); ≤ 15 colours + transparency per
  sprite, like a CPS palette slot. Outlines are dark navy `#181425`, never pure black (reads as a hole over camera).
- **No full-frame CRT/scanline shader** over the webcam. Optional subtle lines only inside opaque overlay pixels, as a toggle.
- **Camera-safe zone:** centre 60 % × 55 % (virtual x 77–307, y 50–170) free of persistent elements; transient callouts may cross it.
- **Few frames, long holds.** That is the look. Motion is stepped through integer offsets.

## 2. Element map (virtual px, origin top-left)

| Element | Position / size | Notes |
|---|---|---|
| P1 (DJ) health bar | x 12–156, y 10, 144×8 | 144 px = 144 HP nod to SF2; yellow drains toward centre; red recoverable trail decays 1 px / 4 f; damage flash white 2 f |
| P2 (CHAT) health bar | mirrored x 228–372 | |
| Centre emblem | x 160–224, y 4–30, 32×16 glyph | our own "VS"/"DJ" mark |
| Timer | x 180–204, y 20, two 10×14 digits | track remaining time (duration is in `np:track`) or 99→0 round timer in v3 [decide] |
| Name plates | y 20; P1 left at x 12, P2 right at x 372 | 8 px font, 1 px shadow; P2 shows top donor for 3 s after a hit |
| Round-win markers | y 20 at inner bar ends | 8×8 vinyl icon, up to 3 |
| Portraits | 24×24 at x 2 / x 358, y 20 (built v2; under the bars, name plates shifted to x 28 / 284) | DJ mascot face; CHAT speech-bubble face, 4 moods each |
| HYPE meter | bottom corners, 112×6, 3 segments | cyan fill, "MAX" flashes 8 f on / 8 f off |
| Combo counter block (P1) | x 20, y 48 (was 60; moved 2026-10-06 to clear the callout lane and sit under the portraits); numerals 20×28 stacked, 40×56 from tier 4 with the callout lane dropping to y 124 | 3S-style slam-in; rank word below; whole block drops on bank |
| Combo block (P2 chat, v3) | mirrored, right-aligned x 364 | bits/subs stack |
| Move callout | centred x 96, y 104; ≤ 16 glyphs of 12×16 slanted | see §4 |
| Now-playing ticker | x 124–260, y 206, 136×8 | attract-mode marquee: "NOW PLAYING ▶ ARTIST — TITLE ▶ 11A 124" |
| Track-change "VS card" | band y 80–136 for 150 f | two diagonal wipes meet; NOW / NEXT panels; our VS glyph |
| Round banners (v3) | centred 160×32 word sprites | ROUND 1 · FIGHT! · K.O. · PERFECT · TIME OVER · DOUBLE K.O., our lettering |

## 2a. Iteration 1 is solo

Triode (2026-10-06): one side only, no PvP. The solo HUD is specified in `art/README.md`
("Solo layout") and runs in the preview with `?solo`: the top-left bar becomes the HYPE bar,
the centre digits show BPM, and every P2 element is removed.

## 3. Sprite vs text vs procedural

- **Sprites:** bar frames and 16 drain tiles, emblem, markers, portraits, meter frames, MAX, hit numerals 0–9 (and a 40×56 big set), rank/word banners, callout glyph set, sparks, lightning, fire tiles, dizzy ornaments, mascot, projectiles, VS-card wipes.
- **Bitmap text (BMFont with baked outline/shadow):** names, ticker, rank words, donor names, debug. Faces: Public Pixel or Kenney Pixel (CC0) at 8 px; Kaph (OFL) or Jersey 10 (OFL) at 16/32 px; Thaleah Fat (CC-BY, credit) or a hand-drawn set for callouts. Avoid Joystix, BoldPixels, any "Street Fighter font".
- **Procedural, pixel-snapped:** bar fill widths, trail decay, meter segments, screen shake (integer offsets of the root), 60 % darken quad, palette-swap LUT shader for escalation recolours, afterimage trails (previous frames tinted at −4/−8/−12 px).

## 4. Motion grammar

- **Callout pop-in:** 1 f at 3×, 1 f at 2×, then 1× with a 2 px overshoot (4 f total); first 2 f pure white via LUT; a 16×16 spark plays once at the leading edge.
- **Hold:** 36 f; each new callout pushes the previous down 18 px and dims one palette step (max 3 visible).
- **Exit:** slide 24 px toward the edge over 6 f, then alpha 100 → 50 → 0 in steps. No smooth fades.
- **Hit-stop:** every HUD animation freezes 6 f at each move pop. This is the most Capcom-feeling thing we can do.
- **Reference timings (60 fps):** SF2 hit-stop 14 f; super hit 8/10 f; hitstun 11/16/20 f; later Capcom 9/11/13 f. Round/FIGHT/KO card timings still to be measured.

## 5. Escalation ladder (tied to the tier thresholds in `02`)

| Tier (hits) | Numerals | Extras |
|---|---|---|
| 1 (3) | 20×28 gold | one spark per hit |
| 2 (6) | LUT → yellow | 24×24 sparks; 1 px shake 4 f |
| 3 (10) | LUT → orange | lightning arc 32×64 behind numerals (6 f loop); 2 px shake 6 f |
| 4 (15) | big numerals 40×56 | fire border tiles top/bottom (8 f loop); afterimage trail on callouts |
| 5 (25) | LUT → red | HYPE fills faster; MAX flashes; CHAT portrait "scared" |
| SUPER fires | strobe red/white 4 f | 60 % darken 12 f, bars pop white 2 f, mascot super pose, 3 px shake 10 f, up to 12 sparks |
| 6 (40) | rainbow LUT every 2 f | double fire border, lightning both sides, ticker reads the top-tier word |

Drop (bank): numerals fall 32 px with a 2-step bounce over 12 f; rank word lingers 24 f; HYPE keeps its level.

## 6. Characters [decide]

Recommendation: **no full-size DJ fighter.** The webcam is P1. Instead:
1. **Portrait chips** 24×24 with 4 moods (MvC/Alpha convention).
2. **Corner mascot** 48×64 above the P1 meter: working name "Wax", a hooded brawler whose head is a record (label = eye). States: idle 6 f, punch 4, super 8, hurt 3, dizzy 4 (orbiting mini-records), KO 6, win 4.
3. **CHAT as a crowd strip** 64×24 of six chibi heads: cheer, boo, throw coins (bits, 8×8 arcs), hurl a "bass bomb" (sub, 24×24), slide in as a wave (raid). Mood follows the health balance.
If a full fighter is ever wanted: a 64–80 px cut-in behind the decks during super flash only.

## 7. Asset list by phase

| Phase | Sheets | Decoded GPU | Hand-finished frames |
|---|---|---|---|
| v1 HUD + callouts | hud 512×256, font8 128×128, font16 256×128, digits 256×64, callout 256×128, vs 512×128 | ≈ 1.1 MiB | ≈ 120 tiles + 130 glyphs |
| v2 escalation | fx 512×512, mascot 512×256, digits_big 512×64, portraits 128×64 | ≈ 1.6 MiB | ≈ 100 VFX + 35 mascot + 8 portraits |
| v3 chat/KO/rounds | chat 512×256, banners 512×256, mascot2 512×256 | ≈ 1.5 MiB | ≈ 90 chat/banner + 14 mascot |
| **Total** | 13 atlases | **≈ 4.2 MiB** | **≈ 500 frames** (smaller than one Alpha character) |

Full per-asset tables: research note §6. PNG on disk will be far smaller (indexed pixel art, likely 1–2 MB total), which matters for inlining (see `05`).

## 8. Production pipeline

1. Author in Aseprite ($19.99) with the Endesga-32/12-bit master palette; one `.aseprite` per sheet, tags per animation.
2. `aseprite -b *.aseprite --sheet-pack --extrude 1 --shape-padding 2 --sheet out/<n>.png --data out/<n>.json --format json-hash --list-tags` (Pixi reads json-hash natively; a 30-line adapter maps Aseprite tag/durations to Pixi `FrameObject[]`).
3. Fonts: rasterise the chosen CC0/OFL faces at 8/16/32 px, paint outline/bevel in Aseprite, export BMFont `.fnt` + PNG (SnowB BMF in the browser works). Giant hit numerals are a sprite strip, not a font.
4. AI assist: Retro Diffusion (palette-locked, pay-per-image) or PixelLab (skeleton animation, subscription) for reference poses and VFX; always redraw/clean in Aseprite to a fixed palette. Outputs are owned by the creator on both. Expect to hand-fix frame-to-frame consistency.
5. Placeholders for logic testing before art exists: LuizMelo Martial Hero (CC0), Kenney particle pack (CC0), Boxer character (CC0). Never Spriters Resource rips or MUGEN packs.
6. Credits file in the theme for CC-BY fonts.

## 9. Open items

- Measure ROUND/FIGHT/KO card timings and the ST super gauge from footage.
- Confirm Google Fonts licences per specimen (Jersey 10, Micro 5, Tiny5) and read the "Fight!" font EULA before considering it.
- Decide the timer semantics (track remaining vs round clock).
- Decide the mascot concept and the P1 name.
