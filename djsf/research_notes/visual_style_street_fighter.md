# DJ Street Fighter — Visual Style Research Note

**Project:** "DJ Street Fighter" theme for Now Playing 3 (OBS browser source, 1920x1080, transparent over the DJ camera)
**Date:** 2026-10-06
**Status:** Research + proposed visual bible. Nothing here is final art direction; it is the evidence base for it.

How to read this note: Sections 1–4 are research with sources. Sections 5–6 are proposals built on that research. Anything marked **[UNVERIFIED]** could not be confirmed against a fetched source during this pass (several key fan wikis — streetfighter.fandom.com, wiki.supercombo.gg, srk.shib.live, strategywiki.org, tvtropes.org and their mirrors — are bot-blocked as of today; where I rely on search-snippet text from those sites I say so). Anything marked **[FROM MEMORY]** is a widely-observable fact about the games that I could not source in this pass and should be checked against emulator footage before it becomes a spec.

Legal framing, once: we may imitate the *idiom* (two bars, centre timer, round markers, stacked hit numbers, slanted callouts, hit sparks, "super flash" darkening). We may not use Capcom's sprites, HUD art, bitmap fonts ripped as images, logos, the "KO" emblem artwork, character names or likenesses. Everything below is written with that line in mind.

---

## 1. HUD anatomy of the reference games

### 1.1 Street Fighter II (CPS-1, 1991) and Super Turbo (CPS-2, 1994)

**Layout.** Two horizontal life bars run along the top edge, growing inward from the screen edges toward a central emblem. The character name sits directly below its bar; a small "victory sign" hand icon appears under the bar for each round won; the round timer sits in the centre under the "KO" lettering, and when the timer reaches zero the player with more life wins. All of this is laid out in a fan reimplementation's UI design page that mirrors the original arrangement ([Rengrow SF2 wiki — UI](https://github.com/Rengrow/Street-Fighter-II-Gamusinos-Fighters-/wiki/UI)).

