# djsf/ · fighting-game theme: planning, measurements and tools

The working material behind the fighting-game theme (working title "DJ Street Fighter"; the
public name is open, see question D6). This folder is not part of the SDK build: the theme
scanner only reads `src/themes/`, and `tsconfig` only includes `src/`.

Changes to anything here go through pull requests, like the code. Edit it here, so we all work
from one copy.

## Start here

| If you want… | Read |
|---|---|
| The end-to-end work in progress | PR #2 (`src/themes/pipeline-probe.tsx`) and its description |
| The open questions | issue #1 (the same text as `docs/11`) |
| The event protocol we proposed | `docs/03 Event protocol proposal.md`, then `docs/06` §A/§A2 (measured decimation), then `docs/07` (gesture ground truth) |
| The whole picture | `docs/00 Project summary.md` |
| The art and the animated preview | https://dfigravity.github.io/nowplaying-theme-sdk/demo/?solo · sheets on the `art-preview` branch · spec in `art/README.md` |

## Folder map

| Path | What it is |
|---|---|
| `docs/00`–`11` | summary, platform capability, game design, protocol proposal, visual bible, build plan, hardware matrix and data-path limits, gesture ground truth, art brief, cover note to Triode, specials and supers, questions |
| `docs/sdk-assets-and-dynamic-imports.patch` | the two build fixes a sprite theme needs (image imports in `theme-meta.mjs`, `inlineDynamicImports`) |
| `recordings/` | 2026-10-06 sessions with a DDJ-FLX10 + rekordbox. `np3-2026-10-06_105733.jsonl` interleaves raw MIDI, gesture-label markers and NP3 `np:mix` states (the NP3 account id is replaced with `redacted-user-id`). `midi-tap-*.jsonl` are raw Web MIDI taps |
| `tools/` | `detect_moves.py` (move detector over a recording), `compare_tap.py` (raw MIDI vs `np:mix`: counts, collapse ratios, latency), `slice_markers.py` (per-gesture breakdown), `midi_tap.html` (Web MIDI tap with gesture-label buttons; Chrome) |
| `research_notes/` | six sourced notes (NP3 platform + full FLX10 MIDI list, Pro DJ Link data model, other hardware ecosystems, rendering stack, game mechanics, visual style) |
| `spike/` | the Pixi 8 renderer spike that proved sprites ship inside a theme bundle (the source only, not the built bundle) |
| `art/` | the art pack's README (sheet contents, solo HUD layout, motion rules) and credits. The PNG sheets and the preview live on the `art-preview` branch |

## Notes

- Some docs refer to `../Now Playing 3 Overlays/…` or `recordings/np3-2026-10-05_*` and
  `np3-2026-10-06_103312.jsonl`. Those are in Osh's private workspace and are not published
  here. The key results are already in the docs.
- The tools are plain Python 3 with no dependencies, e.g.
  `python3 djsf/tools/compare_tap.py djsf/recordings/np3-2026-10-06_105733.jsonl`.
- Dates are 2026-10-06 unless stated. Measurements were taken against NP3 3.0.0-beta, before
  the `np:controller` feed existed. The probe in PR #2 is how we re-measure with it.
