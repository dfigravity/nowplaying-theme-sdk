# Now Playing 3 platform surface and DDJ-FLX10 MIDI implementation

Research note for the DJ Street Fighter overlay theme. Compiled 2026-10-06 from public sources only: the Now Playing marketing and help sites, the live overlay host JavaScript served by app.nowplayingapp.com, the `nowplaying-theme-sdk` repository (cloned to the session scratchpad at `sdk-upstream`), other public repositories under github.com/chrisle, AlphaTheta's official DDJ-FLX10 MIDI message list, and community Mixxx mappings. Where sources disagree, both versions are quoted and the disagreement is flagged.

Conventions: MIDI channels are quoted 1-based (as AlphaTheta prints them); status bytes are hex (`9n` = Note On on channel n+1, `Bn` = CC on channel n+1). Note/CC numbers are given in decimal with hex in parentheses where it matters.

---

## 1. Now Playing public surface

### 1.1 Sites, communities, products

| Surface | URL | Notes |
|---|---|---|
| Legacy marketing site (still serves Now Playing 2) | https://nowplayingapp.com/ | Headline "The Easiest Track ID App For Live Streaming DJs"; download links are still 2.6.9 (`Now Playing Setup 2.6.9.exe`, `Now Playing-2.6.9-arm64-mac.zip`). Links: /compatibility, /download, /tutorials, /support, /product/now-playing-pro, /release-notes, /triode, /company. |
| NP3 marketing site | https://preview.nowplayingapp.com/ | "Your tracks on screen. Automatically." Per-source landing pages such as https://preview.nowplayingapp.com/for/rekordbox and https://preview.nowplayingapp.com/overlays, plus /company and /pricing. |
| Web app / dashboard / overlay host | https://app.nowplayingapp.com/ | Next.js (Turbopack chunks). Overlay URLs are `https://app.nowplayingapp.com/overlay/<friendly-name-or-token>`. Custom themes upload at `/dashboard/overlays/configure` (path named in the SDK build script). |
| Help center | https://nowplayingapp.com/help/ (redirects to /help/guide/getting-started/) | `help.nowplayingapp.com/...` 301-redirects to `nowplayingapp.com/help/...` (relocated 2026-07-11 per changelog beta.4280). |
| Changelog | https://nowplayingapp.com/help/changelog/ | 3.0.0-beta.1061 (2026-01-11) through 3.0.0-beta.4683 (2026-09-29) at time of writing. |
| Discord | https://discord.gg/nowplaying (help-center sidebar); Triode's own server https://discord.com/invite/X8FhJj4mfx (linked from the check-in globe page) | Not fetchable without joining. |
| Triode | https://www.nowplayingapp.com/triode, https://twitch.tv/triodeofficial, https://x.com/triodeofficial, https://linktr.ee/triodeofficial | "I'm a DJ, producer, and developer based out of San Francisco, California." NP3 company page: "a small, independent software studio for the live-streaming and live-performance world." |
| Stream Globe Check-In (separate Triode product) | https://checkin.triodeofficial.com/ and https://checkin.triodeofficial.com/help | See section 5. |
| Old NP1/NP2 open-source app | https://github.com/chrisle/now-playing-app | TypeScript/React/Electron, "Send unified track data to a websocket and do presentation separately." Last updated 2021. |

Help-center sitemap (every page I saw in the sidebar; all under `https://nowplayingapp.com/help/`):

- Getting Started: `guide/installation/`, `guide/getting-started/`, `guide/onboarding/`, `guide/dashboard/`
- Sources: `guide/track-sources/` plus `prodjlink/`, `stagelinq/`, `rekordbox/`, `serato/`, `traktor/`, `virtualdj/`, `djay/`, `djuced/`, `mixxx/`, `spotify/`, `file-watcher/`
- Overlays: `guide/overlays/`, `guide/overlays/setting-up-obs/`, `guide/overlays/customizing/`, `guide/overlays/theme-gallery/`, `guide/overlays/theme-editor/`, `guide/overlays/custom-template/` (titled "Custom Themes")
- Destinations: `guide/destinations/` plus `twitch/`, `discord/`, `file-output/`, `webhooks/`, `lumia-stream/`, `midi-clock/`, `ableton-link/`
- Settings: `guide/settings/general-preferences/`, `track-cleanup/`, `on-air-detection/`, `account/`, `security/`
- Track History: `guide/history/overview/`, `sessions/`, `searching/`, `session-detail/`, `exporting/`, `retention/`
- Setup Guides: `setup/` (24 manufacturers; e.g. `/help/setup/numark/` has 276 guides)
- Technical Reference, Concepts: `reference/concepts/data-flow/`, `play-detection/`, `mix-processor/`, `track-enrichment/`, `output-services/`
- Infrastructure: `reference/architecture/system-requirements/`, `cloud-architecture/`, `failover/`, `data-storage/`
- Integrations: `reference/integrations/prodjlink/`, `stagelinq/`, `rekordbox/`, `onelibrary/`, `serato/`, `traktor/`, `djay/`, `virtualdj/`, `midi-bridge/`, `mixxx/`, `djuced/`, `midi-clock/`, `metadata/`, `spotify/`, `sam-broadcaster/`, `theme-sdk/`, `file-watcher/`, `ableton-link/`
- Accounts & Security: `reference/accounts/user-accounts/`, `overlay-tokens/`, `purchases/`
- Platform: `reference/platform/auto-updater/`, `reference/platform/headless/`

### 1.2 Supported sources and requirements

