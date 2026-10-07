# 08 · Graphic design brief (for the art session)

You are producing the sprite and font assets for DJ Street Fighter, a pixel-art fighting-game HUD
that sits over a DJ's webcam in a 1920×1080 stream. The engine, game design and platform are
settled elsewhere; this brief tells you what to make, at what size, in what format, and where the
hard edges are. Read `04 Visual bible and asset list.md` next (the full element map, motion grammar
and escalation ladder), then `research_notes/visual_style_street_fighter.md` for the sourced
reference material.

## 1. Non-negotiables

- **Canvas:** everything is authored at a virtual resolution of **384×216 pixels** and displayed at
  exactly 5× (1920×1080). One virtual pixel is a 5×5 block on stream. No sub-pixel art, no
  anti-aliasing against transparency, no fractional scales, no rotation except 90° multiples.
- **Transparency:** the background is live video. Sprites need a dark outline so they read over
  any footage. Outline colour is dark navy `#181425`, never pure black (black reads as a hole).
- **Palette:** Endesga 32, snapped to 12-bit (each RGB channel a multiple of 0x11). Each sprite
  uses at most 15 colours plus transparency, like a CPS-2 palette slot. The signature sub-palette is
  in `04` §4: health yellow `#fee761 → #feae34 → #f77622`, damage red `#e43b44`, trail `#f6757a`,
  meter cyan `#2ce8f5 / #0099db / #124e89`, chrome greys `#c0cbdc / #8b9bb4 / #5a6988 / #3a4466`,
  gold bevel for numerals `#ffffff / #fee761 / #feae34 / #b86f50`.
- **Legal:** imitate the idiom (two bars growing inward, centre emblem, stacked hit numerals,
  slanted callouts, hit sparks, super flash). Do not reproduce Capcom sprites, HUD art, logos, the
  "KO" emblem, bitmap fonts ripped as images, character names or likenesses. Every banner word is
  ours.
- **Few frames, long holds.** That is the look. Idle 4–6 frames, a hit 3, a spark 3–4, a KO fall 6–8.
- **Camera-safe zone:** the centre 60 % × 55 % (virtual x 77–307, y 50–170) stays free of
  persistent elements; transient callouts may cross it.

## 2. Deliverables by phase

Sizes are virtual pixels. Full tables with every frame count: `04` §7 and the research note §6.

### v1 · HUD and callouts (do this first)
| Asset | Spec |
|---|---|
| Health bar frame, left and right | 148×12 incl. end caps; fill area 144×8 (144 px = 144 HP, a nod to SF2) |
| Drain tiles | 16 states of 8×8 so the bar drains per pixel, stepped not smooth |
| Recoverable-trail tile | 8×8, tinted at runtime |
| Centre emblem | 32×16, two states (normal, flash). Our own "VS" or "DJ" mark |
| Timer digits | 0–9 plus colon, 10×14 |
| Name-plate strip | 72×10, two states |
| Round-win marker | 8×8 vinyl icon, empty and won |
| HYPE meter frame | 116×8 left and right; segment fill 36×4 × 4 states; "MAX" 20×8 on/off |
| Hit numerals | 0–9 at 20×28, gold bevel, drawn to overlap when stacked |
| Callout glyph set | A–Z, 0–9, ! + x and space at 12×16, slanted, baked outline and bevel |
| Rank words | up to 64×12 each, or bitmap text (decide after the word set is chosen) |
| Hit spark small | 3 frames of 16×16 |
| VS-card wipe panels | 2 panels 192×56 plus 2 wipe masks |
| Ticker strip background | 136×10 nine-slice |
| Fonts | 8 px HUD face from Public Pixel or Kenney Pixel (CC0); 16 px names/timer from Kaph or Jersey 10 (OFL); callouts from Thaleah Fat (CC-BY, credit) or a hand-drawn set. Baked as BMFont `.fnt` + PNG with outline and shadow painted in |

### v2 · Escalation effects
Sparks 24×24 (4 f) and 32×32 (6 f); lightning arc 32×64 (6 f); fire border tile 16×16 (8 f) plus
corners; big numerals 40×56; rank words for tiers 4–7; super-flash burst 64×64 (8 f); palette LUT
strips 16×1 for recolours; mascot "Wax" 48×64 (idle 6, punch 4, super 8, hurt 3, dizzy 4, KO 6,
win 4); dizzy mini-records 8×8 (4 f); portraits 24×24, 4 moods each for DJ and CHAT.