**Health bar colour and damage.** The bar is yellow for remaining life and turns red for the damaged portion, proportionally. In the SF2 series every character had the same health — 144 points in the arcade version, which is literally the number of pixels in the health bar (fandom [Health Meter](https://streetfighter.fandom.com/wiki/Health_Meter) via search snippet; page itself returns HTTP 402 to fetchers). When the bar reaches the "KO" letters the character is knocked out.

**How the bar is actually drawn (important for our sprite plan).** Fabien Sanglard's reverse-engineering shows the CPS-1 can only place 16x16 tiles, so a naïve bar would animate in chunky 16-px steps. Capcom instead pre-rendered twenty intermediate tile states (on tile row `0xF0` of sheet `0x81`) so the bar drains pixel-perfectly — "sub-tile accurate animation" from a tilemap ([Sanglard — SF2 health bar](https://fabiensanglard.net/sf2_health_bar/)). Lesson: a drained bar is a *sprite-strip*, not a scaled rectangle, and the drain should animate (we can do it procedurally, but it should look stepped per pixel, not sub-pixel smooth).

**Hit-stop (impact freeze).** In SF2 the freeze on hit is generally 14 frames starting immediately after the collision frame; hitting a grounded idle opponent extends it to 15; supers cause 8 frames for the attacker and 10 for the opponent (11 vs grounded idle). Ground hitstun is 11 frames (light), 16 (medium), 20 (hard) ([mugen-net Research: Street Fighter II](https://mugen-net.work/wiki/index.php/Research:Street_Fighter_II)). A cross-game comparison gives ~9/11/13 frames for light/medium/hard in later Capcom games, with SF2 "around 14 frames regardless of button strength", and a fireball freezing the victim ~12 frames before pushback ([Sonic Hurricane — Impact Freeze](https://sonichurricane.com/?p=1043); also [Shoryuken forum thread](https://forums.shoryuken.com/t/hit-stop-and-meaty-tecnical-question/35703)). The SF2 "2-in-1 cancel" exists *because* of hitstop extending the cancel window ([Critpoints — Hitstop](https://critpoints.net/2017/05/17/hitstophitfreezehitlaghitpausehitshit/)).

**Timer rate.** "Every 60 internal frames, the overhead match clock counts down one second" at base speed; at Turbo speed 3 (default) the game skips 1 frame for every 4 shown, i.e. the engine runs 75 internal frames per displayed second, so a displayed "second" is ~0.8 real seconds; the clock only counts real seconds at the non-turbo setting ([Sonic Hurricane — Turbo Speed Mechanics](https://sonichurricane.com/?p=1864), written about CFE/HF; EventHubs summary [here](https://eventhubs.com/news/2010/mar/03/sonichurricanecom-explains-turbo-speed-settings)). Timer starts when the announcer says "Fight!" (fandom [Round Timer](https://streetfighter.fandom.com/wiki/Round_Timer), via snippet).

**Dizzy / stun.** Stun indicators float above the head; in HD Remix (same rules as ST) there are four animations keyed to stun length — stars (shortest), birds, angels, grim reapers (longest) ([EventHubs — HD Remix basics](https://www.eventhubs.com/guides/2009/jan/12/basic-gameplay-details-super-street-fighter-2-turbo-hd-remix)). SF2's CPU can escape dizzy in 12 frames ([Kotaku](https://kotaku.com/how-street-fighter-iis-computer-opponents-cheat-to-kick-1838411348)) — i.e. dizzy is a *state with a looping head-ornament sprite*, exactly the kind of thing we want for a "DJ is stunned" moment.

**Double KO / Perfect / Time Over.** In ST no victory is awarded for a double KO; if nobody has two wins after round 3 a sudden-death 4th round is played ([ST Revival — Double KO](https://www.strevival.com/2019/01/06/the-oddities-of-the-double-ko-in-st/)). The CPS-1 announcer voice famously "bears a strong resemblance to game show host Bob Barker" (fandom [Game Announcer](https://streetfighter.fandom.com/wiki/Game_Announcer), via snippet). **[FROM MEMORY]** Presentation beats you can confirm on any ST recording: "ROUND 1" slides in, "FIGHT!" punches in and out; on the final hit the game freezes, big "K.O." appears centre-screen, loser falls, then "PERFECT" if applicable and "YOU WIN"; "TIME OVER" when the clock expires; "DOUBLE K.O." when both fall. These are large bitmap word-sprites, centre-screen, roughly 1/3 screen width.

**Super meter (ST).** **[FROM MEMORY / needs footage check]** The ST super gauge is a single horizontal bar at the bottom of the screen on each player's side; when full it displays a flashing "SUPER" label. Combo messages ("2 HIT COMBO", "FIRST ATTACK", "REVERSAL") appear on the attacker's side under the health bar in a small italic yellow bitmap font. The SuperCombo wiki has a dedicated page ([SSF2T/HUD](https://wiki.supercombo.gg/w/Super_Street_Fighter_2_Turbo/HUD)) but it is behind an Anubis bot-wall; check it in a normal browser.

### 1.2 Street Fighter Alpha series (CPS-2, 1995–1998)

- **Super Combo gauge (Alpha 3 "ISMs").** A-ism gives a *green* three-level gauge (Light/Medium/Heavy picks 1/2/3 levels); X-ism has a single-level gauge and one super; V-ism has a "simple blue super gauge (with a percentage indicator)" and Custom Combos instead of supers ([Wikipedia — SFA3](https://en.wikipedia.org/wiki/Street_Fighter_Alpha_3)).
- **Guard Power Gauge** (Alpha 3) depletes on block; X-ism has the largest guard bar, V-ism the smallest ([Wikipedia — SFA3](https://en.wikipedia.org/wiki/Street_Fighter_Alpha_3)). It sits under the health bar as a second thinner bar. **[FROM MEMORY]**
- **Custom Combo visual.** The character "leaves a shadow trail as Custom Combo is used, with the gap between each shadow being determined by the strength used to activate" ([Wikipedia — SFA3](https://en.wikipedia.org/wiki/Street_Fighter_Alpha_3)). This "afterimage trail" is a cheap, iconic effect we can reuse for a long combo.
- **Super flash.** Retrospectives describe that the screen darkens when a super is activated with a bright flash (search snippet sourced from [Nintendo Life's SFA review](https://www.nintendolife.com/reviews/2010/01/street_fighter_alpha_warriors_dreams_retro) and [Fighters Generation](https://fightersgeneration.com/games/sfa.html); treat as **[UNVERIFIED wording]**). If the opponent is finished by a Super Combo, "the background will flash red and yellow" ([Wikipedia — Street Fighter Alpha](https://en.wikipedia.org/wiki/Street_Fighter_Alpha)).

### 1.3 Street Fighter III: 3rd Strike (CPS-3, 1999)

- **Super Art gauge.** Shows a Roman numeral (I, II, III) for the selected Super Art; a full meter allows a super; a *flashing blue* meter means an EX special is available; an outer number shows the maximum stockable supers (1–3) and an inner number the current stock; the gauge length and stock count depend on the chosen Super Art ([SRK wiki — 3S HUD](https://srk.shib.live/w/Street_Fighter_3:_3rd_Strike/HUD); [3S Super Meter](https://srk.shib.live/w/Street_Fighter_3:_3rd_Strike/New/Super_Meter) — both via search snippets, pages bot-walled).
- **MAX.** "Once your meter is fully filled up, a flashing MAX sign indicates that it can no longer build up any more power" ([StrategyWiki — SFIII Gameplay](https://strategywiki.org/wiki/Street_Fighter_III/Gameplay), via snippet).
- **Stun gauge.** "A black bar that fills up with a red meter when taking stun damage", positioned below the health meter ([SRK wiki — 3S Stun Meter](https://srk.shib.live/w/Street_Fighter_3:_3rd_Strike/New/Stun_Meter), via snippet).
- **Misc status indicator.** Messages such as "First Attack", "Tech Bonus", and the combo counter appear on the side of the player who performed the action ([SRK wiki — 3S HUD](https://srk.shib.live/w/Street_Fighter_3:_3rd_Strike/HUD), via snippet).
- **Combo counter rank words.** The brief lists GOOD / GREAT / SUPER / COOL / FANTASTIC / FINE / DEADLY / MARVELOUS / BRILLIANT / RADICAL. I could **not** find a fetchable text source confirming this exact list in this pass (every candidate page is bot-walled). **[UNVERIFIED — treat the list as a design brief, not a citation.]** What *is* well established and visible in any 3S footage: the hit count renders as very large stacked numerals (roughly 2–3x the HUD font height) on the attacker's side at mid-height, each new hit "slamming" the number in with a 2–3 frame scale pop, with a judgement word below after the combo ends, and the whole block dropping/fading after a short hold. **[FROM MEMORY]** For our purposes we will use our own rank ladder (see 5.6) rather than Capcom's exact words anyway — we should not copy their list verbatim.
- **Animation budget.** 3rd Strike holds the Guinness record for most animation frames in a 2D fighter: 23,039 in-game character frames ([Guinness World Records](https://www.guinnessworldrecords.com/world-records/98823-most-frames-of-animation-in-a-2d-fighter-videogame)). The original SF3 shipped with only ten characters because of the per-character frame cost ([Wikipedia — Street Fighter III](https://en.wikipedia.org/wiki/Street_Fighter_III)). This is the single strongest argument for *not* trying to animate a full fighter for v1.
- **Super flash.** Akuma's Shun Goku Satsu whites the screen out; generic Super Art activation freezes both characters while the background dims and the attacker is highlighted. **[FROM MEMORY — confirm on footage]**

### 1.4 Marvel vs. Capcom (CPS-2) for comparison

The Hyper Combo gauge is "a colored meter at the bottom of the screen that gradually fills as characters deal and receive damage", levelling up to five levels and then resetting ([Wikipedia — MvC2](https://en.wikipedia.org/wiki/Marvel_vs._Capcom_2:_New_Age_of_Heroes)). **[FROM MEMORY]** MvC's hit counter is a tall column of large numerals with "HITS" beneath on the attacker's side, staying on screen longer than SF's and climbing to 50–100+, and its hyper activation backlights the character with a radial flash — the maximalist end of the idiom. Health bars include a red "recoverable" portion for tagged-out partners; this red-trail convention is the one most viewers recognise today (SF4 onward uses it for all characters).

### 1.5 Killer Instinct (Rare/Midway, 1994) for comparison

Combo names by hit count: "Triple(3), Super(4), Hyper(5), Brutal(6), Master(7), Awesome(8), Blaster(9), Monster(10), King(11), Killer(12+), Ultra, and Ultimate", and "after you perform a combo, the announcer will yell out what type of combo it was" ([TASVideos submission #3251 — SNES Killer Instinct](https://tasvideos.org/3251S)). The "C-C-C-Combo Breaker!" shout is the genre's most quoted announcer line ([Killer Instinct Wiki — Combo Breaker](https://killerinstinct.fandom.com/wiki/Combo_Breaker)). KI is the best model for *escalating named tiers tied to hit count plus an announcer shout*, which is exactly our combo-stack mechanic.

### 1.6 Stage parallax and crowd

SF2 drew its floor parallax by scrolling the 16x16 SCROLL2 layer per scanline, and composited up to six layers (SCROLL1 8x8 for GUI, SCROLL2 16x16, SCROLL3 32x32, OBJ sprites, two STAR layers). Priority masking lets some tile colours draw over sprites. Guile's stage even uses OBJ tiles to finish the F-16 because the SCROLL2 budget ran out ([Sanglard — CPS-1 graphics](https://fabiensanglard.net/cps1_gfx/index.html); [SpritesMind thread](https://gendev.spritesmind.net/forum/viewtopic.php?p=38010)). Crowd animations in SF2 are 2–4 frame loops of background sprites (cheering, drinking, bike-wobbling). **[FROM MEMORY]** For us the "stage" is the DJ's room on camera; we only borrow the *crowd* idea for the P2 "CHAT" side.

### 1.7 Timing summary for our animation tables (60 fps)

| Event | Reference value | Source |
|---|---|---|
| Hit-stop, normal hit | 14 f (SF2); 9/11/13 f L/M/H later games | mugen-net; Sonic Hurricane |
| Hit-stop, super hit | 8 f attacker / 10 f defender (SF2) | mugen-net |
| Hitstun L/M/H | 11 / 16 / 20 f (SF2) | mugen-net |
| Projectile freeze | ~12 f | Sonic Hurricane |
| Clock tick | 60 internal frames | Sonic Hurricane |
| Dizzy escape (CPU) | 12 f | Kotaku |
| Round intro, "FIGHT!" hold, KO freeze | **[FROM MEMORY]** ≈ 60–90 f intro card, ≈ 30 f FIGHT, ≈ 45–60 f KO freeze | needs footage timing |

---

## 2. Hardware constraints that define the look

### 2.1 CPS-1 (1988) — Street Fighter II

- 384x224 raster at 59.6294 Hz; Motorola 68000 @ 10 MHz; 4096 colours on screen from a 65,536-colour master palette, organised as 192 global palettes of 16 colours; tile sizes 8x8, 16x16, 32x32, each tile 16 colours (15 unique + 1 transparent); sprites are 16x16 with H/V flip, 256 per scanline ([Wikipedia — CP System](https://en.wikipedia.org/wiki/CP_System)).
- 16 indexed colours = 4 bits per pixel; one 16x16-tile "sheet" is 32 KiB. SF2 World Warrior spent 4.6 MiB of its 6 MiB on 144 OBJ sheets; Zangief 19 sheets, E. Honda 15, Blanka 15, Dhalsim 14, Ryu 13.5, Ken only 3 (Ken is a palette+patch of Ryu). Poses are built from 25–45 tiles: Ryu's victory pose 29 tiles, Sagat's Tiger Uppercut 30, Honda's jump 45, Chun-Li's pose 25 ([Sanglard — SF2 paper trails](https://fabiensanglard.net/sf2_sheets/); [CPSS sheets explorer](https://www.fabiensanglard.net/cpss/)).
- **Derived sprite dimensions.** 25–45 tiles of 16x16 means a standing fighter is roughly 5x6 to 6x7 tiles — about **80–96 px wide by 96–112 px tall** on a 224-px-tall screen, i.e. a fighter is ~45–50% of screen height. **[DERIVED, not measured]** The Spriters Resource rips for arcade Ryu are the place to measure exactly ([Ryu — SF2 arcade rips](https://www.spriters-resource.com/arcade/streetfighter2/asset/60224/)).
- **Animation frame counts.** Not documented in any fetched source. **[FROM MEMORY]** SF2 WW idle stances are 4–6 frames; a light punch is 3 frames (startup/active/recovery), a heavy ~5; hit reactions 2–3 frames per strength; KO fall ~6–8 frames; a dizzy loop 4 frames; hit spark 3–4 frames. For our purposes "few frames, long holds" *is* the look.

### 2.2 CPS-2 (1993) — Super SF2, Alpha, MvC, Darkstalkers

384x224 active (512x262 with overscan); encrypted 68000 @ 16 MHz; 4096 colours on screen (12-bit) from a 24-bit master palette; 16 colours per tile (4-bit planar); 900 sprites on screen; launched 10 Sept 1993 with Super Street Fighter II ([Wikipedia — CP System II](https://en.wikipedia.org/wiki/CP_System_II); layer registers for 8x8 A/B, 16x16 and 32x32 layers in [Data Crystal — CPS2 hardware](https://datacrystal.tcrf.net/wiki/CPS2:Hardware_information); [System16](https://www.system16.com/hardware.php?id=795)). Visually the same constraints as CPS-1 (4-bit sprites, 12-bit RGB), with more sprites and ROM; Alpha's larger, more "animated-film" sprites come from budget, not colour depth.

### 2.3 CPS-3 (1996) — Street Fighter III

384x224 (496x224 widescreen mode used only by 2nd Impact); Hitachi SH-2 @ 25 MHz; 32,768 colours on screen (15-bit) from a 16.7M palette; 64 (6-bit) or 256 (8-bit) colours per tile, with a 16-colour (4-bit) text overlay layer; up to 1024 sprites with hardware scaling; 4 scroll layers plus a text layer; line-scroll, line-zoom, frame-buffer zoom, colour blending ([Wikipedia — CP System III](https://en.wikipedia.org/wiki/CP_System_III)). This is why 3S looks "painted": 64-colour sprites with soft ramps versus SF2's 15-colour ramps. If we want the *SF2/Alpha* look we stay at ≤16 colours per sprite; if we want *3S* richness we allow up to 64 but keep hard pixels and no anti-aliasing against the alpha edge.

### 2.4 Pixel-art technique conventions

- **Outlines.** Capcom's fighters use a dark (not pure black) outline that is *selectively* dropped or lightened on the light-facing side — "selective outlining" — so forms read as volume rather than cut-outs; dithering is used sparingly for translucency and gradients ([TabNews — SF2/CPS-1 curiosities](https://www.tabnews.com.br/rafael/curiosidades-sobre-o-street-fighter-ii-e-a-placa-de-arcade-cps-1); character design context in [Siliconera — Akiman interview](https://www.siliconera.com/former-capcom-developer-akiman-on-designing-the-iconic-characters-of-street-fighter-ii/)). HUD elements, by contrast, use a hard 1-px black (or very dark navy) outline everywhere so they read over any background — important for us because our background is a live camera.
- **Colour ramps.** 15 usable colours per sprite are typically split into 3–4 ramps of 3–4 steps (skin, cloth A, cloth B, hair/accent) plus one outline and one highlight. 12-bit RGB on CPS-1/2 means each channel is one of 16 values; snapping our palette hex values to multiples of `0x11` gives authentic "arcade" colour quantisation for free.
- **Upscaling.** The look depends on integer nearest-neighbour scaling: every virtual pixel becomes an exact NxN block. Non-integer scales or bilinear filtering destroy it. In the browser this is `image-rendering: pixelated` on canvas/img and `SCALE_MODES.NEAREST` on every PixiJS texture; in OBS, browser sources that are resized get *stretched* and blur, so the browser source must be created at exactly 1920x1080 and never resized ([OBS forum — browser source scaling](https://obsproject.com/forum/threads/browser-source-option-to-scale-instead-of-stretch.83508); OBS "Point" scale filter for image sources per [GamePretty — Aseprite pixel art in OBS](https://gamepretty.com/aseprite-how-to-use-pixelart-in-obs/)).
- **CRT / scanlines over a webcam?** Recommendation: **no full-frame CRT shader.** The camera is 1080p video; scanlining it makes the DJ look like a Zoom call from 1994 and halves perceived brightness. Scanlines also fight OBS's encoder (high-frequency horizontal detail costs bitrate). If a CRT flavour is wanted, apply a *subtle* 1-px darker line every 5 px **only within the overlay's own opaque pixels** (bars, plates, callouts), never over transparent regions, and make it a theme toggle. Phosphor bloom/curvature are out. **[Design judgement, not a sourced fact]**

---

## 3. Typography

### 3.1 What the originals look like

**[FROM MEMORY / observable in footage]** SF2's HUD lettering is an 8-px-cell bitmap: bold, slightly condensed, white or yellow with a 1-px dark outline; the timer is a 16-px-tall two-digit numeral set; "HIT COMBO" messages use a small italic yellow face. Alpha moves to a chunkier beveled face for names and a bolder italic for messages. 3rd Strike's hit numerals are the showpiece: very large (roughly 24–32 virtual px tall), heavy, beveled gold/orange with a dark outline and an inner highlight, stacked so each new digit set slams in. KI's announcer words are large italic brush-stroke display words. None of these fonts are available to us as fonts, and ripping them as images is off-limits.

### 3.2 Free / openly licensed candidates

Ranked by usefulness to us, with licence. All Google Fonts are SIL OFL 1.1 unless stated (Google Fonts only hosts OFL/Apache/UFL fonts; verify on each specimen's "About & license" tab).

| Font | Source | Licence | Fit |
|---|---|---|---|
| **Kenney Fonts** (Kenney Pixel, Kenney Blocks, Kenney Future, Mini, High + Square variants) | [OpenGameArt — Kenney fonts](https://opengameart.org/content/kenney-fonts) / kenney.nl | CC0 | Clean 8-px HUD text; zero attribution burden. Good *small* font for names/ticker. |
| **Public Pixel** (ggbot) | [itch.io](https://ggbot.itch.io/public-pixel-font) | CC0 | 8x8 monospace, 1324 glyphs — ideal for the attract-text ticker and timer digits. |
| **Pixel Operator** (Jayvee Enaguas) | [dafont](https://www.dafont.com/pixel-operator.font) | CC0 | Proportional + mono, bold weights; readable HUD labels. |
| **monogram** (datagoblin) | [itch.io](https://datagoblin.itch.io/monogram) | CC0 | Tiny monospace; fallback for debug/ticker. |
| **Kaph** (ggbot) | [itch.io](https://ggbot.itch.io/kaph-font) | SIL OFL 1.1 | Bold display pixel face — closest free thing to a 3S-style *big numeral* set; use for hit counts. |
| **Thaleah Fat** (Tiny Worlds) | [itch.io](https://tinyworlds.itch.io/free-pixel-font-thaleah) | CC-BY 4.0 (credit required) | Fat, friendly pixel display; good for move callouts if credited. |
| **Press Start 2P** | [Google Fonts](https://fonts.google.com/specimen/Press+Start+2P/about) | OFL | Namco 1980s style, 8-px grid — *wrong era* (too NES/arcade-80s) except for the attract ticker. |
| **Silkscreen** | Google Fonts | OFL | 8-px UI face by Jason Kottke — web-pixel feel, not fighter. Skip. |
| **Pixelify Sans**, **Tiny5**, **Micro 5**, **Jersey 10/15/20/25**, **Jacquard 12/24**, **Workbench**, **Sixtyfour** | Google Fonts | OFL | Newer pixel faces (2023–24). Jersey 10/15 (sports-jersey block numerals) are the best Google option for *timer and hit numerals*; Micro 5 / Tiny5 for micro labels. **[Licence from Google Fonts policy; confirm per specimen]** |
| **Karmatic Arcade** (Vic Fieger) | [dafont](https://www.dafont.com/karmatic-arcade.font) | "100% free" | Techno/LCD arcade feel; usable for timer digits, not for callouts. |
| **BoldPixels** (YukiPixels) | [itch.io](https://yukipixels.itch.io/boldpixels) | CC-BY-SA 4.0 | *Avoid* — share-alike could be argued to touch derivative sheets. |
| **Joystix** (Typodermic) | dafont | Free for personal; commercial desktop licence **excludes games, apps, webfonts** | *Avoid* for a shipped overlay. |
| **Fight!** (Mehmet Reha Tuğcu) | [DesignBeep write-up](https://designbeep.com/2026/03/02/fight-pixel-font/) | Described as "Standard Commercial License, free to use with redistribution restrictions" | Explicitly SF-inspired fighting-game display face. **[UNVERIFIED licence — read the actual EULA before use]** |
| Any "Street Fighter font" on FontSpace/FontBolt/dafontfree | e.g. [FontSpace category](https://www.fontspace.com/category/street-fighter) | Mixed/unknown | *Avoid*: trademarked names, unclear provenance, several are traced logos. |

Practical pick for v1: **Public Pixel or Kenney Pixel** for 8-px HUD text and ticker; **Kaph or Jersey 10** rasterised at 16 px and 32 px for names, timer and hit numerals; **Thaleah Fat** (credited) or a hand-drawn 12-glyph custom set for callouts. The *slant, bevel, outline and gradient* that make text feel "Capcom" are applied by us in the bitmap-font build step, not by the font.

### 3.3 Bitmap-font pipeline (PixiJS)

PixiJS v8 `BitmapText` loads AngelCode BMFont `.fnt`/`.xml` and MSDF/SDF fonts via `Assets.load('fonts/MyFont.fnt')`, then `new BitmapText({ text, style: { fontFamily: 'MyFont', fontSize } })`; it draws glyphs from a pre-generated atlas so thousands of text objects are cheap; `BitmapText.resolution` is immutable after creation ([PixiJS 8 — Bitmap Text guide](https://pixijs.com/8.x/guides/components/scene-objects/text/bitmap)). Plan: pre-bake each face at its exact virtual-pixel size (8, 16, 32) into `.fnt` + PNG with the outline/bevel/gradient already painted, mark the textures NEAREST, and never scale text at runtime except by integer "pop" factors. The AngelCode text format is documented by every BMFont tool; `load-bmfont` is the reference JS parser ([load-bmfont README](https://cdn.jsdelivr.net/npm/load-bmfont@1.4.2/README.md)). For the giant stacked hit numerals, skip fonts entirely and ship a 0–9 digit sprite strip (see asset list) — it gives per-digit bevel and lets digits overlap the way 3S does.

---

## 4. Producing original sprites in 2026

### 4.1 Hand tools

- **Aseprite** — US$19.99 (itch.io/Steam) ([dacap.itch.io/aseprite](https://dacap.itch.io/aseprite)); the CLI exports packed sheets with JSON: `--sheet`, `--data`, `--format json-hash|json-array`, `--sheet-type packed|rows|columns|horizontal|vertical`, `--sheet-pack`, `--split-layers`, `--split-tags`, `--list-tags`, `--trim`, `--extrude`, `--inner-padding`, `--shape-padding`, `--filename-format {layer}/{tag}/{frame}` ([Aseprite CLI docs](https://www.aseprite.org/docs/cli/)). Its `json-hash` output is what PixiJS's Spritesheet loader reads natively — this is our primary tool.
- **LibreSprite** — GPL fork from Aseprite's last GPL-2 commit (Aseprite went proprietary 26 Aug 2016) ([LibreSprite README](https://cdn.jsdelivr.net/gh/libresprite/libresprite@master/README.md)). Free, slightly behind on features.
- **Pixquare** — iPad pixel-art editor, freemium pay-once, popular with pros ([App Store](https://apps.apple.com/app/id1659428179)). Good for sketching on the couch; export to Aseprite.
- **"Pixel Studio"** — disambiguation: Google's *Pixel Studio* AI image app has been shut down in 2026 ([Android Authority](https://www.androidauthority.com/google-pixel-studio-app-discontinued-3674832/)); the pixel-art editor of the same name (Hippo Games, mobile/desktop) is unrelated and still exists. **[Second claim from memory]** Not needed given Aseprite.

### 4.2 AI pixel-art generators — honest notes

Consensus caveat across 2026 roundups: style-consistent *stills* are easy; **frame-to-frame consistency across an animated sheet is still the hard part** — "your knight's idle frame and walk frame look like they belong to different games" ([FreeGameSprites — AI pixel art 2026](https://freegamesprites.com/en/news/ai-pixel-art-generation-2026-tools-and-workflows)). Also note every "best of 2026" list is written by a vendor ([Ludo's](https://ludo.ai/compare/best-ai-pixel-art-generators), [Sprite-AI's](https://www.sprite-ai.art/blog/best-pixel-art-generators-2026), [Cinevva's](https://app.cinevva.com/guides/ai-pixel-art-generators)).

| Tool | What it does well | Limits | Price | Output licence |
|---|---|---|---|---|
| **PixelLab** (pixellab.ai) | Browser + Aseprite plugin; skeleton-based animation (pose, don't prompt); 4/8-direction rotations; exports engine-ready sheets | Animation capped at 128x128; max still size ~320–400 px by tier; subscription | $12–50/mo, free trial | You own outputs, commercial OK, no training other models ([ToS](https://www.pixellab.ai/termsofservice); [GameDev AI Hub comparison](https://gamedevaihub.com/retro-diffusion-vs-pixellab/)) |
| **Retro Diffusion** (Astropulse LLC — Astropulse is the pixel-artist author) | Most "authentically pixel" grid-aligned, palette-limited output; palette control via API; presets for walk/idle/jump/attack, 8-dir rotation, VFX, returned as GIF or PNG sheet; "Pixel Fixer" | Animation only on web/API, **not** in the $65 Aseprite extension; manual sheet assembly; up to ~276 px | ~$0.015 (RD Fast) to $0.18 (RD Pro) per image, animations $0.07–0.25, credits never expire | Outputs owned by the creator and usable commercially; model/code not ([Retro Diffusion itch comments](https://astropulse.itch.io/retrodiffusion/comments); [GameDev AI Hub](https://gamedevaihub.com/retro-diffusion-vs-pixellab/)) |
| **Scenario** | Train a custom model on *our* art bible for locked style; "Pixel Snapper" grid tool; hosts Retro Diffusion models | No sprite-sheet/animation pipeline; commercial rights on paid plans only | $15/mo; custom training from $45/mo | Commercial on paid ([Ludo vs Scenario](https://ludo.ai/compare/ludo-vs-scenario)) |
| **Ludo.ai** | Prompt → packed sheets (4–64 frames), motion presets, 8 directions, dedicated low-res animation model | General tool; vendor-written comparisons | $20/mo (unlimited images at $50 Pro) | Assets yours for commercial use ([Ludo](https://ludo.ai/compare/best-ai-pixel-art-generators)) |
| **Layer.ai** | Studio batch generation, many DCC integrations, $0 per seat | Aimed at mobile UA/LiveOps studios, overkill for us | Enterprise-ish | Per contract ([Ludo — Layer alternatives](https://ludo.ai/compare/layer-alternatives)) |
| **Rosebud AI** | Vibe-coded playable games | Not a sprite generator; **[no sprite-pipeline info found]** | — | — |
| **Sprite AI / SpriteLab / Sprixen** | Budget sheet generators with idle/walk/attack/hurt/death presets; SpriteLab commercial on free tier | Small sprites, generic style | $8 / $7.99 / $10 per month | Commercial on paid (SpriteLab incl. free) ([Ludo roundup](https://ludo.ai/compare/best-ai-pixel-art-generators)) |

Recommended workflow: use **Retro Diffusion** (palette-locked) or **PixelLab** (skeleton) to generate *reference poses and VFX sprites* quickly; then redraw/clean in Aseprite to a fixed 16-colour palette, because (a) no generator holds a 15-colour palette and selective outline across 20 frames, and (b) a clean-up pass is what makes it *ours* rather than "AI-looking". VFX (sparks, lightning, fire tiles) are where generators shine; a consistent mascot is where they don't.

### 4.3 Sprite-sheet packers

- **Aseprite CLI** (above) — first choice; one command per sheet in a build script.
- **Free Texture Packer** (odrick) — MIT; exports json/xml/css/pixi.js/godot/phaser/cocos2d plus Mustache custom templates; trim, rotation, multipack, TinyPNG; web app, Win/mac/Linux desktop, CLI, Gulp/Grunt/Webpack plugins; author says only critical fixes going forward ([GitHub — free-tex-packer](https://github.com/odrick/free-tex-packer)). Note the `free-tex-packer.com` domain currently redirects to a parking page — use the GitHub releases.
- **TexturePacker** (CodeAndWeb) — polished, paid; the free tier covers what PixiJS needs, and "Pixi" export is just JSON-hash ([CodeAndWeb PixiJS tutorial](https://www.codeandweb.com/texturepacker/tutorials/how-to-create-sprite-sheets-and-animations-with-pixijs5); [HTML5GameDevs thread](https://html5gamedevs.com/topic/16848-do-i-have-to-pay-to-use-sprite-sheets-in-pixijs)).
- Rules for us: power-of-two sheets ≤ 1024x1024 at 1x virtual resolution, 1-px extrude on every frame (bleeding is very visible at 5x NEAREST), no rotation (rotated frames break pixel alignment at odd angles).

### 4.4 Palettes

- Lospec has **no** "CPS"/"Capcom" tag (0 results at [lospec.com/palette-list/tag/capcom](https://lospec.com/palette-list/tag/capcom)). The [arcade tag](https://lospec.com/palette-list/tag/arcade) has AxulArt 32 (arcade/GBA feel), *Red is Dead* (4 colours, "originally made for a fighting game"), PC-66; the [SNES tag](https://lospec.com/palette-list/tag/snes) has Jehkoba64 and Guildhall 256.
- Recommended master palette: **Endesga 32** (ENDESGA, 32 colours; hex list on [Lospec](https://lospec.com/palette-list/endesga-32)) — warm skin ramp, strong red/orange/yellow (health bar, fire tiers), cyan/blue (EX meter), clean greys. Every individual sprite then takes ≤15 of those plus transparency, exactly like a CPS palette slot. Snap to 12-bit (`0x11` steps) for arcade quantisation (see 2.4).
- Our HUD "signature" sub-palette (proposal, 5.4) is drawn from it.

### 4.5 Open-licensed placeholders

- **Boxer Game Character** — CC0, Raga2D; idle, walk fwd/back, 3 punches, block, hurt, dizzy, KO — practically a fighting-game state machine for free ([OpenGameArt](https://opengameart.org/content/boxer-game-character)). Cartoon style, not pixel; fine for logic testing.
- **Cat Fighter Sprite Sheet** — CC-BY 3.0, dogchicken; 50x50 → 64x64 frames; idle/walk/jump/attacks/spin kick ([OpenGameArt](https://opengameart.org/content/cat-fighter-sprite-sheet)). Credit required.
- **LuizMelo — Martial Hero 1/2/3, Fantasy Warrior** — CC0, credit appreciated; full attack/hit/death sets ([Martial Hero](https://luizmelo.itch.io/martial-hero), [Martial Hero 2](https://luizmelo.itch.io/martial-hero-2), [Martial Hero 3](https://luizmelo.itch.io/martial-hero-3), [Fantasy Warrior](https://luizmelo.itch.io/fantasy-warrior)). Best pixel-art fighter placeholders available.
- **Kenney** — 60,000+ CC0 assets incl. the Particle Pack (80 files, 512x512, CC0) for sparks/smoke to downscale into placeholder hit effects ([kenney.nl particle pack](https://kenney.nl/assets/particle-pack)); plus CC0 UI packs and fonts.
- **OpenGameArt CC0 lists** — [CC0 resources](https://opengameart.org/content/cc0-resources), [2D complete characters](https://opengameart.org/content/2d-complete-characters); itch.io [free fighting assets](https://itch.io/game-assets/free/tag-2d/tag-fighting).
- Never use: Spriters Resource rips of Capcom sprites, "MUGEN" character packs (almost all are rips), fan-made SF fonts traced from logos.

---

## 5. Proposed visual bible

### 5.1 The virtual CRT

- **Virtual resolution 384x216, integer scale 5 → 1920x1080.** 384x216 is exactly 16:9 and keeps CPS width, so horizontal HUD proportions match the originals; we lose 8 rows versus 384x224 (12:7 ≈ 1.714 vs 1.778). Alternatives considered: 320x180 @6x (too coarse for names), 480x270 @4x (more room, less "arcade"). Stick with 384x216.
- All positions, sizes and motion are authored in virtual pixels and multiplied by 5 at the last step. No sub-pixel positions, no fractional scales, no rotation except 90° multiples and the pre-drawn slanted glyphs. Easing is done by stepping through integer offsets.
- Camera-safe zone: keep the centre 60% x 55% (virtual x 77–307, y 50–170) free of persistent elements; transient callouts may cross it.

### 5.2 HUD element map (virtual px; origin top-left)

| Element | Position / size | Style |
|---|---|---|
| **P1 (DJ) health bar** | x 12–156, y 10, 144x8 (144 px = 144 HP, a nod to SF2) | 1-px dark navy outline; yellow fill drains right-to-left toward centre; red "recoverable" trail that decays 1 px / 4 f; damage flash: bar whites for 2 f then shows red |
| **P2 (CHAT) health bar** | mirrored x 228–372, y 10 | same; drains left-to-right toward centre |
| **Centre emblem** | x 160–224, y 4–30 | our own 32x16 "VS" / "DJ" glyph instead of "KO" artwork; timer below |
| **Timer** | x 180–204, y 20, two 10x14 digits | counts the *current track's remaining time* in whole seconds, or 99→0 round timer in v3 |
| **Name plates** | under bars, y 20; P1 "OSH" left-aligned x 12, P2 "CHAT" right-aligned x 372 | 8-px font, white, 1-px black shadow; chat name plate shows top bits donor for 3 s on fight-back |
| **Round-win markers** | y 20, inner ends of bars (x 128–156 / 228–256) | 8x8 original icon (a vinyl record), up to 3 |
| **Portraits** (optional) | 24x24 at x 0–24 / 360–384, y 2 | Alpha/MvC-style face chips; DJ = mascot face, CHAT = crowd-mob face with 4 moods |
| **Super / "HYPE" meter** | bottom corners: x 8–120, y 198, 112x6, 3 segments; mirrored | blue-cyan fill (EX colour), "MAX" 3-letter sprite flashing 8 f on / 8 f off when full |
| **Combo counter block (P1)** | anchored x 20, y 60; numerals 20x28 each, stacked | 3S-style slam-in; rank word 8-px font below; whole block drops off-screen on reset |
| **Combo counter block (P2 chat)** | mirrored x 364 right-aligned | bits/subs stack identical mechanics |
| **Move callout** | centred on x 96 (P1 side), y 104; up to 16 glyphs of 12x16 slanted font | see 5.5 |
| **Now-playing ticker** | x 124–260, y 206, 136x8 | 8-px font marquee between the meters: "NOW PLAYING ▶ ARTIST — TITLE ▶ KEY/BPM"; orange on 50% black 1-px-outlined strip, attract-mode style |
| **Track-change "VS card"** | full-width band y 80–136 for 150 f | two diagonal wipes meet in the middle; left panel "NOW" + old title, right panel "NEXT" + new title; our own "VS" glyph; then wipes out. Replaces the SF2 "vs" screen |
| **Round banners** (v3) | centred 160x32 word-sprites | "ROUND 1", "FIGHT!", "K.O.", "PERFECT", "TIME OVER", "DOUBLE K.O." — our own lettering, slanted, with bevel |

Now-playing placement rationale: the bottom centre band is the one area of a fighter screen that is *never* occupied (super meters are in the corners, the fighters' feet end above it), and arcade attract-mode text lives there in the player's memory; it also sits below the DJ's hands on a typical top-down-ish camera framing. The VS card is the "big moment" presentation for a track change and doubles as a crowd-readable title card.

### 5.3 What is a sprite, what is bitmap text, what is procedural

- **Sprites (pre-cached PNG atlases):** bar frames and drain tiles, emblem, round markers, portraits, meter frames and MAX, hit numerals 0–9, rank/word banners, callout glyphs, hit sparks, lightning, fire tiles, dizzy ornaments, mascot frames, projectiles, VS-card wipes.
- **Bitmap text:** names, ticker, rank words, donor names, debug. Always BMFont atlases with baked outline/shadow.
- **Procedural (but pixel-snapped):** bar fill width, recoverable trail decay, meter segments, screen shake (integer offsets of the whole stage), darken overlay (solid colour quad at 60% alpha, no gradient), palette swaps on sprites via a 16-colour LUT shader (this is how escalation recolours the HUD cheaply, exactly as CPS did palette swaps), afterimage trails (previous frames re-drawn tinted at −4, −8, −12 px offsets).

### 5.4 Palette (from Endesga 32, 12-bit snapped)

- Outline / shadow: `#181425` (near-black navy) — never pure black, it reads as a hole over camera.
- Health yellow ramp: `#fee761` → `#feae34` → `#f77622`; damage red `#e43b44`, dark red `#a22633`; recoverable trail `#f6757a`.
- Meter cyan: `#2ce8f5` / `#0099db` / `#124e89`; "MAX" white `#ffffff` on `#ff0044` flashes.
- UI chrome greys: `#c0cbdc`, `#8b9bb4`, `#5a6988`, `#3a4466`.
- Escalation accents: green `#63c74d` (tier 1), yellow `#fee761` (2), orange `#f77622` (3), red `#e43b44` (4), magenta `#ff0044` (5), white-cyan strobe (6+).
- Gold bevel for numerals: `#ffffff` highlight, `#fee761` face, `#feae34` mid, `#b86f50` shade, `#181425` outline.

### 5.5 Move callouts

A callout is a word-sprite row ("BASSLINE SWAP!", "CUT!", "BACKSPIN!", "ECHO OUT!", "FILTER SWEEP!", "DOUBLE DROP!") built from a 12x16 slanted bevel glyph set (A–Z, 0–9, "!", "+", "x").

- **Pop-in:** 1 f at 3x scale (integer), 1 f at 2x, then 1x with a 2-px overshoot right and back — total 4 f. During the first 2 frames draw the word pure white (palette LUT "flash"), then normal colours. This mimics hit-stop + hit-flash.
- **Hold:** 36 f for a single move; while a chain continues, each new callout pushes the previous one down 18 px and dims it one palette step (max 3 visible).
- **Exit:** slide 24 px toward the screen edge over 6 f, then drop alpha in two steps (100 → 50 → 0; no smooth fade, CPS had none).
- **Accompanying spark:** a 16x16 hit spark plays once at the word's leading edge (3 frames, 2 f each) — this is the "impact".
- **Hit-stop analogue:** freeze every HUD animation (ticker, idle mascot, meter shimmer) for 6 f at each move pop. The whole overlay "stopping" for a tenth of a second is the single most Capcom-feeling thing we can do.

### 5.6 Escalation ladder (combo stack)

| Chain | Rank word (ours) | Numerals | Extras |
|---|---|---|---|
| 2–3 | "NICE" | 20x28 gold | one spark per hit |
| 4–6 | "SOLID" | same, LUT → yellow | sparks 24x24; 1-px screen shake 4 f |
| 7–9 | "WICKED" | LUT → orange | lightning arc 32x64 behind numerals (6 f loop); shake 2 px 6 f |
| 10–14 | "SAVAGE" | 2x taller numerals (digit sprite 40x56) | fire border: 16x16 animated tiles along top/bottom edges (8 f loop); afterimage trail on callouts |
| 15–19 | "LETHAL" | same, LUT → red | HYPE meter fills faster; "MAX" flashes; crowd (P2 side) portrait goes to "scared" |
| 20–29 | "MAXIMUM" | numerals strobe red/white 4 f | **super flash**: 60% dark overlay 12 f, HUD bars pop white 2 f, mascot does a super pose, screen shake 3 px 10 f, hit sparks everywhere (up to 12 on screen) |
| 30+ | "ULTRA" (KI homage, generic word) | rainbow LUT cycle every 2 f | fire border doubles, lightning on both sides, ticker replaced by scrolling "ULTRA COMBO" |

Reset after inactivity (configurable, default 2.5 s): numerals "drop" — fall 32 px with a 2-step bounce over 12 f, then vanish; rank word stays 24 f longer. Stack resets to 0 but the HYPE meter keeps its level.

### 5.7 Should the DJ be a sprite?

**Recommendation: no full fighter for the DJ; yes to a small mascot and portraits.** The webcam *is* P1's "character" and a 100-px-tall fighter idling in front of the DJ's face would compete with, not frame, the person. Three cheaper devices give the fighting-game read:

1. **Portrait chips** (24x24) in both name plates — the MvC/Alpha convention — with 4 moods each (idle, hype, hurt, KO). Cheap to draw, carries a huge amount of "fighting game".
2. **A corner mascot** (48x64) above the P1 super meter: an original character — proposal "**Wax**", a hooded vinyl-headed brawler whose head is a record (label = eye) and who idles with a slow bob, throws a punch per move callout, does a super pose at tier 6, gets dizzy (orbiting mini-records instead of stars) when chat lands a big hit, and falls at KO. 6–8 frames per state, 15 colours. Small enough that AI reference + hand clean-up is tractable.
3. **P2 "CHAT" as a crowd**, not a fighter: a 64x24 strip of 6 chibi heads that cheer, boo, throw things (bits = thrown coins arc left as 8x8 projectiles; a sub = a 24x24 "bass bomb" hurled across the top band; a raid = a wave of heads sliding in). Their mood swaps with the health balance. This is the SF2 background-crowd idea repurposed as an opponent, and it avoids ever needing a second full fighter.

If a full-size fighter is wanted later, it should be *behind the decks* bottom-centre at 64–80 px tall, only during super flash moments, as a cut-in — the KI/MvC "super portrait" convention — not a persistent idle.

---

## 6. Asset list

All sizes are **virtual pixels at 1x** (multiply by 5 for on-screen). Sheets are RGBA8 PNG, power-of-two, NEAREST, 1-px extrude. Memory figures are decoded GPU texture size (width x height x 4 bytes), which is what matters; PNG file sizes will be far smaller.

### v1 — HUD + callouts

| Asset | Frames / glyphs | Frame size | Notes |
|---|---|---|---|
| Health bar frame L/R | 2 | 148x12 | includes end caps |
| Health drain tiles | 16 | 8x8 | sub-tile drain states, SF2 style (or procedural; keep sprites for the stepped look) |
| Recoverable-trail tile | 1 | 8x8 | tinted procedurally |
| Centre emblem | 2 (normal, flash) | 32x16 | our "VS"/"DJ" glyph |
| Timer digits | 10 + colon | 10x14 | |
| Name-plate strip | 2 | 72x10 | |
| Round-win marker | 2 (empty, won) | 8x8 | vinyl icon |
| Super/HYPE meter frame | 2 (L/R) | 116x8 | |
| Meter segment fill | 4 (0,1,2,3) | 36x4 | or procedural |
| "MAX" | 2 (on, off) | 20x8 | |
| Hit numerals | 10 | 20x28 | gold bevel |
| Callout glyph set | 40 (A–Z, 0–9, ! + x space) | 12x16 slanted | baked outline + bevel |
| Rank words v1 | 3 ("NICE", "SOLID", "WICKED") | ≤64x12 | or bitmap text |
| Hit spark small | 3 | 16x16 | |
| VS-card wipe panels | 2 + 2 wipe masks | 192x56 | |
| Ticker strip bg | 1 | 136x10 | 9-slice |
| BMFont 8 px (Public Pixel / Kenney) | ~96 glyphs | 8x8 | .fnt + PNG |
| BMFont 16 px names (Kaph/Jersey) | ~70 glyphs | ≤12x16 | .fnt + PNG |

v1 sheets: `hud.png` 512x256, `font8.png` 128x128, `font16.png` 256x128, `digits.png` 256x64, `callout.png` 256x128, `vs.png` 512x128. **≈ 6 sheets, ≈ 1.1 MiB GPU.**

### v2 — Escalation effects

| Asset | Frames | Frame size | Notes |
|---|---|---|---|
| Hit spark medium / large | 4 / 6 | 24x24 / 32x32 | |
| Lightning arc | 6 | 32x64 | mirrored for P2 |
| Fire border tile | 8 | 16x16 | + 2 corner variants x 8 |
| Afterimage LUTs | 3 palettes | 16x1 | shader lookup textures |
| Big hit numerals | 10 | 40x56 | tier 4+ |
| Rank words v2 | 4 ("SAVAGE", "LETHAL", "MAXIMUM", "ULTRA") | ≤96x16 | |
| Super-flash burst | 8 | 64x64 | radial lines, white/cyan |
| Mascot "Wax" | idle 6, punch 4, super 8, hurt 3, dizzy 4, KO 6, win 4 = 35 | 48x64 | 15 colours |
| Dizzy mini-records | 4 | 8x8 | orbit procedurally |
| Portraits DJ / CHAT | 4 + 4 | 24x24 | |
| Darken overlay | — | — | procedural quad |

v2 sheets: `fx.png` 512x512, `mascot.png` 512x256, `digits_big.png` 512x64, `portraits.png` 128x64. **≈ 4 sheets, ≈ 1.6 MiB GPU.**

### v3 — Chat fight-back, damage, KO, rounds

| Asset | Frames | Frame size | Notes |
|---|---|---|---|
| Crowd heads | 6 heads x 4 moods x 2 f = 48 | 12x12 | P2 strip |
| Bit coin projectile | 4 | 8x8 | + 3-frame impact 16x16 |
| Sub "bass bomb" | 6 flight + 6 burst | 24x24 / 48x48 | |
| Raid wave | 8 | 96x24 | heads sliding in |
| Chat super ("raid"/"hype train") cut-in | 8 | 96x64 | |
| Bar damage flash tile | 2 | 8x8 | white / red |
| Round banners | 6 words ("ROUND 1/2/3" share digits, "FIGHT!", "K.O.", "PERFECT", "TIME OVER", "DOUBLE K.O.") | 160x32 | slanted bevel, own lettering |
| Round digits | 3 | 16x32 | |
| Damage number pop | 10 digits | 8x12 | shows HP taken, 3S-adjacent |
| Win-pose mascot extras | 6 | 48x64 | |
| KO fall mascot extras | 8 | 64x64 | |
| Continue countdown digits | 10 | 24x32 | optional attract mode |

v3 sheets: `chat.png` 512x256, `banners.png` 512x256, `mascot2.png` 512x256. **≈ 3 sheets, ≈ 1.5 MiB GPU.**

### Totals

- **13 atlases, ≈ 4.2 MiB of decoded texture at 1x virtual resolution** — trivial for an OBS browser source. Even if we pre-bake everything at 2x to allow half-step motion (not recommended), it is ≈ 17 MiB.
- Frame count to draw: roughly **120 HUD/UI tiles, ~130 glyphs, ~100 VFX frames, ~75 mascot frames, ~90 chat/banner frames ≈ 500 hand-finished frames** for v1–v3. For scale: a single SF2 character is 13–19 sheets of 16x16 tiles; one 3S character is ~1,000+ frames (23,039 / 20 characters). Our whole theme is smaller than one Alpha character — which is the point.

### Build pipeline (summary)

1. Author in Aseprite with Endesga-32 (12-bit snapped) as the master palette; each sprite ≤ 15 colours + transparency.
2. `aseprite -b *.ase --sheet-pack --extrude --sheet out/<name>.png --data out/<name>.json --format json-hash --list-tags --filename-format '{title}_{tag}_{frame}'`.
3. Fonts: rasterise chosen OFL/CC0 face at 8/16/32 px, paint outline/bevel in Aseprite, export BMFont `.fnt` + PNG.
4. Load with PixiJS `Assets`, set `scaleMode: 'nearest'` on every texture, render to a 384x216 `RenderTexture`, blit to the 1920x1080 stage with `scale.set(5)`.
5. OBS: browser source at exactly 1920x1080, "Shutdown source when not visible" off, no OBS-side scaling.

---

## Open questions / things to verify on footage before specifying

1. Exact 3S rank-word list and the hit-count thresholds that trigger each (we are inventing our own ladder regardless).
2. Frame timings for ROUND/FIGHT/KO cards in ST and 3S (count on a 60 fps capture).
3. ST super gauge exact position/size and the "SUPER" flash cadence.
4. Whether chat-fight-back damage should also reduce the *timer* (round-timer mode) or only health.
5. Licence text of "Fight!" font; Google Fonts specimen pages for Jersey/Micro 5/Tiny5 to confirm OFL (expected).
6. Whether NP3 exposes track remaining time to the theme runtime (the project memory notes the runtime receives `{track}` only) — decides whether the centre timer is track-time or a pure round timer.

## Sources consulted (fetched or snippet-verified this pass)

- Sanglard: [SF2 health bar](https://fabiensanglard.net/sf2_health_bar/), [SF2 paper trails](https://fabiensanglard.net/sf2_sheets/), [CPS-1 graphics](https://fabiensanglard.net/cps1_gfx/index.html), [CPSS explorer](https://www.fabiensanglard.net/cpss/)
- Hardware: [CP System](https://en.wikipedia.org/wiki/CP_System), [CP System II](https://en.wikipedia.org/wiki/CP_System_II), [CP System III](https://en.wikipedia.org/wiki/CP_System_III), [Data Crystal CPS2](https://datacrystal.tcrf.net/wiki/CPS2:Hardware_information), [System16 CPS2](https://www.system16.com/hardware.php?id=795)
- Timing: [mugen-net Research: SF2](https://mugen-net.work/wiki/index.php/Research:Street_Fighter_II), [Sonic Hurricane Impact Freeze](https://sonichurricane.com/?p=1043), [Sonic Hurricane Turbo Speed](https://sonichurricane.com/?p=1864), [Critpoints Hitstop](https://critpoints.net/2017/05/17/hitstophitfreezehitlaghitpausehitshit/), [Kotaku SF2 CPU](https://kotaku.com/how-street-fighter-iis-computer-opponents-cheat-to-kick-1838411348)
- HUD: [Rengrow SF2 UI wiki](https://github.com/Rengrow/Street-Fighter-II-Gamusinos-Fighters-/wiki/UI), [SRK 3S HUD](https://srk.shib.live/w/Street_Fighter_3:_3rd_Strike/HUD), [SRK 3S Super Meter](https://srk.shib.live/w/Street_Fighter_3:_3rd_Strike/New/Super_Meter), [SRK 3S Stun Meter](https://srk.shib.live/w/Street_Fighter_3:_3rd_Strike/New/Stun_Meter), [StrategyWiki SFIII Gameplay](https://strategywiki.org/wiki/Street_Fighter_III/Gameplay), [SuperCombo SSF2T HUD](https://wiki.supercombo.gg/w/Super_Street_Fighter_2_Turbo/HUD), [EventHubs HD Remix basics](https://www.eventhubs.com/guides/2009/jan/12/basic-gameplay-details-super-street-fighter-2-turbo-hd-remix), [ST Revival Double KO](https://www.strevival.com/2019/01/06/the-oddities-of-the-double-ko-in-st/), [Wikipedia SFA3](https://en.wikipedia.org/wiki/Street_Fighter_Alpha_3), [Wikipedia SF Alpha](https://en.wikipedia.org/wiki/Street_Fighter_Alpha), [Wikipedia SF III](https://en.wikipedia.org/wiki/Street_Fighter_III), [Wikipedia MvC2](https://en.wikipedia.org/wiki/Marvel_vs._Capcom_2:_New_Age_of_Heroes), [Guinness SF3 frames](https://www.guinnessworldrecords.com/world-records/98823-most-frames-of-animation-in-a-2d-fighter-videogame), [TASVideos KI combo names](https://tasvideos.org/3251S), [KI wiki Combo Breaker](https://killerinstinct.fandom.com/wiki/Combo_Breaker)
- Art technique: [TabNews SF2/CPS-1](https://www.tabnews.com.br/rafael/curiosidades-sobre-o-street-fighter-ii-e-a-placa-de-arcade-cps-1), [Siliconera Akiman](https://www.siliconera.com/former-capcom-developer-akiman-on-designing-the-iconic-characters-of-street-fighter-ii/)
- OBS/scaling: [OBS forum browser source scaling](https://obsproject.com/forum/threads/browser-source-option-to-scale-instead-of-stretch.83508), [GamePretty Aseprite in OBS](https://gamepretty.com/aseprite-how-to-use-pixelart-in-obs/)
- Fonts: [Kenney fonts (OGA)](https://opengameart.org/content/kenney-fonts), [Public Pixel](https://ggbot.itch.io/public-pixel-font), [Pixel Operator](https://www.dafont.com/pixel-operator.font), [monogram](https://datagoblin.itch.io/monogram), [Kaph](https://ggbot.itch.io/kaph-font), [Thaleah](https://tinyworlds.itch.io/free-pixel-font-thaleah), [BoldPixels](https://yukipixels.itch.io/boldpixels), [Press Start 2P](https://fonts.google.com/specimen/Press+Start+2P/about), [Karmatic Arcade](https://www.dafont.com/karmatic-arcade.font), [Joystix](https://www.dafont.com/joystix.font), [Fight! font write-up](https://designbeep.com/2026/03/02/fight-pixel-font/), [PixiJS 8 BitmapText](https://pixijs.com/8.x/guides/components/scene-objects/text/bitmap), [load-bmfont](https://cdn.jsdelivr.net/npm/load-bmfont@1.4.2/README.md)
- Tools: [Aseprite CLI](https://www.aseprite.org/docs/cli/), [Aseprite on itch](https://dacap.itch.io/aseprite), [LibreSprite](https://cdn.jsdelivr.net/gh/libresprite/libresprite@master/README.md), [Pixquare](https://apps.apple.com/app/id1659428179), [free-tex-packer](https://github.com/odrick/free-tex-packer), [TexturePacker PixiJS tutorial](https://www.codeandweb.com/texturepacker/tutorials/how-to-create-sprite-sheets-and-animations-with-pixijs5)
- AI generators: [PixelLab ToS](https://www.pixellab.ai/termsofservice), [GameDev AI Hub RD vs PixelLab](https://gamedevaihub.com/retro-diffusion-vs-pixellab/), [Retro Diffusion itch](https://astropulse.itch.io/retrodiffusion/comments), [Ludo roundup](https://ludo.ai/compare/best-ai-pixel-art-generators), [Ludo vs Scenario](https://ludo.ai/compare/ludo-vs-scenario), [FreeGameSprites 2026](https://freegamesprites.com/en/news/ai-pixel-art-generation-2026-tools-and-workflows)
- Palettes/placeholders: [Lospec Endesga 32](https://lospec.com/palette-list/endesga-32), [Lospec arcade tag](https://lospec.com/palette-list/tag/arcade), [Lospec SNES tag](https://lospec.com/palette-list/tag/snes), [OGA Boxer](https://opengameart.org/content/boxer-game-character), [OGA Cat Fighter](https://opengameart.org/content/cat-fighter-sprite-sheet), [LuizMelo Martial Hero](https://luizmelo.itch.io/martial-hero), [LuizMelo Fantasy Warrior](https://luizmelo.itch.io/fantasy-warrior), [Kenney Particle Pack](https://kenney.nl/assets/particle-pack), [OGA CC0 resources](https://opengameart.org/content/cc0-resources)