- NP3 marketing (preview site) lists 11 sources: "rekordbox, Serato DJ, Traktor Pro, VirtualDJ, djay Pro, Mixxx, DJUCED, Denon StageLinq, Pioneer PRO DJ LINK, Spotify, and universal file watcher." SAM Broadcaster is also an integration (shares a settings entry with Traktor since beta.3521).
- System requirements page: macOS 12 Monterey+, Windows 10 64-bit, no Linux; Rekordbox 6.x/7.x, Serato DJ Pro 3.x, Traktor Pro 3.x/4.x, djay Pro 5.x, VirtualDJ 2024+, DJUCED 6.x, Mixxx 2.4+, Engine DJ 3.x/4.x. PRO DJ LINK uses UDP 50000 (discovery), 50001 (beat), 50002 (status); "all devices must be on the same subnet".
- NP2 compatibility page (https://www.nowplayingapp.com/compatibility) still describes "Pioneer Rekordbox 7 (USB) ... all-in-one systems (XDJ, OMNIS, OPUS), controllers (DDJ), and players (CDJ)". The DDJ-FLX10 is never named on any Now Playing page; the MIDI Bridge page says the 61 Pioneer mappings cover "the DDJ-FLX and DDJ-REV lines", and the changelog (beta.1315, 2026-02-09) says "MIDI mappings added for 27 Pioneer DJ devices including DDJ-FLX series and CDJ/DJM setups."

### 1.3 Architecture (data flow, services, transports)

From `reference/concepts/data-flow/`, `reference/architecture/cloud-architecture/`, `reference/concepts/output-services/`, `reference/accounts/overlay-tokens/`:

- Pipeline: "DJ Software → Desktop App → Cloud → Overlay".
- Desktop → cloud: "an encrypted Socket.IO connection (WebSocket with HTTPS)". It sends three things: track events, controller state (continuously), and desktop state (every 20 seconds or on change).
- Cloud services (Python microservices in one Docker container supervised by s6-overlay, co-located with Redis on a Proxmox homelab LXC, GCP Compute Engine standby, Cloud SQL Postgres, Managed Redis, Cloudflare Tunnel/CDN, Backblaze B2 backups): **Track Service, Router Service, Overlay Service, Twitch Service, File Output Service, Mix Processor Service**, plus a Next.js web app. "The Router Service reads each enriched track from a Redis stream and pushes a job into a dedicated queue for every output type." Latency is described as "hundreds of milliseconds".
- Cloud → overlay: Server-Sent Events, not WebSockets. "Browser sources implement SSE natively and reconnect automatically". Each overlay load "Subscribes that browser's SSE connection to `user:{userId}:track` in Redis".
- Overlay URLs: friendly form `/overlay/brave-orange-sunset` (adjective-color-noun) or token form `/overlay/k7m3np9q-r4s8tv2w-fh3d5jxe-9mn2vq7s` (four 8-char segments from a 30-char alphabet, about 2 × 10^47 combinations). Read-only; resettable.

Observed in the live overlay host JS (fetched from `https://app.nowplayingapp.com/overlay/test`, chunks under `/_next/static/chunks/`), which is the authoritative description of what the overlay page actually does:

- Initial fetch `GET /api/tracks/current/{token}` → `{ track }`.
- `new EventSource("/api/tracks/stream/{token}")` with named events:
  - `connected`
  - `track:update` → `JSON.parse(e.data).payload` is the enriched track (`artworkUrl`, etc.); the host also calls `pushRecentTrack` to keep a recent-tracks list for the designer themes.
  - `mix-processor:update` → stored as `mixState`.
  - `settings:update` → `data.outputs.overlay.{theme, showArtwork, themeConfig, ...}`.
- Dashboard desktop state: `new EventSource("/api/desktop-state/stream")` with `connected` and `state-update`; state carries `trackSources`, `devices`, `hydrationProgress`, `statusMessages`, `midiCompatibility`, `midiBridgePlatform`.
- Query params on the overlay page: `?preview=1` (cycles mock tracks, listens for `np:preview` postMessages with `{animate}` from the dashboard), `?static=1` (no SSE), `?theme=`.
- Identifier strings present in the host bundle that confirm internal naming: `djStyle`, `crossfaderDeadZone`, `crossfaderMuteThreshold`, `crossfaderCuts`, `crossfaderDisabled`, `onAirFlag`, `channelFaders`, `mixState`, `protocol:1`.

### 1.4 MIDI Bridge (how NP3 reads the FLX10)

Source: https://nowplayingapp.com/help/reference/integrations/midi-bridge/ plus changelog.

- The bridge is "a helper tool bundled with Now Playing's desktop application" that "captures MIDI messages from all connected DJ controllers at once". On macOS it uses CoreMIDI's multi-client architecture so it can listen alongside rekordbox without blocking it. The desktop app launches it as a child process; it emits JSON lines to stdout; the desktop app decodes them, translates via controller-specific mappings, and forwards state to the cloud via Socket.IO.
- Message types captured: Control Change ("Faders, EQ knobs, crossfader, filter, jog wheels"), Note On/Off ("Play, cue, pad, loop buttons"), Pitch Bend ("Tempo fader position on some controllers"). Each captured event includes "the device name, channel number, CC or note number, value, and timestamp."
- Normalisation: "0–1 linear or -1 to 1 bipolar" (EQ/filter bipolar since beta.1173).
- Mappings: "approximately 98 controller mappings" (Pioneer DJ 61, Hercules 14, Numark 7, Denon DJ 6, Behringer 5, plus Roland, Reloop, Native Instruments); "auto-generated from the MIDI implementation charts"; "MIDI mappings now load from web API" (beta.1194) with "fuzzy device name matching" (beta.1223); "MIDI channel fader detection is now automatic based on controller mapping" (beta.1509).
- Platform: "fully supported on macOS but remains in development for Windows, pending the Windows MIDI Services release" (reference page), although the changelog records "Windows virtual MIDI port support added to midi-bridge" (beta.1373) and a fix for "MIDI capture on Windows" (beta.4269), so some Windows path exists.
- Multi-device: "MIDI processor supports multiple devices simultaneously", "hot-plug device detection", "Multi-port MIDI controllers now share state correctly" (beta.1173).
- Serato interplay (beta.4356, 2026-07-29): "Now Playing properly detects which song is being heard, reading your controller over MIDI together with Serato's internals." and "Serato supplies the faders and Now Playing fills in the knobs it doesn't send."

The exact normalised controller-state schema NP3 sends to the cloud is not published. The closest public artefact is https://github.com/chrisle/autopilot-mappings, whose README says the maps were converted from "a standardized JSON library of MIDI maps ... 288 devices, ~19k controls, all conforming to one schema" that "Now Playing 3 typed". That tells us NP3's internal control vocabulary (see 3.6): `play`, `cue`, `sync`, `volume`, `trim`, `eq_high`, `eq_mid`, `eq_low`, `pitch`, `jog_touch`, `jog_turn`, `key_lock`, `hot_cue`, `loop_in`, `loop_out`, `loop_active`, `filter`, `crossfader`, `master_volume`, `headphone_volume`, `headphone_mix`, each scoped to a deck.

### 1.5 Mix processor and on-air detection (djStyle presets)

Sources: https://nowplayingapp.com/help/reference/concepts/mix-processor/, https://nowplayingapp.com/help/reference/concepts/play-detection/, https://nowplayingapp.com/help/guide/settings/on-air-detection/.

Problem statement (settings page): "DJ software considers a track 'active' as soon as it's loaded into a deck, but loading a track is not the same as your audience hearing it."

State model (mix-processor page): **Mixer** (hardware controller with crossfader and channels), **Channels** (per-deck device, track, live signals), **Signals** (real-time values), **Score** ("Computed 0–1 likelihood the channel is on air"), **On Air** ("Current winning channel with debounce management").

Signals the processor can consume: channel fader (0–1), trim/gain (0–1), crossfader (−1 to 1, with a ±0.15 centre dead zone), EQ low/mid/high (−1 to 1), filter (−1 to 1), play state (binary), on-air flag ("PRO DJ LINK only" / "Pioneer DJM only"), master tempo (binary), jog touch (binary), loop active (binary); the settings page additionally lists master deck assignment and "Playback position indicators".

Three strategies (play-detection page):
- **BYPASS (Software Only)**: "Used when no hardware controller or mixer is connected." Emits each incoming track immediately.
- **SIMULATED (Hardware On-Air Flag)**: "Used when the connected hardware can report directly which channel is on air." (DJM via Pro DJ Link.) "no debounce guessing".
- **SCORING (Controller Signals)**: "Used when hardware is connected and provides mixer signals such as fader positions and EQ state, but no direct on-air flag is available." This is the FLX10 case.

Scoring rules: "The deck with the highest weighted score becomes the active track." Hard gates reset a channel's score to zero when the "Channel fader fully closed" or the "Deck fully stopped" (not playing or cueing). "A debounce timer holds the change until the new leader has maintained its position for a configured duration."

Preset weights published on the mix-processor page:

| Signal | House/Techno | Hip-Hop | Drum & Bass | Open Format |
|---|---|---|---|---|
| On-air flag | 0.20 | 0.15 | 0.20 | 0.20 |
| Channel fader | 0.25 | 0.18 | 0.25 | 0.25 |
| Play state | 0.15 | 0.15 | 0.20 | 0.20 |
| Crossfader | 0.02 | 0.25 | 0.02 | 0.05 |
| EQ low | 0.10 | 0.05 | 0.08 | 0.05 |

Presets exposed in Settings → On-Air Detection (debounce in ms): Default 300 ("Balanced settings that work for most mixing styles"), Bass/Dub 300, Drum & Bass 300, Hardstyle 250, Hip-Hop/R&B 200, House/Techno 1875 ("Long blends with bass swaps and extended fader transitions"), Trance 1000. A Custom style exposes individual weights and a debounce labelled Fast (≤250 ms), Medium (≤400 ms), Slow (≤700 ms) or Long. (The marketing copy says "open-format, techno, hip-hop, drum & bass, trance".) A separate **Track Update Delay** (0–300 s, beta.4652) holds a new track back "from the overlay, chat and history until it has been on air for the seconds you choose".

Debug screen (dashboard): "Visual DJ mixer display in the debug screen with EQ, filter, and crossfader" (beta.1509); "leads with the track that's on air, the channel that won it, and a health line" and "shows a live feed of everything happening on your account" (beta.4580); "score breakdown says when a channel fader is read through the mixer's on-air flag" and "log lines and bus messages as the services handle your tracks and faders" (beta.4634); "draws your rig's real channel count instead of always six" (beta.4613). Admins can "view other users' mix processor data in real-time from the debug page" (beta.1238). Session recording "captures your DJ sets with markers for replay and debugging" (beta.3376).

### 1.6 Overlays, themes, theme editor, custom themes

- Built-in themes (theme-gallery page): Default 800×150, Clean 1280×200, Kinetik 3D 1100×130, ASOT 2K3 900×200, Sideways 1000×180, In The Mix 1280×360 ("shows a card for every deck currently in the mix"), plus Defcon (beta.4445) and Basic. Host bundle description of In The Mix: "On-air track on top, every other audible deck stacked underneath during transitions".
- Theme Editor (visual designer, beta.4190/4263): track-data text (title, artist, BPM, key, previous track), static text, album art, custom image, shapes; enter/exit/idle animations; 1080p/720p/custom canvas; opens in its own window.
- Display duration: Never / 20 s / 30 s / 60 s (beta.4336). One-click "add to OBS" (beta.4445). Overlays can load from a custom URL (beta.4190).
- Custom Themes (https://nowplayingapp.com/help/guide/overlays/custom-template/): upload a `.np3theme` ("ZIP archives under the hood") via the Import button on the Overlays page. Limits: 25 MB, 500 files, 50 themes per bundle, 20 bundles per account; allowed types HTML/CSS/JS, PNG/JPG/WebP/SVG/GIF/ICO/AVIF, WOFF/WOFF2/TTF/OTF, JSON, source maps, text, Markdown. Runs in an iframe with `sandbox="allow-scripts allow-same-origin"` ("JavaScript executes and fetch() requests work against CDN assets, but cookies, popups, navigation, form submission, and pointer-lock are blocked"). Must declare `color-scheme: dark` to composite transparently. Messages: "`np:hello` — fires once when the iframe loads", "`np:track` — delivers track data on load and when tracks change", "`np:mix` — provides mix state (only for compatible setups)"; "All messages include `type` and `protocol` fields, with the current protocol at version `1`." Pro feature: "included with the one-time Now Playing purchase and the 30-day trial". NP2 `.html` themes import and run as-is (beta.4320) and "importing your Now Playing 2 custom theme no longer requires Pro" (beta.4480).

### 1.7 Destinations and chat integrations

- Available: Twitch Chat, Discord (webhook; per-session threads since beta.4525), LumiaStream, Ableton Link. Coming soon: File Output, Webhooks, MIDI Clock; OSC "rolling out" (preview site). No Kick or YouTube destination exists; YouTube/Mixcloud/1001Tracklists appear only as playlist export targets.
- Twitch (https://nowplayingapp.com/help/guide/destinations/twitch/): OAuth — "You'll be redirected to Twitch to authorize Now Playing. Only the permissions needed to post chat messages are requested." A separate account can be the bot (beta.3359). Service "rebuilt with TwitchIO" (beta.1670). Commands: `!song !trackid !id` (current), `!mix` (all audible tracks during a transition), `!nowplaying` (admin manual set), `!last` / `!lasttrack` (previous track), auto-announce toggle (beta.4590). Nothing reads bits, subs, raids or arbitrary chat for overlays.
- Webhook payload (coming soon): `{artist, title, album, bpm, key, artworkUrl}`, empty strings rather than omitted fields.

### 1.8 Pricing and the custom-theme requirement

- NP3 purchases page (https://nowplayingapp.com/help/reference/accounts/purchases/): "Now Playing 3 is sold as a **one-time purchase**, not a subscription." Pay-over-time $5/month × 8 = $40 via PayPal; 30-day trial with Pro from account creation. Preview pricing says Pro "$29.99 one-time; $39.99 launch price" (wording ambiguous on the page). Pro gates: "custom theme creation/editing, Twitch chat integration, non-overlay outputs, automatic track cleanup, and playlist exports" plus unlimited history (free = 30 days).
- NP2 Pro page still lists "$24.99 USD" one-time ("out of stock"); NP2 Pro had "Custom Overlays" in HTML/CSS/JS and "Websocket data output".
- SDK README wording differs: "Custom themes require an active paid subscription." Treat the help center (one-time purchase or trial) as current; worth confirming with Triode which copy is right.

### 1.9 Changelog milestones relevant to this project (all 3.0.0-beta.N)

- 1094 (2026-01-14): "MIDI processor sends controller state via Socket.IO"; "Normalize controller signals to 0-1 and -1 to 1 ranges"; "Add Socket.IO server for real-time desktop communication".
- 1173 (01-19): crossfader dead zone; bipolar EQ/filter; "Filter signal penalizes score when away from center"; multi-device MIDI; hot-plug.
- 1223 (01-21): "Add device name to mix processor channel state"; fuzzy device matching; "DJ mixer UI uses schema value ranges".
- 1315 (02-09): "MIDI mappings added for 27 Pioneer DJ devices including DDJ-FLX series and CDJ/DJM setups."
- 1405 (02-22): "On-air detection is now fully managed by the mix processor."; "track timeout safety net".
- 1509 (02-28): debug mixer display; "On-air detection now checks all MIDI ports for channel faders."
- 3090 (03-14): "Overlay theme SDK available for building custom overlays."
- 3463 (04-12): onboarding MIDI device selection; USB-to-MIDI mapping remembered.
- 3557 (05-08): "In the Mix" theme.
- 4190 (07-04): visual theme editor; "Custom Themes — upload your own overlay theme as a ZIP bundle".
- 4340 (07-25): "Custom theme bundles are uploaded as a .np3theme file. If you were building bundles from source, rebuild them with the theme SDK before uploading."
- 4343 (07-26): "Custom themes you upload now show over your video instead of on a white box."
- 4356 (07-29): MIDI + Serato fusion; channel fader off-by-one fix; crossfader end-stops fix; idle-controller flood fix.
- 4496 (08-30): Pro DJ Link "Bridge mode (experimental)" with DJM-A9 real faders.
- 4622 (09-18): six-channel rigs; "both the Stagehand bridge and the V10 MIDI maps now read channels 5 and 6" (Stagehand = AlphaTheta's PRO DJ LINK Bridge app).
- 4652 (09-26): Track Update Delay.

---

## 2. The theme SDK repository in depth

Repo: https://github.com/chrisle/nowplaying-theme-sdk ("Now Playing 3 Theme SDK"). Created 2026-03-11, pushed 2026-10-06, 1 star, 2 forks (`aivandelindt/nowplaying-theme-sdk` pushed 2026-09-05, `MrBenJ/nowplaying-theme-sdk` 2026-03-17), no tags, single branch `main`, no license file, `package.json` version `1.0.0`.

### 2.1 Every commit (newest first, author Chris Le)

| Date (PDT) | SHA | Message |
|---|---|---|
| 2026-10-05 21:48 | 475e322 | fix: announce theme readiness once |
| 2026-10-04 22:34 | dbd5865 | fix: cancel theme animation timers |
| 2026-08-26 00:15 | b8ad268 | feat: start a theme from a three-line example instead of the full Clean one |
| 2026-07-26 01:07 | c98aef7 | docs: explain which files are yours and how to upgrade the kit |
| 2026-07-26 01:07 | d3c125d | feat: pull the latest SDK into your clone with npm run upgrade |
| 2026-07-26 01:07 | 784e08d | feat: adding a theme no longer means editing SDK files, so updates never clobber your work |
| 2026-07-25 17:04 | 256f650 | fix: themes downloaded from the playground now render instead of showing nothing |
| 2026-07-25 17:00 | 69bfb83 | fix: uploaded themes now render instead of crashing on load |
| 2026-07-25 16:54 | d96f63d | feat: download your .np3theme straight from the theme playground |
| 2026-07-25 10:48 | fc80929 | refactor: ship the SDK as a standalone starter kit with only the Clean example theme |
| 2026-07-22 11:35 | 63d95d9 | feat: package themes as editable source bundles that rebuild on upload |
| 2026-07-08 23:43 | 375897c | feat: build a single-theme bundle from a converted NP2 theme |
| 2026-07-08 19:48 | 241b153 | feat: scaffold NP3 themes from NP2 sources with the convert-np2 CLI |
| 2026-07-03 16:55 | 045ed97 | Merge feat/np3-251-build-bundle: ship themes as uploadable ZIP bundles |
| 2026-05-30 08:19 | 803f54e | chore: drop transient peer:true flags from lock file |
| 2026-05-24 12:08 | 4b04b0c | feat: add build:bundle command to ship themes as uploadable ZIP |
| 2026-04-12 02:47 | be92b60 | chore: update lockfile |
| 2026-04-10 00:30 | 2727b2c | chore: update lockfile and remove unused variables in kinetik-3d theme |
| 2026-03-16 12:28 | d8aa867 | feat: add create-theme skill for Claude Code |
| 2026-03-16 00:56 | 83fd357 | Add theme customization panel and fix Kinetik 3D / Sideways animations |
| 2026-03-15 22:30 | a2633d2 | Add ASOT 2K3, Kinetik 3D, and Sideways themes to the SDK |
| 2026-03-11 08:33 | b2704b7 | Initial commit |

The two October commits are small: `475e322` adds a `useRef` guard so `np:ready` is posted once under StrictMode ("Announce once so the host does not resend its buffered state twice"); `dbd5865` makes `BaseOverlay` cancel pending timers on unmount/track change.

### 2.2 Files

`README.md`, `package.json` (deps `motion ^12`, `react ^18.3`, `react-dom`; dev `vite ^6`, `tailwindcss ^3.4`, `jszip`, `typescript ^5.7`), `bundle.config.json` (`{"name": "My Themes"}`), `index.html`, `vite.config.ts`, `vite.bundle.config.ts`, `tailwind.config.js`, `postcss.config.js`, `tsconfig.json`, `.gitignore`, `scripts/build-bundle.mjs`, `scripts/theme-meta.mjs`, `scripts/upgrade.mjs`, `scripts/vite-plugin-download.mjs`, `src/App.tsx` (playground), `src/main.tsx`, `src/index.css`, `src/types.ts`, `src/theme.ts`, `src/discover.ts`, `src/registry.ts`, `src/examples-registry.ts`, `src/mock-data.ts`, `src/bundle/entry.tsx`, `src/components/{album-art,base-overlay,download-bundle-button}.tsx`, `src/examples/{basic,clean}.tsx`, `src/themes/README.md`, `public/images/test-artwork/*.jpg`, `.claude/skills/create-theme/{SKILL.md,template.md}`.

### 2.3 The documented contract (README + `src/theme.ts`)

- A theme is one file in `src/themes/` (or `src/themes/<name>/index.tsx`) exporting `meta: ThemeMeta` and a default component. "Themes are **discovered, not registered**".
- `ThemeMeta`: `id` (`/^[a-z0-9][a-z0-9_-]{0,63}$/`), `name`, optional `description`, `width`, `height` ("used to size the browser source in OBS"), `fields: ThemeField[]` where `ThemeField = { key, label, type: "color"|"boolean"|"number"|"string"|"range", defaultValue, min?, max?, step? }`; dotted keys nest.
- `ThemeProps = { track: EnrichedTrack | null; [key: string]: unknown }`.
- `EnrichedTrack` (standalone copy; "The full type lives in the main project at packages/shared/src/types/generated/track.ts"): `id, artist, title, album?, label?, genre?, bpm?, key?, artworkUrl?, artworkUrlSmall?, signature, source, timestamp, enrichedAt`.
- `BaseOverlay({ track, renderTheme, animationTiming = {exitDuration: 1500, enterDuration: 1500} })` renders `ThemeRenderProps = { title, artist, label?, artwork?, isAnimating }`; lifecycle: `isAnimating` true → wait exit → swap track → 50 ms → wait enter → false. Shows "Waiting for track..." until the first track.
- Ownership split enforced by `scripts/upgrade.mjs`: yours = `src/themes/**`, `bundle.config.json`; ours = `SDK_PATHS` (`.claude/skills/create-theme`, `.gitignore`, `README.md`, `index.html`, configs, `public`, `scripts`, `src/App.tsx`, `src/main.tsx`, `src/index.css`, `src/types.ts`, `src/theme.ts`, `src/discover.ts`, `src/registry.ts`, `src/examples-registry.ts`, `src/mock-data.ts`, `src/bundle`, `src/components`, `src/examples`).

### 2.4 What `src/bundle/entry.tsx` actually forwards

The header comment declares the protocol:

```
{ type: "np:hello",  protocol: 1 }
{ type: "np:track",  protocol: 1, track, connected }
{ type: "np:mix",    protocol: 1, state }
```

Behaviour: reads `<meta name="np-theme" content="...">`, finds the theme in `USER_THEMES`, listens to `window` `message` events, and **only** handles `np:track` with `protocol === 1`, calling `setTrack(msg.track ?? null)`. It posts `{ type: "np:ready", protocol: 1 }` to `window.parent` once. It then renders `<Component track={track} />` — so in production a theme receives exactly `{ track }`. `connected` is typed but discarded; `np:mix` and `np:hello` are ignored; `meta.fields` values are playground-only (the dashboard's customisation panel is for built-in themes, and nothing in the bundle plumbs field values into a custom theme). A theme that wants mix state today must register its own `window.addEventListener("message", ...)` for `np:mix` alongside the SDK entry.

### 2.5 What the host actually sends (from the live app bundle)

The custom-theme host component in app.nowplayingapp.com, reconstructed from the minified chunk:

```js
function CustomThemeFrame({ track, mixState, connected, customThemeEntryUrl }) {
  const post = (msg) => iframe.contentWindow?.postMessage(msg, "*");   // only after onLoad
  useEffect(() => post({ type: "np:track", protocol: 1, track, connected }), [track, connected]);
  useEffect(() => { if (mixState) post({ type: "np:mix", protocol: 1, state: mixState }); }, [mixState]);
  return <iframe src={customThemeEntryUrl} title="Custom overlay theme"
                 sandbox="allow-scripts allow-same-origin"
                 onLoad={() => { post({type:"np:hello",protocol:1});
                                 post({type:"np:track",protocol:1,track,connected});
                                 if (mixState) post({type:"np:mix",protocol:1,state:mixState}); }} />;
}
```

So `np:mix` is live today whenever the account has a mixer-aware setup; `mixState` is whatever arrives on the `mix-processor:update` SSE event. The host does not currently react to the theme's `np:ready` in this component (the SDK comment says it exists "so the host can re-send any state it has buffered"; the resend may happen elsewhere or be planned).

Partial `mixState` shape, inferred from the built-in In The Mix theme's consumer code (field names are exact; the full set is not visible because the minifier only preserves accessed keys):

```ts
mixState = {
  onAir?: { currentOnAir?: { channelNumber: number } },
  channels: Array<{
    channelNumber: number,
    track: EnrichedTrack | null,            // title, artist, artworkUrl ...
    signals: { isOnAir: boolean, channelFader: number /* 0–1 */, ... }
  }>,
  mixer: { crossfader: number /* −1..1 */, ... }
}
```

In The Mix picks the on-air channel from `onAir.currentOnAir.channelNumber`, falling back to the first channel whose `signals.isOnAir === true`; other decks are shown when `isInMix(channel, mixer.crossfader, { faderThreshold: 0.1 })`; it rounds `signals.channelFader` to 0.05 steps for a fader-level bar. The help text also names per-channel `device`, `score`, trim, EQ, filter, play state, master tempo, jog touch and loop active as signals; expect those to exist on `signals` even though this bundle does not read them. Ask Triode for the `mix-processor:update` schema (packages/shared types) rather than guessing.

### 2.6 Bundle (.np3theme) format

`scripts/build-bundle.mjs`: typecheck → `vite build --config vite.bundle.config.ts` (library mode, ES, `entry.js` + `style.css`, `process.env.NODE_ENV` inlined to production) → staging:

```
manifest.json
shared/entry.js
shared/style.css
themes/<id>/index.html        # <meta name="np-theme" content="<id>">, html{color-scheme:dark}, transparent body, #root, <script type="module" src="../../shared/entry.js">
```

`manifest.json`: `{ version: 1, name, themes: [{ id, name, entry: "themes/<id>/index.html", description?, width?, height? }] }` (help center adds optional `thumbnail`; 1–50 themes). Zipped with JSZip (DEFLATE 6) to `dist-bundle/<slug>.np3theme`; `slug` = lower-cased name, non-alphanumerics → `-`, max 60 chars. The dev server exposes `GET /__np3theme/download` for the playground's "Download .np3theme" button (409 if a build is running). `scripts/theme-meta.mjs` bundles each theme with esbuild and a proxy stub for every bare/CSS import so `meta` can be evaluated in Node; validation errors (missing `meta`, bad id, duplicate id, no default export) fail the build.

Upgrade script (`npm run upgrade [-- --dry-run|--ref <tag>|--repo <url>|--force]`): shallow-clones the source repo, reads the *incoming* `SDK_PATHS`, mirrors directories (deleting files you added inside SDK folders), refuses to run with uncommitted edits to SDK files unless `--force`, merges `package.json` (upstream wins on keys it declares; your extra deps survive), and asserts no SDK path overlaps `src/themes` or `bundle.config.json`.

### 2.7 The Claude skill (`.claude/skills/create-theme/`)

`SKILL.md` front matter: `name: create-theme`, description "Create a new Now Playing overlay theme. Use when asked to create, scaffold, or add a new theme to the theme SDK.", `allowed-tools: Read, Write, Edit, Bash, Glob, Grep`. It prescribes the two-component pattern (inner component receives `ThemeRenderProps & CustomProps` and drives Framer Motion `useAnimation()` controllers from `isAnimating`; outer default export wraps `BaseOverlay`), the `meta` export, field types, the rule "Never edit `src/App.tsx`, `src/registry.ts`, or `bundle.config.json`", and a verification step (`npm run typecheck`, `npm run build`). "Important" bullets: use Tailwind; use Framer Motion; "The `isAnimating` flag drives the entire animation — do not use separate timers"; prefer transform/opacity. `template.md` is a full TSX skeleton with `__Name__`/`__kebab-name__` placeholders, `EXIT_DURATION`/`ENTER_DURATION` constants and the `animationTiming` calculation `(EXIT_DURATION + 0.1) * 1000`. Note the skill still imports from `"framer-motion"` while `package.json` depends on `motion` (Framer Motion's successor package); `clean.tsx` is the canonical reference.

### 2.8 Issues, PRs, planned features

- PR #1 (open, MrBenJ, 2026-03-17) "Add Glitched Theme to Theme SDK": adds a CRT-glitch theme, a `CLAUDE.md`, and README mention of `/create-theme`. Never merged (predates the July restructure).
- PR #2 (merged, chrisle, 2026-05-24) "feat: add build:bundle command to ship themes as uploadable ZIP": references Jira `NP3-251` (https://triodeofficial.atlassian.net/browse/NP3-251) and says the ZIP "validates against the server-side `readAndValidateBundle()` validator (companion PR np3#221)" — confirming a private `np3` monorepo.
- No GitHub issues besides the PR. No roadmap in the repo. Planned/implicit features visible only through protocol comments: `np:mix` (declared, not consumed), `connected` (declared, dropped), `np:ready` buffer resend.
- The help-center "Theme SDK" reference page (https://nowplayingapp.com/help/reference/integrations/theme-sdk/) is stale relative to the repo: it describes a Next.js harness, a `registerTheme` API, an `artworkUrl` prop and a `phase: 'enter' | 'visible' | 'exit'` prop, and says themes are "bundled into the Now Playing web app". The current SDK has none of these (Vite, folder discovery, `artwork`, `isAnimating`). Do not design against `phase`.

### 2.9 Other public repositories under github.com/chrisle (related ones)

| Repo | What it is | Reveals events / MIDI? |
|---|---|---|
| alphatheta-connect (TS, MIT, 26 stars) | PRO DJ LINK client; "used as part of Now Playing"; CDJ-3000/3000X, XDJ-XZ/RX/RX2/RX3, Opus Quad, DJM-V10 | Player state as `CDJStatus.State` (play, BPM, master); no MIDI, no FLX10 |
| alphatheta-connect-rs | Rust port of the above | — |
| alphatheta-emu | "Pioneer DJ / AlphaTheta players as virtual machines" | — |
| rekordbox-connect (TS, MIT) | SQLCipher master.db reader; events `ready`, `db-changed`, `tracks`, `history`, `error`; rowid-based history polling | No live deck state |
| onelibrary-connect | rekordbox OneLibrary `exportLibrary.db` reader | — |
| serato-connect (TS, MIT) | Session/history/crate/database reader plus Serato Remote (OSC) network mode with per-deck `deckChange`, `playhead`, `loopChange`, `mixerChange` | Yes: live deck events for Serato |
| traktor-connect | OGG Vorbis broadcast metadata | — |
| djay-connect, virtualdj-connect | NowPlaying.txt / M3U history readers | — |
| StageLinq (fork lineage), stagelinq-pcap | Denon StageLinQ | — |
| metadata-connect | Audio tag extraction | — |
| connector-ci | Shared CI for the connector libraries | — |
| autopilot-mappings | NP3's internal MIDI library (288 devices) converted to Autopilot `.map` JSON | Yes: control vocabulary and the FLX10 map (section 3.6) |
| pioneer-dj-usb-shell, cdj3k-mods, cdj3k-root, cdj3k-subucom-tools, rx3-toolkit, PrimeBox, dysentery (fork) | Hardware hacking | — |
| now-playing-app (2021), now-playing-theme-start (2022) | NP1/NP2 era | NP2 socket.io/websocket overlay feed |
| lumia-stream | Lumia Stream plugins ("User Commands plugin") | Chat-command related, not NP3 |
| kick-js (fork), Twitchat (fork), Developer-Docs (Lumia) | Chat tooling forks | Suggests the Kick bot for the check-in globe |
| stemd | Local stem separation (Rust) | — |
| conductor*, the-knowledge-releases, claude-* | Unrelated dev tooling | — |

---

## 3. DDJ-FLX10 MIDI implementation (official list)

Source: AlphaTheta, "DDJ-FLX10 List of MIDI message", `DDJ-FLX10_MIDI_Message_List_E1.pdf` (7 pages, © 2023 AlphaTheta Corporation), linked from https://support.alphatheta.com/en-US/articles/16716711647129?product=16715825715481 ("DDJ-FLX10 MIDI-compatible software"), file at https://downloads.support.alphatheta.com/software_info/dj-controllers/DDJ-FLX10/DDJ-FLX10_MIDI_Message_List_E1.pdf. (The old pioneerdj.com `/-/media/...` URLs now redirect to the support home.) Cross-checked against the community Mixxx mapping `res/controllers/Pioneer-DDJ-FLX10.midi.xml` (mixxxdj/mixxx PR #16539, https://github.com/mixxxdj/mixxx/pull/16539; also https://github.com/Loui1979/MIXXX-FLX10 and https://github.com/Veezuhz/Mixxx_FLX10_Controller_Mapping), which agrees with the PDF on every control I compared. VirtualDJ's hardware pages (https://virtualdj.com/manuals/hardware/pioneer/ddjflx10/layout/decks.html, `.../pads.html`, `.../mixer.html`) were used for control-surface semantics only.

### 3.1 Channel assignment

| MIDI channel (1-based) | Status nibble | Category |
|---|---|---|
| 1–4 | n=0..3 | DECK 1–4 (everything except performance pads) |
| 5 | m=4 | EFFECT (Beat FX section) |
| 6 | m=5 | (No Use) |
| 7 | m=6 | BROWSER plus mixer-global controls (crossfader, master, booth, headphones, mic, Sound Color FX, FX part select, Active Part double-press) |
| 8 / 10 / 12 / 14 | p=7,9,B,D | DECK 1–4 PERFORMANCE PADS (without SHIFT) |
| 9 / 11 / 13 / 15 | p=8,A,C,E | DECK 1–4 PERFORMANCE PADS (with SHIFT) |
| 16 | F | MIDI-OUT communication (host → controller illumination/jog display) |

Buttons send Note On with velocity `0x7F` on press and `0x00` on release ("OFF=0x00, ON=0x7F"). All deck controls on the right deck mirror the left deck on their own channel. "n" below means the deck's channel (1–4).

### 3.2 Transport, tempo, jog (DECK group)

| Control | Trigger | Ch | Msg | Data1 dec (hex) | Notes |
|---|---|---|---|---|---|
| PLAY/PAUSE | press | n | Note | 11 (0x0B); +SHIFT 71 (0x47) | MIDI-OUT echoes LED |
| CUE | press | n | Note | 12 (0x0C); +SHIFT 72 (0x48) | |
| JOG (Platter) rotate, **Vinyl On** | rotate | n | CC | **34 (0x22)** | relative: "Difference count value from previous operated. Turn clockwise: Increases from 65 (0x41). Turn counterclockwise: Decreases from 63 (0x3F)" |
| JOG (Platter) rotate, **Vinyl Off** | rotate | n | CC | **35 (0x23)** | same encoding |
| JOG (Platter) + 4 BEAT JUMP held | rotate | n | CC | 41 (0x29) | same encoding |
| JOG (Platter) +SHIFT | rotate | n | CC | 31 (0x1F) | search/seek; same encoding |
| JOG touch (platter) | touch | n | Note | **54 (0x36)**; +SHIFT 103 (0x67) | ON=0x7F while touched |
| JOG (Wheel Side) rotate | rotate | n | CC | **33 (0x21)**; +SHIFT 38 (0x26) | pitch bend / nudge; same relative encoding |
| TEMPO slider | slide | n | CC | MSB **0 (0x00)**, LSB **32 (0x20)**; +SHIFT MSB 5, LSB 37 | 14-bit; "−" side Min (0x00/0x00), "+" side Max (0x7F/0x7F) |
| BEAT SYNC | press | n | Note | 88 (0x58); long press 120 (0x78); +SHIFT 92 (0x5C) | |
| TEMPO RESET | press | n | Note | 65 (0x41); +SHIFT 96 (0x60) | |
| KEY SYNC | press | n | Note | 101 (0x65); long press 26 (0x1A); +SHIFT 100 (0x64) | SHIFT+KEY SYNC is the master-tempo/key-lock toggle in rekordbox |
| SLIP REVERSE | press | n | Note | 21 (0x15); +SHIFT 56 (0x38) | |
| QUANTIZE | press | n | Note | 53 (0x35); +SHIFT 104 (0x68) | |
| SLIP | press | n | Note | 64 (0x40); +SHIFT 23 (0x17) | |
| 4 BEAT JUMP ◀ | press / long / +SHIFT | n | Note | 94 (0x5E) / 112 (0x70) / 97 (0x61) | |
| 4 BEAT JUMP ▶ | press / long / +SHIFT | n | Note | 95 (0x5F) / 113 (0x71) / 98 (0x62) | |
| SHIFT | press | n | Note | 63 (0x3F) | per deck |
| DECK SELECT 3/1, 2/4 | press | 1/3 or 2/4 and 7 | Note | 114 (0x72) on the deck channel; 60 (0x3C) with velocity 0x7F = "control On" / 0x00 = "control Off" on each deck channel; +SHIFT 124/125 on ch 7 | tells the host which deck layer each side controls |

Jog encoding summary (matches the classic Pioneer convention): one CC per tick, value 0x40 is the centre, `0x41..0x7F` clockwise with speed as distance above 0x40, `0x3F..0x01` counter-clockwise with speed as distance below 0x40. Platter touch is a separate Note (54). Vinyl mode is signalled by which CC the platter uses (34 vinyl-on vs 35 vinyl-off), and seek is CC 31 (SHIFT held). The Mixxx mapping treats CC 0x22 as "scratch mode", 0x21 as "pitch bend", 0x1F as "Jog Press+Seek (loop adjust / needle seek)" and 0x26 as "Beatgrid adjust (Shift+Jog)".

### 3.3 Loops, cue call, Mix Point, Stems (Active Part)

| Control | Ch | Msg | Data1 dec (hex) |
|---|---|---|---|
| CUE/LOOP CALL ◀ | n | Note | 81 (0x51); +SHIFT 61 (0x3D) |
| CUE/LOOP CALL ▶ | n | Note | 83 (0x53); +SHIFT 62 (0x3E) |
| LOOP IN / 1/2X | n | Note | 16 (0x10); +SHIFT 76 (0x4C) |
| LOOP OUT / 2X | n | Note | 17 (0x11); +SHIFT 77 (0x4D) |
| 4 BEAT / EXIT (reloop/exit) | n | Note | 20 (0x14); +SHIFT 80 (0x50) |
| MIX POINT SELECT ◀ | n | Note | 89 (0x59); +SHIFT 73 (0x49) |
| MIX POINT SELECT ▶ | n | Note | 90 (0x5A); +SHIFT 66 (0x42) |
| MIX POINT LINK | n | Note | 74 (0x4A); +SHIFT 67 (0x43) |
| ACTIVE PART **DRUMS** | n | Note | 13 (0x0D) |
| ACTIVE PART **VOCAL** | n | Note | 14 (0x0E) |
| ACTIVE PART **INST** | n | Note | 15 (0x0F) |
| ACTIVE PART DRUMS, +SHIFT press twice (Stems split to other deck) | 7 | Note | 36/37/38/39 (0x24–0x27) for DECK 1–4 |
| ACTIVE PART VOCAL, +SHIFT press twice | 7 | Note | 40/41/42/43 (0x28–0x2B) |
| ACTIVE PART INST, +SHIFT press twice | 7 | Note | 44/45/46/47 (0x2C–0x2F) |

The three ACTIVE PART buttons are the per-channel stem toggles (rekordbox "Track Separation"); each press is a plain Note on the deck channel, and the LED state comes back on MIDI-OUT with the same note. There is no separate "MIX mode" message; in rekordbox the same buttons act as EQ-kill-style part mutes, which is why the Mixxx mapping labels 0x0D/0x0E/0x0F "EQ Low/Mid/High kill (stem btn)". Loop active/inactive is not reported as a dedicated input message; the host learns it only from its own state or from LED feedback (MIDI-OUT to the controller, not readable by a third party).

### 3.4 Mixer section

| Control | Ch | Msg | MSB / LSB dec (hex) | Range |
|---|---|---|---|---|
| CROSSFADER | 7 | CC | **31 (0x1F) / 63 (0x3F)** | 14-bit; "Min at left side, Max at right side" |
| CH FADER | n | CC | **19 (0x13) / 51 (0x33)** | 14-bit; "Min at bottom end, Max at top end" |
| FADER START (CH fader zero → not zero) | n | Note | 102 (0x66) "PLAY message only for CH fader start"; +SHIFT 93 (0x5D) "SYNC message"; not-zero → zero 82 (0x52) "CUE message" | only when fader-start is enabled |
| TRIM | n | CC | 4 (0x04) / 36 (0x24) | 14-bit |
| EQ HI | n | CC | 7 (0x07) / 39 (0x27) | 14-bit |
| EQ MID | n | CC | 11 (0x0B) / 43 (0x2B) | 14-bit |
| EQ LOW | n | CC | 15 (0x0F) / 47 (0x2F) | 14-bit |
| CH CUE (headphone PFL) | n | Note | 84 (0x54); +SHIFT 57 (0x39) | |
| MASTER LEVEL | 7 | CC | 8 (0x08) / 40 (0x28) | 14-bit |
| MASTER CUE | 7 | Note | 99 (0x63); +SHIFT 98 (0x62) | |
| BOOTH LEVEL | 7 | CC | 9 (0x09) / 41 (0x29) | 14-bit |
| CROSSFADER ASSIGN (per channel, 3-position) | n | Note | 22 (0x16) = A, 24 (0x18) = B, 29 (0x1D) = THRU; the selected one is sent with 0x7F and the other two with 0x00 | |
| HEADPHONES MIX | 7 | CC | 12 (0x0C) / 44 (0x2C) | 14-bit |
| HEADPHONES LEVEL | 7 | CC | 13 (0x0D) / 45 (0x2D) | 14-bit |
| MIC EQ HI / LOW | 7 | CC | 7/39 and 15/47 (same numbers as channel EQ, but on channel 7) | 14-bit |
| LINE/PHONO (CH 3/4) | 3/4 | Note | 70 (0x46): PHONO=0x00, LINE=0x7F | |
| INPUT SELECT (PC-A / LINE-PHONO / PC-B) | n | Note | 85/86/87 (0x55–0x57), selected = 0x7F | |
| MIC OFF/ON/TALKOVER | 7 | Note | 106/107/108 (0x6A–0x6C), selected = 0x7F | |
| SAMPLER CUE | 7 | Note | 105 (0x69); +SHIFT 110 (0x6E) | |
| SAMPLER VOL | 7 | CC | 3 (0x03) / 35 (0x23) | 14-bit |
| MASTER LEVEL METER | — | — | "without MIDI-control" | |
| CH LEVEL METER | n | CC (MIDI-OUT) | 2 (0x02) | host → controller, "Use when INPUT Selector is PC-A or PC-B" |

So every fader and knob on the FLX10 is 14-bit (MSB CC, LSB CC = MSB + 32), including the channel faders and crossfader. A reader that only parses the MSB still gets 128 steps.

### 3.5 Effect section (Sound Color FX, Beat FX, part select)

| Control | Ch | Msg | Data1 dec (hex) |
|---|---|---|---|
| COLOR knob CH 1–4 | 7 | CC | MSB 23/24/25/26 (0x17–0x1A), LSB 55/56/57/58 (0x37–0x3A); 14-bit |
| SOUND COLOR FX SPACE / D.ECHO / CRUSH / PITCH / NOISE / FILTER | 7 | Note | 0 / 1 / 2 / 3 / 4 / 5 (0x00–0x05); +SHIFT 8–13 (0x08–0x0D) |
| FX PART SELECT VOCAL / DRUMS / INST | 7 | Note | 27 / 28 / 29 (0x1B–0x1D); +SHIFT 30/31/32 |
| BEAT ◀ / BEAT ▶ | 5 | Note | 74 (0x4A) / 75 (0x4B); +SHIFT 102 / 107 |
| BEAT FX SELECT (rotary, one Note per effect) | 5 | Note | 32 (0x20) LOW CUT ECHO, 33 ECHO, 34 MT DELAY, 35 SPIRAL, 36 REVERB, 37 TRANS, 38 ENIGMA JET, 39 FLANGER, 40 PHASER, 41 STRETCH, 42 SLIP ROLL, 43 ROLL, 44 MOBIUS SAW, 45 (0x2D) MOBIUS TRI |
| BEAT FX CH SELECT (rotary) | 5 | Note | 16 (0x10) CH1, 17 CH2, 18 CH3, 19 CH4, 20 MASTER, 21 MIC, 22 (0x16) SAMPLER |
| LEVEL/DEPTH | 5 | CC | MSB 2 (0x02), LSB 34 (0x22); 14-bit |
| BEAT FX ON/OFF | 5 | Note | 71 (0x47); +SHIFT 67 (0x43) |

### 3.6 Performance pads (8 pads × 8 modes × 2 pages)

Pad presses are Note On/Off on the pad channel of the deck (8/10/12/14 without SHIFT; 9/11/13/15 with SHIFT). Note number = mode base + page offset + (pad − 1):

| Mode | PAGE 1 base | PAGE 2 base |
|---|---|---|
| HOT CUE | 0 (0x00) | 8 (0x08) |
| PAD FX 1 | 16 (0x10) | 24 (0x18) |
| BEAT JUMP | 32 (0x20) | 40 (0x28) |
| SAMPLER | 48 (0x30) | 56 (0x38) |
| KEYBOARD | 64 (0x40) | 72 (0x48) |
| PAD FX 2 | 80 (0x50) | 88 (0x58) |
| BEAT LOOP | 96 (0x60) | 104 (0x68) |
| KEY SHIFT | 112 (0x70) | 120 (0x78) |

Example from the PDF footnote: Hot Cue mode on DECK 1, PAGE 1 pads 1–8 are `97 00 hh` … `97 07 hh`; PAGE 2 is `97 08 hh` … `97 0F hh`. MIDI-OUT to the same note sets the pad colour ("lit in color specified in color number (1-127). OFF=0x00 (dimmer)"). "When switching the PAGE, MIDI for the pad changes." (The marketing pad modes "Scratch Bank" and "Pad FX" map onto PAD FX 1/2 and SAMPLER in this list; there is no separate scratch-bank note range.)

Pad mode buttons (deck channel n): HOT CUE mode 27 (0x1B) (long press 75, +SHIFT 105), PAD FX 1 mode 30 (0x1E) (+SHIFT 107), BEAT JUMP mode 32 (0x20) (+SHIFT 109), SAMPLER mode 34 (0x22) (+SHIFT 111). PAGE ◀ / PAGE ▶ send a mode-specific note: in HOT CUE / PAD FX 1 / BEAT JUMP / SAMPLER / KEYBOARD / PAD FX 2 / BEAT LOOP / KEY SHIFT mode, PAGE ◀ = 36/37/38/39/40/41/42/43 (0x24–0x2B) and PAGE ▶ = 44/45/46/47/48/49/50/51 (0x2C–0x33); their +SHIFT variants are 1–8 and 122–127/0. Because the page buttons encode the current mode, a listener can infer the active pad mode from them.

### 3.7 Browser section (channel 7)

BROWSE rotate CC 64 (0x40) (+SHIFT CC 100): relative, "Turn clockwise: 1 ～ 30 (0x01 ～ 0x1E)", "Turn counterclockwise: 127 ～ 98 (0x7F ～ 0x62)". BROWSE press (load) is deck-specific: Note 70/71/72/73 (0x46–0x49) for deck 1/2/3/4 (+SHIFT 93/109/94/111). BACK Note 101 (0x65) (+SHIFT 102). VIEW Note 122 (0x7A), long press 103, +SHIFT 104.

### 3.8 MIDI-OUT (host → controller), useful for understanding what rekordbox knows

Channel 16 CC/Note from the computer: DIGITAL MARKER per deck (CC 16–19 MSB / 48–51 LSB, 0–359 degrees), BPM per deck (CC 20–23 / 52–55, 0.0–999.9), Playing speed per deck (CC 24–27 / 56–59, −100.0%…+100.0%), Time minutes/seconds per deck (CC 66–73), Time mode per deck (Note 20–23, Elapsed 0x00 / Remaining 0x7F), Cue point angle per deck (CC 28–31 / 60–63, 0x7F/0x7F hides), Key (CC 73 on the deck channel, 0x00–0x18), Key change amount (CC 74), Key display format (Note 91 Classic/Camelot), Master tempo per deck (Note 32–35), MASTER (beat sync) per deck (Note 24–27), SYNC per deck (Note 28–31), Jog ring illumination per deck (Note 9–12), jog display show/hide (Note 93–96). These are output-only; a third-party listener on the controller's input port does not see them (and rekordbox owns the output port), but they document what the on-jog display is fed.

### 3.9 What Now Playing's own FLX10 map reads

From https://github.com/chrisle/autopilot-mappings/blob/main/Mappings/alphatheta-ddj-flx10.map ("Pioneer DJ / AlphaTheta DDJ-FLX10", 21 verified + 31 speculative bindings, converted from the NP3 library; MIDI channel "passed through 1-16"). Per deck 1–4 on channels 1–4: `play` note 11, `cue` note 12, `sync` note 88, `volume` cc 19, `eq_high` cc 7, `eq_mid` cc 11, `eq_low` cc 15, `trim` cc 4, `pitch` cc 0, `jog_touch` note 54, `jog_turn` cc 33 (relative), `key_lock` note 65. Global on channel 7: `crossfader` cc 31, `master_volume` cc 8, `headphone_volume` cc 13, `headphone_mix` cc 12. All agree with the PDF MSBs except two speculative ones worth flagging to Triode: `jog_turn` cc 33 is the wheel-side ring (pitch bend), not the platter (cc 34/35), and `key_lock` note 65 is TEMPO RESET (key lock / master tempo is SHIFT+KEY SYNC, note 100). No LSBs, no pads, no stems, no loop or filter controls are in NP3's FLX10 map, which is consistent with the mix processor only needing fader/EQ/trim/play/jog-touch signals. A second file, `other-ddj-flx10-prod.map` (40 verified / 86 speculative / 4 unusable), is a scraped third-party map whose assignments (hot cues as CCs on even channels, etc.) contradict the official list; ignore it.

Practical consequences for a theme that wants controller-driven events: NP3 today surfaces, at most, channel fader, crossfader, trim, EQ, filter (not mapped on the FLX10 — the COLOR knobs are on channel 7 and the map has no `filter` binding), play/cue state, sync, jog touch and master-tempo-ish flags per channel through `mix-processor:update`. Pad hits, stem toggles, loops, Beat FX and jog rotation are **not** in NP3's FLX10 map, so a Street Fighter theme that reacts to those would need either an extended mapping from Triode or a separate local MIDI listener feeding the overlay.

---

## 4. Rekordbox side: what NP3 can read beyond MIDI

- Rekordbox has no streaming overlay, chat or OBS integration of its own; the only official "now playing" surfaces are the history playlists written into the library database and, for hardware, PRO DJ LINK. Third-party tools (Now Playing, Prolink Tools https://selector.news/2021/02/05/prolink-tools/) exist because of that.
- NP3's rekordbox integration (https://nowplayingapp.com/help/reference/integrations/rekordbox/, https://nowplayingapp.com/help/guide/track-sources/rekordbox/, https://github.com/chrisle/rekordbox-connect): reads `master.db` ("SQLCipher-encrypted SQLite database" holding metadata and play history) with the key recovered from `options.json` (Blowfish-encrypted password), polls the history table by file mtime every ~2 s with a rowid cursor, and extracts title/artist/album/genre/label/BPM/key plus artwork via the metadata connector. "The exact column schema changes between Rekordbox 5, 6, and 7." Deck numbers "may be present in some Rekordbox versions but are not consistently available". The overlay updates "when rekordbox marks a track as on-air in its internal history", i.e. when the track goes live in performance mode, not on load.
- Explicit limitation: "The Rekordbox database shows what tracks are in your library and which have been played, but it does not provide live controller state" (fader, EQ, crossfader). Live state "requires the MIDI Bridge when hardware is connected". Note a contradiction: the user guide page says "connecting a MIDI controller or mixer alongside it has no effect on when the overlay updates" because rekordbox does not provide deck numbers, while the reference page and the changelog describe MIDI-driven on-air detection with rekordbox-era controllers (DDJ-FLX mappings were added for exactly this). Ask Triode which statement is current for the FLX10 (it matters for whether per-channel `track` is populated in `mixState.channels`).
- Play / cue / loop / hot-cue state: not available from rekordbox's database in real time. PRO DJ LINK (CDJs, XDJs, Opus Quad, and the FLX10 is not a Pro DJ Link device) exposes "the currently loaded track ID, play state, BPM, beat position, and tempo master flag", the mixer on-air flag, and hot/memory cues via metadata requests; active/passive/bridge modes; ports 50000–50002. OneLibrary (`exportLibrary.db`) is read for Pro DJ Link USB exports. For Serato, the Serato Remote OSC path delivers `deckChange`, `playhead`, `loopChange`, `mixerChange`, which is the nearest NP3 gets to per-deck live state on a laptop source; nothing equivalent exists for rekordbox.
- Net: with rekordbox + DDJ-FLX10, NP3's likely data sources are (a) `master.db` history for *which* track and its metadata, (b) the MIDI Bridge for faders/EQ/trim/play/jog-touch signals that the mix processor scores, (c) enrichment (Apple Music, Beatport, MusicBrainz, ISRC via Spotify/MusicBrainz) for artwork. Cue/loop/hot-cue/stem/pad activity is not captured anywhere in the published pipeline.

---

## 5. Twitch integration feasibility in this ecosystem

- Now Playing 3 does not forward Twitch chat, bits or subs anywhere. The Twitch Service is write-only chat (announcements and command replies) via TwitchIO with "Only the permissions needed to post chat messages". The overlay SSE stream carries only `connected`, `track:update`, `mix-processor:update`, `settings:update`, and the custom-theme postMessage protocol carries only `np:hello`, `np:track`, `np:mix` (plus `np:preview` for the dashboard). There is no "community", "chat" or "events" channel in either.
- Stream Globe Check-In (https://checkin.triodeofficial.com/) is Triode's existing chat-to-overlay product and shows how he builds that kind of pipeline: the DJ adds a Browser Source at `https://checkin.triodeofficial.com/<channelname>` (1080×1080), mods the bot (`/mod streamdjbot` on Twitch, `/mod thecheckinglobe` on Kick), and viewers type `!checkin <location>`; the streamer has `!globe reload|reset|hide|unpin <user>|mute|unmute|scale|angle|speed|maxpins|antispam`. Stats at `https://checkin.triodeofficial.com/stats/<channel>`. No OAuth is required from the streamer: the bot joins the channel by name, so authentication is simply "mod the bot".
- Transport (from the open-source OBS plugin that embeds Triode's looks, https://github.com/dfigravity/globe-overlay-for-obs, `data/looks/*.html`): the page loads `https://checkin.triodeofficial.com/socket.io/socket.io.js` with exponential retry, then opens a Socket.IO namespace per channel, `io("https://checkin.triodeofficial.com/<channel>", { transports: ["websocket"] })`, and listens for server events `connect`, `connect_error`, `globe_config`, `add_pin`, `add_sat`, `add_pins`, plus removal events. So Triode already runs a Socket.IO fan-out of chat-derived events to browser sources, separate from NP3's SSE. A `?demo` mode replays fake pins.
- Related signals of intent: chrisle's forks of `Twitchat` and `kick-js`, the `lumia-stream` plugin repo (chat "User Commands"), and Lumia's `Developer-Docs`.
- Feasibility options for DJ Street Fighter chat events, in rough order of robustness: (1) ask Triode to add an `np:community`/chat event (he has the pieces: TwitchIO already connected, Socket.IO infrastructure in the globe service, a `protocol` field for versioning); (2) have the theme itself open an anonymous Twitch IRC WebSocket (`wss://irc-ws.chat.twitch.tv:443`, `NICK justinfan…`) — the custom-theme sandbox is `allow-scripts allow-same-origin`, scripts and `fetch()` are permitted and nothing in the published rules forbids WebSockets, but a page CSP could; needs a quick empirical test, and it only yields chat text, not bits/subs, which need EventSub plus a token; (3) a separate local or hosted service (Socket.IO/SSE) that the theme connects to, mirroring the globe architecture. Whatever the path, keep the theme's own listener for `np:mix` since the SDK entry drops it today.

---

## Appendix A: quick-reference of NP3 identifiers worth reusing verbatim

`np:hello`, `np:track`, `np:mix`, `np:ready`, `np:preview`, `protocol: 1`; SSE events `connected`, `track:update`, `mix-processor:update`, `settings:update`, `state-update`; `mixState.onAir.currentOnAir.channelNumber`, `mixState.channels[].channelNumber|track|signals.isOnAir|signals.channelFader`, `mixState.mixer.crossfader`; settings keys `djStyle`, `crossfaderDeadZone`, `crossfaderMuteThreshold`, `crossfaderCuts`, `crossfaderDisabled`, `onAirFlag`; strategies BYPASS / SIMULATED / SCORING; services Track, Router, Overlay, Twitch, File Output, Mix Processor; control vocabulary `play, cue, sync, volume, trim, eq_high, eq_mid, eq_low, pitch, jog_touch, jog_turn, key_lock, hot_cue, loop_in, loop_out, loop_active, filter, crossfader, master_volume, headphone_volume, headphone_mix`.

## Appendix B: local copies

Scratchpad (session-only): `sdk-upstream/` (clone), `flx10_midi.pdf` + `flx10_midi.txt` (official list, text-extracted), `flx10_mixxx.midi.xml`, `alphatheta-ddj-flx10.map`, `other-ddj-flx10-prod.map`, `npchunks/` (overlay host JS). Re-download links are given inline above.
