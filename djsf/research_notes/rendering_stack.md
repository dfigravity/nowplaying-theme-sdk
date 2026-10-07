# DJ Street Fighter — Rendering / Engineering Stack Research

Date: 2026-10-06. Scope: how to render a 90s-arcade pixel-sprite overlay as a Now Playing 3 (NP3) theme that runs for 3-hour sets inside an OBS browser source on Apple Silicon.

Hard constraints this note respects (from the brief and from reading the SDK clone at a local clone of the SDK):

- Theme = React 18.3 + TS + Vite 6 + Tailwind 3 component, bundled by `scripts/build-bundle.mjs` using `vite.bundle.config.ts` in **library mode** into one `shared/entry.js` + `shared/style.css`, plus `themes/<id>/index.html` per theme, zipped as `.np3theme`. Nothing else is copied into the ZIP (`buildStaging()` only copies `entry.js`/`style.css`; `assetFileNames` would emit other assets to `dist-bundle/assets/` but they are never staged).
- Runs in an iframe (`sandbox="allow-scripts allow-same-origin"`) on `https://app.nowplayingapp.com/overlay/<slug>`; OBS 31/32 load that via CEF with Chromium 127 ([OBS 31 shipped Chromium 127](https://cyberinsider.com/?p=343590); OBS 33 moves CEF to 150/7871, [linuxiac](https://linuxiac.com/?p=219967)).
- Deps already in the SDK: `react`, `react-dom`, `motion` 12, `gsap` 3.15 + `@gsap/react`. `npm run upgrade` preserves dependencies you add (README: "dependencies you added stay").
- Target: 384x216 virtual canvas, 5x nearest-neighbour to 1920x1080, transparent, 60 fps, low idle cost, all sprites resident before the first move.

Where I could, I verified against source (obs-browser, pixijs, CEF headers) and measured sizes myself rather than trusting blog numbers. Measurements are marked "measured".

---

## 1. Renderer candidates

### Measured bundle sizes (jsDelivr dist builds, `gzip -9`, 2026-10-06)

| Library | Version (npm latest) | Minified | Gzipped | License | Last publish |
|---|---|---|---|---|---|
| pixi.js `dist/pixi.min.js` (whole library) | 8.22.0 | 841 KB | **237 KB** | MIT | 2026-10-01 |
| phaser 3 `phaser.min.js` | 3.90.0 | 1.20 MB | 315 KB | MIT | (3.x line) |
| phaser 4 `phaser.min.js` | 4.2.1 | 1.38 MB | 352 KB | MIT | 2026-07-09 |
| kaplay `dist/kaplay.mjs` | 3001.0.19 | 189 KB | 70 KB | MIT | 2025-06-15 (v4000 alpha 2026-05-12) |
| littlejsengine `dist/littlejs.min.js` | 1.25.0 | 436 KB | 135 KB | MIT | 2026-10-04 |
| excalibur `excalibur.min.js` | 0.32.0 | 574 KB | 147 KB | BSD-2-Clause | 2025-12-23 (0.33 alpha 2026-09-21) |
| three `three.module.min.js` | 0.186.1 | 393 KB | 90 KB | MIT | — |
| gsap core / PixiPlugin | 3.15.0 | 73 KB / 6.6 KB | 28 KB / 2.9 KB | GSAP standard (free incl. commercial, [Webflow announcement](https://webflow.com/blog/gsap-becomes-free)) | — |
| @pixi/react | 8.0.5 | 35 KB | 9 KB | MIT | 2025-12-01 |

Notes: the pixi number is the everything-included UMD; an ES import of `Application, Container, Sprite, AnimatedSprite, BitmapText, ParticleContainer, NineSliceSprite, Assets` tree-shakes to well under that (measure with the real build; expect ~150–200 KB gz). The Pixi raw size agrees with the third-party figure for 8.18.1 (857.9 KB / 244.4 KB gz, [depscope](https://depscope.dev/pkg/npm/pixi.js)). None of these sizes matters much for an overlay that loads once per stream; what matters is runtime cost and maintenance.

### PixiJS v8 — recommended

- WebGL2 by default with WebGPU optional (`preference: 'webgl' | 'webgpu'`, `preferWebGLVersion` default 2) ([ApplicationOptions](https://pixijs.download/release/docs/app.ApplicationOptions.html)). Use `preference: 'webgl'` in OBS: CEF off-screen rendering is documented for D3D/Metal/Vulkan shared-texture paths, and I found no evidence WebGPU is exercised in CEF OSR; WebGL2 in Chromium 127 is boring and reliable.
- Assets: `Assets.init({ manifest })`, `Assets.addBundle`, `Assets.loadBundle(name, onProgress)` where progress is 0..1 ([Assets API](https://pixijs.download/release/docs/assets.Assets.html), [manifest guide](https://pixijs.com/8.x/guides/components/assets/manifest)). Per-asset `data: { scaleMode: 'nearest' }` is passed to the texture loader.
- Spritesheet: TexturePacker/Aseprite JSON hash with `frames`, `meta.image`, `meta.scale`, optional `animations` map; `new Spritesheet(texture, json); await sheet.parse()` or `Assets.load('sheet.json')`; multipack via `linkedSheets`; you can pre-supply the texture with `data: { texture }` ([Spritesheet](https://pixijs.download/release/docs/assets.Spritesheet.html)).
- AnimatedSprite: textures array or `FrameObject { texture, time }` for per-frame durations, `animationSpeed`, `loop`, `autoUpdate`, `onComplete/onFrameChange/onLoop`, `gotoAndPlay` ([AnimatedSprite](https://pixijs.download/release/docs/scene.AnimatedSprite.html)).
- BitmapText + BitmapFont: loads AngelCode `.fnt`/`.xml` via Assets; `BitmapFont.install({ name, style, chars, resolution, padding, textureStyle: { scaleMode: 'nearest' } })` builds a glyph atlas at runtime from any loaded web font ([BitmapFont](https://pixijs.download/release/docs/text.BitmapFont.html), [bitmap text guide](https://pixijs.com/8.x/guides/components/scene-objects/text/bitmap)).
- NineSliceSprite for HUD bars (`leftWidth/topHeight/rightWidth/bottomHeight`) ([NineSliceSprite](https://pixijs.download/release/docs/scene.NineSliceSprite.html)).
- ParticleContainer for hit sparks: thousands of same-atlas particles, position dynamic by default, no children/filters ([ParticleContainer](https://pixijs.download/release/docs/scene.ParticleContainer.html)). `@pixi/particle-emitter` 5.0.10 still declares peer deps `<8.0.0` (checked `package.json` on jsDelivr) — do **not** add it; a 60-line emitter over `ParticleContainer` is enough for sparks.
- Context loss: `GlContextSystem.isLost`, `forceContextLoss()`; resources are recreated on the next render after restore ([GlContextSystem](https://pixijs.download/release/docs/rendering.GlContextSystem.html)).
- Texture GC: `textureGCActive`/`textureGCMaxIdle` were deprecated in 8.15 in favour of init options `gcActive`, `gcMaxUnusedTime`, `gcFrequency` (ms) ([garbage collection guide](https://pixijs.com/8.x/guides/concepts/garbage-collection)). This matters for us (section 3).
- Maintenance: releases every 2–6 weeks through 2026 (8.19 Jun, 8.20 Aug, 8.21 Sep, 8.22 Oct 1) ([releases](https://github.com/pixijs/pixijs/releases)). MIT.
- React integration: `@pixi/react` 8 is a thin JSX layer (`<Application>`, `extend()`, `useTick`, `useApplication`) but its `peerDependencies` are `react >= 19.0.0` and `pixi.js ^8.2.6` (verified from the published package.json). The SDK pins React 18.3.1 and the SDK's `entry.tsx` owns the root. **Skip @pixi/react**; mount Pixi imperatively into a `<div ref>` from one `useEffect`. That is also the right architecture for a game loop (section 5).
- GSAP: the shipped `PixiPlugin.js` 3.15 contains an `_isV8Plus` branch (`version >= 8`, remaps `line` to `stroke`), so GSAP tweens on Pixi objects work; register with `PixiPlugin.registerPIXI(PIXI)` ([PixiPlugin docs](https://gsap.com/docs/v3/Plugins/PixiPlugin/)).
- Overlay suitability: excellent. One canvas, batched sprite renderer, no DOM churn, the ticker can be stopped/started, texture memory is explicit.

### Phaser 3.90 / 4.2

Full game framework (scene manager, loader, input, arcade physics, tweens, camera, bitmap text, 9-slice). Phaser 4.0 "Caladan" shipped April 2026, 4.2.1 in July ([phaser.io](https://phaser.io/download/stable)). MIT. Pros: batteries included, pixelArt mode (`pixelArt: true` sets nearest + roundPixels), camera shake/flash built in. Cons for us: 315–352 KB gz, its own game loop and global `Phaser.Game` that wants to own the canvas and `document` events; React is purely a wrapper; the framework assumes it is the page. Fallback candidate only if you later want a real fighter with physics and scenes.

### Raw Canvas2D + atlas `drawImage`

Zero dependencies, `ctx.imageSmoothingEnabled = false` gives pixel-perfect nearest scaling, trivial to understand. A 384x216 backing store and a few hundred `drawImage` calls per frame is cheap even on CPU. Downsides: you write your own sprite/animation/9-slice/bitmap-font/particle/tween plumbing (all small, but it adds up to roughly what Pixi gives for free), no GPU batching (fine at this resolution), and any "super flash" colour effects (tint, additive blend, palette swaps) are slow or impossible without pixel loops; Canvas2D tinting is `globalCompositeOperation` tricks or pre-baked frames. It is the right **fallback**: the same virtual-canvas-and-CSS-scale strategy applies, and a Canvas2D path can even be kept as a runtime fallback when WebGL is unavailable (SwiftShader case, section 3).

### DOM/CSS sprites

`background-position` stepping with `image-rendering: pixelated` works for 5–20 elements, each a composited layer. Bad fit for hit sparks, screen shake over many elements, and per-frame z-order changes; layout/paint cost grows with element count and CEF software compositing (when hw-accel is off) makes many layers expensive. Keep DOM for the React shell (loading splash, debug HUD), not the game.

### three.js

90 KB gz, superb maintenance, but it is a 3D scene graph. Only reason to consider it: a 3D parallax stage (rotating arena, camera dolly) behind 2D sprites. That look is more "PS1" than "CPS-2"; the brief is 90s arcade, so no. If parallax is wanted, do 2–3 2D layers in Pixi.

### Lightweight 2D libs

- KAPLAY (ex-Kaboom): 70 KB gz, friendly API with sprites/anims/tweens, but the stable 3001 line last published June 2025 and the team is on a v4000 alpha; API churn risk. It also wants to own the canvas and loop.
- LittleJS: active (1.25.0 four days ago), MIT, pixel-art friendly, WebGL batching, but opinionated global-state engine with its own loop and input; integration into a React-hosted iframe is awkward.
- Excalibur: 147 KB gz, BSD-2, nice TypeScript API, scene/actor model, 0.x versioning with breaking changes between minors.

### Recommendation

**PixiJS 8 imperative (no @pixi/react) with a fixed-step game loop outside React; Canvas2D atlas renderer as the designed fallback behind a tiny `Renderer` interface.** Pixi gives atlases, animated sprites, bitmap text, 9-slice, particles, tint/blend modes and a stoppable ticker; everything else in the comparison either costs more (Phaser) or makes you write the plumbing (Canvas2D) or has maintenance/ownership issues (the small engines).

---

## 2. Pixel-perfect scaling

### Integer scaling for OBS

1920/384 = 5 and 1080/216 = 5 exactly, so the OBS path is an integer scale. Set `meta.width = 1920, meta.height = 1080` in the theme (the manifest uses them to size the browser source). Two ways to get 5x:

A. **Backing store at virtual resolution, scale with CSS.** Pixi `Application.init({ width: 384, height: 216, resolution: 1, autoDensity: false })`, then style the canvas `width: 1920px; height: 1080px; image-rendering: pixelated;`. Chrome has supported unprefixed `image-rendering: pixelated` and `crisp-edges` since Chrome 41 ([caniuse](https://caniuse.com/css-crisp-edges), [MDN](https://developer.mozilla.org/en-US/docs/Web/CSS/image-rendering)); Chromium 127 is fine. The GPU fills 384x216 pixels per frame and the compositor upsamples once with nearest filtering. Cheapest option by far; position rounding is automatic because there is no sub-virtual-pixel to draw into.

B. **Render at full resolution with nearest textures.** `resolution: 5` (or width 1920 / height 1080 with a 5x root container scale) and `roundPixels: true` plus all textures `scaleMode: 'nearest'`. Visually identical for integer scale, costs 25x the fill (still trivial on an M-series GPU), and it lets you cheat with smooth sub-pixel parallax if you ever want to. Rotated sprites look smoother (less authentic).

Pick A. It also makes CRT-style effects (if any) and screenshot tests operate on a 384x216 image.

### The NP3 dashboard preview (smaller, not 16:9)

The scale factor becomes non-integer, e.g. a 800x450 preview is 2.083x. Options:

- **Letterbox to the largest integer** (`k = floor(min(W/384, H/216))`, centre with CSS margins). Perfectly crisp, but at 2x inside a 800-wide preview you waste ~8% width. Best for faithfulness.
- **Fractional CSS scale with `pixelated`.** Chrome's `pixelated` performs plain nearest sampling at any scale, so some virtual pixels become 2 device pixels and some 3; static art looks fine, moving art shimmers slightly. Acceptable for a preview that is never broadcast.
- **Renderer resolution = fractional k.** Same shimmer as above plus more GPU work; no benefit.

Implement `fitVirtualCanvas(containerW, containerH, { integerOnly })` and choose `integerOnly = true` when `window.innerWidth === 1920 && innerHeight === 1080` (or simply whenever the computed k is within 0.01 of an integer), fractional otherwise. Use CSS `width/height` rather than `transform: scale()` on the canvas; both are nearest-filtered in Chromium when `image-rendering: pixelated` is set, but layout sizing is the path everyone tests.

### Nearest sampling per renderer

- Pixi: global default `TextureSource.defaultOptions.scaleMode = 'nearest'` before loading anything, or per asset `data: { scaleMode: 'nearest' }` ([TextureSource](https://pixijs.download/release/docs/rendering.TextureSource.html), [v8 migration](https://pixijs.com/8.x/guides/migrations/v8)). Leave `autoGenerateMipmaps` false (the default); mipmaps blur pixel art and add 33% memory. Runtime bitmap fonts: `textureStyle: { scaleMode: 'nearest' }` in `BitmapFont.install`.
- Canvas2D: `ctx.imageSmoothingEnabled = false` after every context size change (resizing a canvas resets state).
- CSS: `image-rendering: pixelated` on the canvas element (and on any `<img>` used in the React shell).

### Sub-pixel positions

With approach A, positions are in virtual pixels already; still `Math.round` every x/y you write from tweens (easing produces fractions, and Pixi with `roundPixels: false` will sample half-pixels → smeared edges). Set `roundPixels: true` on the renderer anyway as a belt-and-braces. Scale/rotation of sprites should be avoided except for deliberate effects; use pre-drawn frames.

### `devicePixelRatio` in OBS

obs-browser runs CEF in windowless (off-screen) mode: `settings.windowless_rendering_enabled = true` ([obs-browser-plugin.cpp](https://github.com/obsproject/obs-browser/blob/master/obs-browser-plugin.cpp)), and `BrowserClient::GetViewRect` returns `(0, 0, width, height)` of the source ([browser-client.cpp](https://github.com/obsproject/obs-browser/blob/master/browser-client.cpp)). It does **not** override `CefRenderHandler::GetScreenInfo` (grep of `browser-client.cpp/.hpp` finds no `GetScreenInfo`), so CEF's default screen info applies and the page sees `devicePixelRatio === 1`; the page renders at exactly the source's pixel size regardless of the Mac's Retina display. Therefore 1920x1080 CSS px = 1920x1080 source px; no DPR handling is needed in OBS. In the dashboard preview on a Retina Mac DPR is 2, which only makes integer scales "more integer". Verify once with `console.log(devicePixelRatio)` through remote debugging (section 7).

### CRT / scanlines

Cheap ways: a 384x216 (or 1920x1080) repeating 1px-line PNG overlaid with `mix-blend-mode: multiply`, or a Pixi filter on the root container. Over a **transparent** background, a full-frame scanline layer would darken the webcam too, which is not the arcade-cabinet look (the cabinet would show scanlines on everything, but then it is not an overlay). A filter on the sprite container limited to sprite alpha (multiply only where alpha > 0) works but forces a render-texture pass each frame; at 384x216 that is negligible. Recommendation: skip CRT globally; if wanted, bake 1-px darker lines into the callout/HUD sprites themselves, or apply a per-callout filter only while a callout is on screen.

---

## 3. Transparency and compositing inside OBS

### Transparent WebGL canvas

- Pixi: `backgroundAlpha: 0` (default is 1) and keep `premultipliedAlpha: true` (default) ([ApplicationOptions](https://pixijs.download/release/docs/app.ApplicationOptions.html)). The browser assumes a WebGL drawing buffer holds premultiplied colours; Pixi uploads PNG textures premultiplied and blends accordingly, so edges composite correctly. Turning `premultipliedAlpha` off while Pixi still writes premultiplied values causes dark fringes ([WebGL Fundamentals](https://webglfundamentals.org/webgl/lessons/webgl-qna-how-to-make-webgl-canvas-transparent.html), [James Fisher](https://jameshfisher.com/2020/08/12/why-does-my-webgl-alpha-transparency-look-wrong/)).
- The SDK's `index.html` already sets `html { color-scheme: dark; }` and transparent `html, body` — this is the real gotcha for iframes (Chrome paints a white base under light colour scheme). Keep it, and also keep the OBS default custom CSS `body { background-color: rgba(0,0,0,0); margin:0px auto; overflow:hidden; }` ([OBS KB](https://obsproject.com/kb/browser-source)).
- Additive blend ("super flash", sparks) is `blendMode: 'add'` on a sprite; over transparent regions the result is still premultiplied-correct.
- Expected PNG alpha: export sprites with straight alpha (normal PNG); Pixi premultiplies on upload (`alphaMode` default `premultiply-alpha-on-upload`).

### Hardware acceleration in OBS on macOS

- obs-studio defaults `General/BrowserHWAccel` to `true` (`config_set_default_bool(appConfig, "General", "BrowserHWAccel", true)` in [frontend/OBSApp.cpp](https://github.com/obsproject/obs-studio/blob/master/frontend/OBSApp.cpp)); macOS support arrived in OBS 26.1 via [PR #3934](https://github.com/obsproject/obs-studio/pull/3934) (CEF 4183). The toggle is Settings → Advanced → "Enable Browser Source Hardware Acceleration" and requires an OBS restart.
- With hw-accel on, CEF renders via its GPU process and hands OBS an IOSurface per frame (`OnAcceleratedPaint` → `gs_texture_create_from_iosurface` on macOS, browser-client.cpp). No CPU readback.
- With hw-accel off, `BrowserApp::OnBeforeCommandLineProcessing` appends `disable-gpu-compositing` unless `--enable-gpu` was passed ([browser-app.cpp](https://github.com/obsproject/obs-browser/blob/master/browser-app.cpp)). WebGL still exists but the composited frame is produced by the software compositor and copied via `OnPaint` → `gs_texture_set_image` every frame: a 1920x1080 RGBA readback (8.3 MB) per frame, ~500 MB/s at 60 fps. In that mode Chromium may also fall back to SwiftShader for WebGL; SwiftShader is a conservative CPU emulation of the whole GPU pipeline and is far slower than ANGLE on Metal ([microlink](https://microlink.io/blog/webgl-without-a-gpu)). The 384x216 backing store keeps our own WebGL work tiny, so even SwiftShader is survivable; the readback cost is the same for any 1080p browser source and is not ours to fix. Document for users: keep hw-accel on.
- Detect it at runtime: `gl.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL)` contains "SwiftShader" → show a one-time warning in the debug HUD and optionally switch to the Canvas2D fallback.

### Frame rate

obs-browser with shared textures and "Use custom frame rate" **off** sets `external_begin_frame_enabled = true` and `windowless_frame_rate = 0`, then calls `SendExternalBeginFrame()` from `BrowserSource::Tick()` every OBS tick (obs-browser-source.cpp lines ~213–228 and ~445–560). So the page's `requestAnimationFrame` runs at the OBS canvas rate: keep the OBS base canvas at 60 fps and leave custom FPS unchecked. The legacy default `fps` is 30 (`obs_data_set_default_int(settings, "fps", 30)`), which is where the old "browser sources are 30 fps" folklore comes from ([forum](https://obsproject.com/forum/threads/browser-source-not-look-like-runing-60fps-even-obs-and-program-is-60.72686)).

### Visibility and "Shutdown source when not visible"

- Defaults: `shutdown` false, `restart_when_active` false ([obs-browser-plugin.cpp](https://github.com/obsproject/obs-browser/blob/master/obs-browser-plugin.cpp); [OBS KB](https://obsproject.com/kb/browser-source)). With shutdown off, `Tick()` keeps requesting frames even when the source is hidden, so `document.hidden` stays false and the page keeps burning CPU/GPU in hidden scenes.
- OBS dispatches `obsSourceVisibleChanged` / `obsSourceActiveChanged` DOM events ([obs-browser README](https://github.com/obsproject/obs-browser)). Whether those reach a cross-origin iframe is not documented; the host page certainly receives them. Ask the SDK author to forward them as `np:visibility` messages (section 8). Until then: pause the loop when `document.hidden`, when no `np:mix` update has arrived for N minutes (deck idle), and expose a `visible` flag in the dev HUD.
- Recommend users enable "Shutdown source when not visible" only if they switch scenes a lot; reload cost is one full asset load (served from HTTP cache, so ~1–2 s plus texture upload).

### Context loss over a 3-hour session

GPU resets, display sleep, adapter switches, or too many contexts can fire `webglcontextlost`; handlers must `preventDefault()` on the lost event so the browser attempts a restore, stop the loop, and rebuild GPU resources on `webglcontextrestored` ([MDN](https://developer.mozilla.org/en-US/docs/Web/API/HTMLCanvasElement/webglcontextlost_event)). Pixi re-creates GPU resources on the next render after restore; our job is (1) stop the ticker on lost, (2) on restored re-run the warm-up pass (section 4) so every atlas is re-uploaded before the next combo, (3) if no restore within ~5 s, tear down and re-init the Application (and as a last resort swap to the Canvas2D renderer). Test with `gl.getExtension('WEBGL_lose_context').loseContext()` from the debug HUD.

### Texture memory budget

- RGBA8 is 4 bytes per texel: 1024² = 4 MiB, 2048² = 16 MiB, ten 2048² = 160 MiB (the brief's figure). We need far less: a full 384x216 frame is 83k texels (324 KB). Two fighters at 64x96 with 40 frames each = 491k texels; HUD, callouts, numbers, sparks maybe another 500k. Everything fits in **two to four 1024² atlases (8–16 MiB GPU)**. Keep atlases ≤ 2048² and avoid power-of-two padding waste by packing tightly.
- Mipmaps off (default) → no +33%.
- Pixi GC: an atlas not drawn for `gcMaxUnusedTime` is unloaded from the GPU and re-uploaded on next use, which is exactly the late pop we must avoid (the KO sheet may sit unused for 40 minutes). Set `gcActive: false` at init (or `texture.source.autoGarbageCollect = false` per atlas — check the exact option names for the installed 8.x). With ≤16 MiB resident this is safe.
- CPU side: decoded `ImageBitmap`s for the same atlases cost the same again in RAM, plus base64 strings if assets are inlined (section 4). Still under 100 MB total; negligible next to Rekordbox.

---

## 4. Asset pipeline

### Sprite sheets

- Formats Pixi reads natively: TexturePacker "JSON (Hash)" and "JSON (Array)" (`frames`, `meta.image`, `meta.scale`, trimmed `spriteSourceSize`/`sourceSize`, `rotated`) plus an `animations` map; Aseprite's `--format json-hash|json-array` is the same shape with `frames[*].duration` (ms) and `meta.frameTags[{name, from, to, direction}]` ([Aseprite CLI](https://www.aseprite.org/docs/cli/)). Pixi ignores `duration`/`frameTags`, so write a 30-line adapter: tag → `FrameObject[]` with `time = duration` so AnimatedSprite honours per-frame timing, and `direction` → loop/pingpong.
- Free tooling: `free-tex-packer-core` 0.3.9 (MIT, "only critical bugs will be fixed" per the author, but stable) exports JSON hash/Pixi format with trim/extrude/padding ([free-tex-packer](https://github.com/odrick/free-tex-packer)); Aseprite CLI (`--sheet --data --format json-hash --sheet-pack --list-tags --trim --extrude --shape-padding 2`) is the better choice if art is drawn in Aseprite because tags and durations come for free.
- Bleeding: with nearest sampling and integer positions, bleeding only happens if a frame's edge texel is sampled at exactly a half-texel boundary; it is rare but shows up with scaled/rotated sprites. Use `--shape-padding 2` (or TexturePacker shape padding ≥ 2) and `--extrude 1` for anything that will rotate or scale; keep `--trim` on but note Pixi restores trimmed offsets via `spriteSourceSize` so anchors stay correct. Disable rotation in the packer (rotated frames add a transform; pointless at this scale).
- 9-slice HUD bars: author 3-pixel corners and 1-pixel repeatable edges; `NineSliceSprite` scales edges (stretch, not tile). For a stepped "health" bar, draw the fill as a separate 1xN sprite scaled in width in whole virtual pixels.

### Bitmap fonts

- Formats: AngelCode BMFont `.fnt` (text or XML) + PNG pages; Pixi's `bitmap-font` loader accepts `.fnt`/`.xml` URLs and parses text or XML by content (`loadBitmapFont.ts`). Tools: [SnowB BMF](https://snowb.org) (browser, exports `.fnt` XML + PNG, project active April 2026), [AngelCode BMFont](https://angelcode.com/products/bmfont/) (Windows), Hiero (libGDX, Java). [msdf-bmfont-xml](https://github.com/soimy/msdf-bmfont-xml) produces SDF/MSDF only — the wrong tool for crisp pixel fonts (SDF implies linear filtering; Pixi forces `scaleMode: 'linear'` when `distanceField` is present).
- Runtime alternative with no font atlas to ship: load a pixel TTF/WOFF2 (e.g. Press Start 2P, OFL, native 8 px; or a hand-drawn pixel font) via `FontFace`, `await document.fonts.load('8px "Press Start 2P"')`, then `BitmapFont.install({ name: 'arcade', style: { fontFamily: 'Press Start 2P', fontSize: 8, fill: '#fff' }, chars: [...], resolution: 1, padding: 0, textureStyle: { scaleMode: 'nearest' } })`. Rasterising a pixel font at its native size with resolution 1 yields crisp glyphs; big combo numbers are the same font at 16/24/32 px (integer multiples) or dedicated number sprites. BitmapText then stamps glyphs from the atlas — "perfect for HUDs, score counters, timers" ([guide](https://pixijs.com/8.x/guides/components/scene-objects/text/bitmap)).
- Recommendation: hand-drawn number/callout sprites for the hero elements (kerning and outlines are art), runtime `BitmapFont.install` for everything secondary.

### Preloading with progress and the "INSERT COIN" splash

1. React shell mounts a DOM splash immediately (pure CSS, tiny inline PNG/SVG, text "LOADING… INSERT COIN", a 0–100% stepped bar).
2. `Assets.init({ manifest })` with one bundle `boot` (splash sprites, numbers font) and one bundle `game` (everything else). `await Assets.loadBundle('game', p => setProgress(p))`.
3. **Warm-up render**: the first draw of a texture is when it is uploaded to the GPU, and the first use of each pipeline (sprite, bitmap text, particle, nine-slice, filter) compiles shaders. After loading, build an off-screen container that contains one Sprite from every atlas page, one BitmapText per font, one ParticleContainer with one particle, one NineSliceSprite, any filter you will use, render one frame with it at alpha 0 (or inside a 1x1 render texture), then remove it. Without this, the first "BASSLINE SWAP!" of the night stutters.
4. Flip splash → game only after the warm-up frame; emit `np:ready` to the host only then (today `entry.tsx` sends `np:ready` on mount; the theme can send its own second-stage ready or just hold state until loaded).
5. Canvas2D fallback uses `createImageBitmap(blob)` / `img.decode()` per atlas to decode off the main thread; the same manifest drives it.

### Shipping assets given the SDK constraint

Facts first:

- Vite **library mode ignores `build.assetsInlineLimit` and always inlines imported assets as base64** ([Vite build options](https://vite.dev/config/build-options#build-assetsinlinelimit)). `vite.bundle.config.ts` uses `build.lib`, so today any `import atlas from './atlas.png'` already becomes a data URI inside `entry.js` with no change at all. The `assetFileNames: 'assets/[name][extname]'` rule in that config never fires for images.
- `app.nowplayingapp.com` is behind Cloudflare (`server: cloudflare`, `content-encoding: br` on both `/` and `/overlay/test`, 2026-10-06). Cloudflare compresses `application/javascript` on the fly and does not compress images ([Cloudflare compression](https://developers.cloudflare.com/speed/optimization/content/compression/)); if the theme files are served from the same zone, `entry.js` arrives brotli-compressed. I could not fetch a real theme's `entry.js` without a slug — confirm with DevTools on an installed theme.
- No `content-security-policy` header was present on `/overlay/test`; a `<meta>` CSP in the iframe document is still possible — check once with DevTools before relying on `data:`/CDN URLs.
- Pixi's texture loader accepts data URLs by MIME (`checkDataUrl(url, ['image/png', ...])`, `loadTextures.ts`), and `Spritesheet` can be given its texture directly (`data: { texture }` or `new Spritesheet(texture, json)`), so inlined atlases need no URL juggling. Bitmap fonts via `.fnt` URL want a real URL; with inlining, import the `.fnt` with `?raw` and construct `new BitmapFont({ data: bitmapFontTextParser.parse(text), textures })`.

(a) **Base64 inlining (works today).** Size math: base64 is ceil(n/3)*4 → +33%; 4 MB of PNG becomes 5.33 MB of JS source. Brotli/gzip of base64-encoded, already-compressed data recovers most of that: typical results are "comparable to the original", roughly +2–10% over the raw PNG ([phpied](https://www.phpied.com/?p=1338), [W3C www-svg thread](https://lists.w3.org/Archives/Public/www-svg/2014Jan/0120.html)), so ~4.2–4.4 MB on the wire if the host compresses, 5.4 MB if it does not. Costs: `entry.js` is parsed as one module (V8 handles multi-MB string literals fine, but the decoded string stays resident, ~5 MB), and the ZIP's own DEFLATE will not shrink base64 much (expect ~4.5 MB zipped; the 25 MB cap is far away). Benefit: no SDK change, no hosting, no CORS, no cache headers, no version skew between JS and art. Pixel-art PNGs are small anyway: a 1024² indexed PNG of 90s sprite art is typically 50–200 KB, so a complete game is likely 1–2 MB of PNG, not 4.

(b) **Extend `scripts/build-bundle.mjs` to ship files.** Minimal, upgrade-safe proposal to the SDK author: after `buildStaging()` writes `themes/<id>/index.html`, copy an optional per-theme folder `src/themes/<id>/public/**` to `staging/themes/<id>/public/**` (skipping dotfiles like the existing walker does), and add `"assets": "themes/<id>/public/"` to the manifest entry. In `buildStaging()`:

```js
import { cpSync, existsSync } from "node:fs";
// inside the per-theme loop, after writeFileSync(index.html):
const pub = join(ROOT, "src/themes", theme.id, "public");
if (existsSync(pub)) {
  cpSync(pub, join(dir, "public"), {
    recursive: true,
    filter: (src) => !basename(src).startsWith("."),
  });
}
```

The theme resolves URLs against the document, not the module: `new URL('public/atlas.png', document.baseURI).href` (document = `themes/<id>/index.html`; `import.meta.url` would point at `shared/entry.js`). The allowed-file-type list already includes png/webp/json/woff2, so the validator would accept it; the open question is whether the host serves arbitrary files from the ZIP at their paths — it must at least serve `shared/*` and `themes/*/index.html`, so probably yes, but the author has to confirm. Also propose a 500-file / 25 MB sanity check in the script and a `.np3ignore`-style skip for `*.aseprite` sources. (An alternative is to drop `build.lib` for a normal Rollup `input` build with `base: './'`, let Vite emit hashed assets next to `entry.js`, and copy `dist-bundle/assets/**` to `staging/shared/assets/**`; URLs then resolve via `import.meta.url` automatically. It changes more of the SDK's build semantics, so the explicit `public/` copy is the smaller ask.)

(c) **External hosting.** GitHub Pages (`Cache-Control: max-age=600`, not customisable), jsDelivr GH CDN (versioned tags are cached long-term), or Cloudflare R2 with custom headers; reference `https://…/dj-sf/v1.4/atlas.png?v=…`. Works in CEF, no build change, but adds a CORS/CSP dependency, a cold-start download on every OBS launch if cache is evicted, a second artefact to deploy in lockstep with the ZIP, and an outage mode where the overlay loads but the art does not. Not worth it for ≤ 5 MB.

**Recommendation: start with (a) — it needs nothing from anyone and the realistic payload is 1–2 MB — and request (b) in parallel so that if the art grows past ~5 MB (or a future theme wants audio/video) the clean path exists.** Keep the asset manifest abstract (`{ atlas: string | Texture, json: object }`) so switching from data URIs to `public/` URLs is a one-file change.

---

## 5. Game loop and React

### Keep the loop out of React

React is the shell: mount a `<div ref>` for the canvas, a splash overlay, an optional debug HUD, and nothing else re-renders during play. Everything that moves lives in plain TS modules.

- Create the Pixi `Application` in one `useEffect` with an `alive` flag and a cleanup that calls `app.destroy(true, { children: true, texture: false })`. `Application.init()` is async in v8 — guard against unmount before init resolves. `entry.tsx` wraps the app in `<StrictMode>`; in dev that double-invokes effects, so the engine must be idempotent (singleton per canvas, cancel pending init).
- Input: `entry.tsx` only forwards `np:track`; the `np:mix` stream (median 0.3 s, bursts at 100 ms per the protocol notes) is read by the theme's own `window.addEventListener('message')`. Push events into a ring buffer / tiny emitter (`mitt`-style, 200 bytes, or hand-rolled) that the game reads during its fixed step. No React state involved; the only React updates are splash progress and the debug HUD (throttled to 2 Hz).
- Loop: Pixi's `Ticker` (or a raw rAF) produces time; game logic consumes it in a fixed 60 Hz step with an accumulator, clamped to 0.25 s of catch-up to avoid the spiral of death, and render state is interpolated by `alpha = accumulator / dt` ([Fix Your Timestep](https://gafferongames.com/post/fix_your_timestep/)). At 384x216 with integer positions interpolation mostly affects timing precision, not smoothness, but it makes replay tests deterministic (section 7). Note the Ticker callback receives the `Ticker` in v8 (`ticker.deltaMS`), not a delta number.
- Pause: stop the ticker when `document.hidden`, when an `np:visibility` false arrives (if the host adds it), and drop to a 10 Hz "idle breathing" tick when no mixer event has arrived for 60 s. Resume instantly on the next event.
- Beat clock: track BPM arrives with `np:track`; keep `barPhase = ((now - anchor) * bpm / 60000) % 4`. Anchor on the first play event per deck (jog/play from `np:mix`) rather than track start, and re-anchor on each cue press; idle animations (HUD pulse, fighter stance bob, "ROUND 1" wobble) read `barPhase` so they breathe in time even without beat-grid data. Expect drift of a few ms per minute; re-anchoring on play/cue events keeps it honest.

### Tweens and GSAP/motion coexistence

- Simplest and most deterministic: a 40-line tween list inside the fixed step (`{ obj, prop, from, to, t0, dur, ease }`) with 4–5 easing functions (outBack for callouts, outExpo for numbers, steps() for frame-stepped "pixel" motion). It runs on the game clock, so replays and screenshot tests are exact.
- GSAP: `gsap.ticker` runs on its own rAF ([gsap.ticker docs](https://gsap.com/docs/v3/GSAP/gsap.ticker/)); PixiPlugin handles v8 (verified `_isV8Plus` in the shipped plugin). Fine for one-off cinematic sequences (KO slow-mo, "PERFECT" slam) if you accept that they run on wall time. If you want GSAP on the game clock, `gsap.ticker.sleep()` and drive `gsap.updateRoot(gameTimeSeconds)` from the loop. Also call `gsap.ticker.lagSmoothing(0)` so a hitch does not freeze tweens.
- motion: use it only for the DOM splash/HUD; its standalone `animate(0, 100, { onUpdate })` works on plain numbers ([motion.dev](https://motion.dev/docs/animate)) but adds nothing over the in-loop tween for canvas objects.
- Screen shake: offset the root container by rounded integer pixels for N steps, decaying; never shake the DOM canvas (it would re-layout).

---

## 6. Sound effects

- Autoplay: obs-browser appends `--autoplay-policy=no-user-gesture-required` to CEF unconditionally ([browser-app.cpp](https://github.com/obsproject/obs-browser/blob/master/browser-app.cpp)), so inside OBS an `AudioContext` starts `running` without a gesture. In a normal browser (the NP3 dashboard preview) Chrome creates it `suspended` until a gesture ([Chrome autoplay policy](https://developer.chrome.com/blog/autoplay)). One open question: the theme runs in an iframe; cross-origin iframes additionally need `allow="autoplay"` delegation unless the flag bypasses the permissions-policy check — test in OBS before promising sound. If the iframe is same-origin with the overlay page it is a non-issue.
- Routing: `reroute_audio` ("Control audio via OBS") defaults to **false** ([obs-browser-plugin.cpp](https://github.com/obsproject/obs-browser/blob/master/obs-browser-plugin.cpp)). Off: CEF plays through the system default output — on a DJ Mac that is often the same interface as Rekordbox's master, i.e. the SFX come out of the booth speakers and only reach the stream if desktop audio is captured. On: CEF audio is muted locally (`SetAudioMuted(true)`) and delivered to OBS as a source track via `OnAudioStreamPacket` (float planar), where it can be mixed and monitored; some users report crackle/first-10-ms repeats with this path ([forum](https://obsproject.com/forum/threads/browser-control-audio-via-obs-problem-with-sound-crackling.185292), [forum](https://obsproject.com/forum/threads/no-audio-in-browser-source-when-using-control-audio-via-obs.161356)).
- Musical reality: the stream audio is a mix at a known BPM and key; arcade "hadouken" samples are tonal and will clash. Noise-based hits, short clicks, coin blips at −18 dBFS are the only sounds that survive under house music, and even those compete with the DJ's own FX.
- Recommendation: **ship SFX as an option, off by default** (a `boolean` field in `meta.fields`), implemented with `@pixi/sound` 6.0.1 (MIT, peer `pixi.js ^8`) or a 30-line Web Audio sample player, decoded at load, with a master gain exposed as a field. Document the "Control audio via OBS" checkbox for anyone who turns it on.

---

## 7. Testing and dev tooling

- **Replay recorded postMessage logs.** The theme's input layer listens on `window` for `message`; `window.postMessage(msg, '*')` to self delivers through the same path, so a dev-only replayer (`import.meta.env.DEV` guarded; exposed as `window.__sf.replay(jsonlText, { speed })`) can read a `.jsonl` of `{ t, msg }` lines and dispatch at real time with `setTimeout` deltas (or step the fixed clock instantly for tests). Record logs with a 5-line snippet in the console of a live overlay (`addEventListener('message', e => lines.push({t: performance.now(), msg: e.data}))`). The SDK playground only sends tracks today, so this is the only way to drive `np:mix` locally.
- **Stress mode.** `window.__sf.stress({ eventsPerSec: 10 })` fires random fader/EQ/jog/play events; watch frame time and GPU memory for 10 minutes; assert no growth in `renderer.texture.managedTextures.length` or `performance.memory.usedJSHeapSize` (Chromium-only API).
- **Playwright screenshot regression.** Make the game deterministic: seeded RNG, `window.__sf.step(ms)` advancing the fixed clock, `animations: 'disabled'` for DOM. Screenshot only the canvas at virtual resolution (`locator('canvas').screenshot()` with the canvas CSS-sized 384x216 in the test page) and compare with `toHaveScreenshot({ maxDiffPixels: 0 })` — pixel art should match exactly; snapshots are suffixed per browser/platform and updated with `--update-snapshots` ([Playwright](https://playwright.dev/docs/test-snapshots)). Headless Chromium uses SwiftShader for WebGL unless told otherwise (`--use-angle=swiftshader` for a GPU-less CI runner; `--use-gl=angle --use-angle=metal` locally) ([microlink](https://microlink.io/blog/webgl-without-a-gpu)); since nearest-sampled integer-positioned sprites produce identical pixels on both, run CI on SwiftShader.
- **Frame time.** In the loop, keep an exponential moving average of `performance.now()` deltas and of the time spent inside `update` and `render`; show in the debug HUD; log a warning when a step exceeds 8 ms. In OBS, View → Stats shows "Frames missed due to rendering lag" (GPU compositing) and "Skipped frames due to encoding lag"; for 60 fps the render budget is 16.6 ms ([OBS forum](https://obsproject.com/forum/threads/understanding-rendering-lag-acceptable-threshold.100352/post-391941)). Baseline the stats with the source hidden, then visible, then under stress mode.
- **Profile the real CEF.** Launch OBS with remote debugging: `/Applications/OBS.app/Contents/MacOS/OBS --remote-debugging-port=9222 --remote-allow-origins=*` (the flags are forwarded to CEF on all platforms; `--remote-allow-origins` fixes the "WebSocket disconnected" DevTools failure seen on OBS 31) ([OBS wiki](https://github.com/obsproject/obs-studio/wiki/Browser-Source-Development-and-Debugging), [forum](https://obsproject.com/forum/threads/browser-source-remote-debugger-not-working-in-obs-31.182612)). Then open `http://localhost:9222` in Chrome (or `chrome://inspect` → Configure → `localhost:9222`) and use Performance, Memory and the Rendering → Frame Rendering Stats overlay. Check `devicePixelRatio`, `WEBGL_debug_renderer_info` (Metal vs SwiftShader), and `AudioContext.state` here too.
- **Unit tests.** Vitest for the combo/move state machine with recorded `.jsonl` fixtures; no renderer needed.

---

## 8. Recommended architecture, packages, SDK asks, risks

### Folder layout (`src/themes/street-fighter/`)

```
index.tsx                 meta + default export (React shell only)
public/                   (future) atlases/fonts if SDK ships files; today unused
assets/
  atlas/                  *.aseprite sources, packed *.png + *.json (imported → base64)
  fonts/                  arcade.fnt + .png, or pixel .woff2 for BitmapFont.install
  manifest.ts             typed list of bundles → Pixi Assets manifest
  adapters.ts             aseprite json → Pixi spritesheet + FrameObject[] per tag
engine/
  renderer.ts             Renderer interface (init, resize, begin/end frame, destroy)
  pixiRenderer.ts         Pixi 8 implementation (backgroundAlpha 0, nearest, no GC)
  canvasRenderer.ts       Canvas2D fallback (imageSmoothingEnabled=false)
  loop.ts                 fixed-step accumulator, pause/resume, clock for tests
  input.ts                postMessage → typed events, ring buffer, replay hooks
  tween.ts                in-loop tweens + easings
  scale.ts                fitVirtualCanvas(), integer/fractional policy
  warmup.ts               draw-everything-once pass after load
  context.ts              webglcontextlost/restored handling
game/
  state.ts                decks, faders, combo meter, round state
  moves.ts                mixer deltas → moves (BASSLINE SWAP, FILTER SWEEP …)
  combos.ts               timing windows, multipliers, super meter
  beat.ts                 BPM bar clock
  director.ts             spawns scene objects for events (callouts, sparks, shake)
scene/
  hud.ts                  9-slice bars, timers, names
  callout.ts              kinetic text sprites
  numbers.ts              big combo digits
  sparks.ts               ParticleContainer emitter
  fighters.ts             (later) AnimatedSprite characters
ui/
  Shell.tsx               canvas mount, splash, debug HUD (DEV only)
  Splash.tsx              LOADING… INSERT COIN with progress
dev/
  replay.ts, stress.ts    window.__sf hooks, DEV only
```

### Packages to add

- `pixi.js@^8.22.0` (runtime)
- `@pixi/sound@^6.0.1` (runtime, optional, only if SFX ship)
- dev: `free-tex-packer-core@^0.3.9` (or rely on the Aseprite CLI), `@playwright/test` (latest), `vitest` (latest)
- Do **not** add `@pixi/react` (needs React 19) or `@pixi/particle-emitter` (peer `<8`). GSAP + PixiPlugin are already present if wanted.

### Pixi init to use

```ts
TextureSource.defaultOptions.scaleMode = 'nearest';
const app = new Application();
await app.init({
  width: 384, height: 216, resolution: 1, autoDensity: false,
  backgroundAlpha: 0, antialias: false, roundPixels: true,
  preference: 'webgl', powerPreference: 'low-power',
  gcActive: false,            // 8.15+ name; older: textureGCActive
  autoStart: false,           // our loop decides
});
canvas.style.imageRendering = 'pixelated';
```

### Asks for the SDK author

1. Ship static files from the ZIP: copy `src/themes/<id>/public/**` into `themes/<id>/public/**` and confirm the host serves them at those paths with long cache headers (section 4b, patch above).
2. Forward OBS visibility to the iframe (`np:visibility { visible, active }`) from the host's `obsSourceVisibleChanged`/`obsSourceActiveChanged` listeners, and document whether the iframe is same-origin (affects audio autoplay and `window.obsstudio` access).
3. Document the overlay page's CSP (if any) regarding `data:`, `blob:` and third-party origins, and whether `entry.js` is served compressed.
4. Optionally forward `np:mix` in `entry.tsx` as a prop-less event (it already streams; the theme can listen directly, so this is cosmetic).
5. No dependency allowlist exists in the build today (anything in `package.json` is bundled); ask whether the upload validator scans JS for anything (size only, presumably).

### Risks

- **Late texture uploads** are the biggest practical risk to "nothing pops late": handled by disabling GC and the warm-up pass; re-run warm-up after context restore.
- **Hardware acceleration off** on the user's OBS → software compositor readback + possible SwiftShader WebGL. Detect and warn; the Canvas2D fallback keeps it working.
- **Visibility unknown inside the iframe** → idle CPU in hidden scenes until the host forwards it; idle throttling mitigates.
- **Chromium 127 → 150 jump in OBS 33**: nothing we use is bleeding edge; re-test the transparent canvas and audio when OBS 33 lands.
- **React 18 StrictMode double effects in dev** → engine must be idempotent.
- **Dashboard preview is non-integer** → accept slight shimmer or letterbox; never let preview logic leak into the OBS path.
- **Base64 inlining growth**: watch `entry.js`; move to `public/` once the SDK supports it or the payload passes ~5 MB.
- **Beat clock drift** without beat-grid data → re-anchor on play/cue; keep idle animations tolerant (phase, not frame-exact).
- **Audio** is a nice-to-have with routing and taste problems; keep it off by default.