### v3 · Chat fight-back
Crowd heads 12×12 (6 heads × 4 moods × 2 f); bit coin 8×8 (4 f) + impact 16×16 (3 f); bass bomb
24×24 flight (6 f) + 48×48 burst (6 f); raid wave 96×24 (8 f); chat cut-in 96×64 (8 f); bar damage
flash tiles; round banners 160×32 (ROUND, FIGHT!, K.O., PERFECT, TIME OVER, DOUBLE K.O.) plus
round digits 16×32; damage number digits 8×12; extra mascot win/KO frames; continue digits 24×32.

Totals: 13 atlases, roughly 500 hand-finished frames, about 4.2 MiB of decoded texture.

## 3. Layout you are designing into (virtual px, origin top-left)

P1 bar x 12–156 y 10 · P2 bar mirrored x 228–372 · emblem x 160–224 y 4–30 · timer x 180–204 y 20 ·
name plates y 20 · HYPE meters bottom corners y 198 · combo block x 20 y 60 (mirrored for chat) ·
callouts centred x 96 y 104 · now-playing ticker x 124–260 y 206 · VS card band y 80–136.
Full table: `04` §2.

## 4. Motion the art must support

- Callout pop-in: 1 frame at 3×, 1 at 2×, then 1× with a 2 px overshoot; first two frames pure
  white (so glyphs need a clean silhouette). Hold 36 f. Exit: slide 24 px and alpha 100 → 50 → 0 in
  steps. No smooth fades anywhere.
- Hit-stop: every HUD animation freezes 6 frames at each move pop.
- Escalation recolours are palette swaps (LUT), so keep each sprite's colours on a consistent
  ramp index: outline, shade, mid, face, highlight.
- Numerals stack and slam; a drop is a 32 px fall with a 2-step bounce over 12 frames.
- The health bar drains in whole pixels with a red trail that decays 1 px every 4 frames; damage
  flash is 2 frames of white.

## 5. Production pipeline and file conventions

- Author in **Aseprite** with the palette loaded; one `.aseprite` per sheet; animations as tags.
- Export per sheet: `aseprite -b <name>.aseprite --sheet-pack --extrude 1 --shape-padding 2 --sheet
  out/<name>.png --data out/<name>.json --format json-hash --list-tags`. Power-of-two sheets up to
  1024×1024 at 1× virtual resolution. No rotation in the packer.
- Sheet names: `hud`, `font8`, `font16`, `digits`, `callout`, `vs` (v1); `fx`, `mascot`,
  `digits_big`, `portraits` (v2); `chat`, `banners`, `mascot2` (v3).
- Frame tags: `<object>_<state>` in snake_case, e.g. `wax_idle`, `spark_small`, `bar_drain_07`.
- Fonts: rasterise the chosen face at its native 8/16/32 px, paint outline/bevel in Aseprite,
  export BMFont `.fnt` (text or XML) + PNG. SnowB BMF in the browser works. Giant hit numerals are
  a sprite strip, not a font.
- AI assist is fine for reference poses and VFX (Retro Diffusion for palette-locked stills,
  PixelLab for skeleton animation; outputs owned by the creator on both) but every frame is
  redrawn or cleaned by hand to the fixed palette; generators do not hold a 15-colour palette and
  selective outlining across 20 frames.
- Placeholders for engine testing before art exists: LuizMelo Martial Hero (CC0), Kenney particle
  pack (CC0). Never Spriters Resource rips or MUGEN packs.
- Keep a `CREDITS.md` for CC-BY fonts.
- Deliver into `assets/atlas/` and `assets/fonts/` of the theme folder (layout in
  `research_notes/rendering_stack.md` §8); until the theme exists, into `TRIODE Street Fighter/art/`.

## 6. Decisions that affect the art (ask Osh if unanswered)

Tier word set (decides the rank-word sprites) · P1 name (name plate) · mascot concept approval ·
timer semantics (digits are the same either way) · whether CRT scanlines inside opaque pixels are
wanted as a toggle (recommendation: no full-frame CRT ever).

## 7. Reference facts to design against (sourced; details and caveats in the research note)

CPS-1/2 ran 384×224 at 16 colours per tile; SF2's health bar was 144 pixels for 144 HP and Capcom
pre-rendered 20 drain tiles; SF2 hit-stop is 14 frames, super hit 8/10; 3rd Strike stacked numerals
slam in with a 2–3 frame pop; KI's announcer tiers run Triple (3) to Killer (12+). Round/FIGHT/KO
card timings and exact SF2 sprite dimensions are not yet measured from footage.
