# 11 · Questions for Triode (2026-10-06)

Open questions on design, functionality, platform and workflow. Each one is numbered so you can
answer by number. Each states our current default, so "default ok" is a full answer. Some
questions are new; others pull together questions scattered through `03` §6 and `09`.

Posted as https://github.com/dfigravity/nowplaying-theme-sdk/issues/1 (2026-10-06); answers there
or in Discord.

Already settled by you (thanks): we work in a fork of the SDK
(https://github.com/dfigravity/nowplaying-theme-sdk), and iteration 1 is one side only, no PvP.

## D · Design

**D1. The solo HUD.** With no opponent, a health bar has nothing to drain it. We turned the
top-left bar into the HYPE (super) bar, show BPM in the centre digits, and leave the right half
empty for the camera. (The preview's `?solo` mode; spec in `art/README.md`.) Does that read
right to you, or did you picture a drain in iteration 1, such as a stamina bar that idling
drains?
*Default:* HYPE bar, no health in iteration 1.

**D2. What is "something" in iteration 2?** The options we see:
- (a) chat as P2, our `02` §5;
- (b) DJ vs DJ on one rig in a back-to-back set, with decks 1/3 against decks 2/4;
- (c) DJ vs DJ across two streams, with NP3 relaying events between two overlays;
- (d) the track as a "boss" whose bar is its duration.
*Default:* (a), because it needs nothing new from NP3 beyond `np:community`. (c) is the most
exciting, but it is your infrastructure.

**D3. The centre digits.** Today they show BPM, because a theme gets the track's duration but
no playback position. Would you rather they showed time remaining on the on-air track? That
needs position or remaining time from NP3. Rekordbox exposes it to you; CDJs over Pro DJ Link
send it every 30 ms.
*Default:* BPM until a position arrives.

**D4. Loudness.** The top tier (40 hits) puts fire on both screen edges, lightning on both
sides, and rainbow numerals. Is that too much as a default for a stream overlay? We'd like an
intensity option (low / normal / max), which needs `np:options`.
*Default:* normal, which caps at tier 5's look until options exist.

**D5. Mascot and portraits.** "Wax", a hooded brawler with a vinyl record for a head, stands in
the bottom-left corner. Do you have any NP3 brand or gallery guidelines that a mascot should
respect (colours, tone, nothing that reads as a person)?
*Default:* keep Wax.

**D6. The theme's public name.** "Street Fighter" is Capcom's trademark, and we have kept every
asset original for that reason. The name should follow. Some candidates: **MIX FIGHTER**,
**DECK FIGHTER**, **COMBO DECK**, **SPIN FIGHTER**. Do you have a preference, or a naming
convention for gallery themes?
*Default:* "Street Fighter" stays a working title only.

**D7. Specials.** These are the command-input moves in `10` §2: SUB CANNON, CROSSFIRE, FULL
HANDOVER, BLACKOUT DROP, THE LONG GAME and LEVEL UP from today's data, plus RISING STORM,
SPIN CYCLE, ECHO SLAM and CUE STORM once events exist. Are any DJ moves missing, or are any
names you'd veto?

**D8. Sound.** Optional hit and announcer effects, off by default, or none at all? A sound in a
stream overlay ends up in the stream mix.
*Default:* none in iteration 1.

## F · Functionality

**F1. Where gestures are recognised** (repeats `09` Q3). Desktop app, mix processor, or the
SDK on raw events?
*Default:* NP3 emits named gestures, and the SDK ships the same recogniser for the playground.

**F2. Where specials are recognised.** Specials are patterns over moves inside a musical window
(`10` §1). We planned to recognise them in the theme. Would you rather NP3 emitted specials too,
so other themes could use them?
*Default:* in the theme, because they are game rules, not gestures.

**F3. Beat phase.** Combo windows are measured in bars. Today we anchor a bar clock on play and
cue presses, which drifts. Can NP3 send `beat.tick`, or a phase, from any source? CDJs over Pro
DJ Link do; Rekordbox with the FLX10 may not.
*Default:* the anchored clock, with "on the one" bonuses switched off.

**F4. When `np:track` fires.** On deck load or on on-air change? The VS card ("NOW vs NEXT")
should play when the new track takes over the mix, not when it is loaded.
*Default:* we treat the on-air change as the trigger, if we can tell which it is.

**F5. Persistence.** Should stats such as best combo of the set and total hits survive an OBS
reload? Is `localStorage` reliable in the NP3 overlay origin, or is there an NP3-side store?
*Default:* `localStorage`, reset at the start of each set.

**F6. Several copies of the overlay.** If the theme is open in OBS and in the dashboard preview
at the same time, each scores on its own. Is that expected, or should the preview tell the theme
it is a preview (`np:visibility` or a flag)?
*Default:* the preview runs a quiet demo mode.

**F7. Simulated source.** We score nothing while `mixer.sourceId == "simulated"`. For the
playground and the gallery thumbnail, is an autoplay demo, like our preview, welcome?
*Default:* yes, an attract-mode demo.

**F8. Options to expose** (needs `np:options`): P1 name, intensity, solo or versus, health
anchor, SFX, which specials are on.
*Default:* hard-coded until options reach custom themes.

## P · Platform and SDK

**P1. Size.** The theme bundles Pixi 8 plus about 60 KB of PNG art, roughly 1.4 MB raw and
about 350 KB gzipped. Is there a size limit or budget for themes?

**P2. Rendering.** Is a WebGL canvas fine in themes, and are there guidelines for frame rate or
CPU? We run a 60 fps fixed step and stop drawing when idle.

**P3. Pull requests from the fork.** Do you want the two build patches as PRs now (image
imports in `theme-meta.mjs`, and `inlineDynamicImports`)? Is there a commit style or a tests
expectation?

**P4. Layout of the fork.** Is it fine for the theme to live at `src/themes/street-fighter/` in
the fork, as the other themes do? Or would you rather a theme of this size were its own package?

**P5. Distribution.** Will it be published to an NP3 theme gallery or uploaded privately, and
under what licence? The art and fonts are original, so we are free to choose.

## W · Workflow

**W1. Where to talk.** Discord for quick questions, and issues on our fork for anything that
needs a decision record?
*Default:* yes, issues on the fork.

**W2. First milestone.** What would you like to see first? We propose the solo theme running
in OBS from the fork, built against today's `np:mix`. That covers moves and combos from faders
and EQ, plus specials, with a short screen recording.

**W3. Gear.** Which controllers and mixers can you test on? We have a DDJ-FLX10. More labelled
recordings help the recognisers (`07` lists the remaining gestures).

**W4. Protocol proposal.** Have you had a chance to look at `03`? Its own questions are still
open (`03` §6, `09`).

*Reply in Discord or on the fork; we'll fold the answers back into `02`, `03`, `05` and `10`.*
