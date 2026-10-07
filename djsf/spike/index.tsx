import { useEffect, useRef } from "react";
import { Application, Sprite, Texture, Rectangle, TextureSource, BitmapText, Container } from "pixi.js";
import type { ThemeMeta, ThemeProps } from "../../theme";
import sheetUrl from "./sheet.png";

export const meta: ThemeMeta = {
  id: "street-fighter",
  name: "Street Fighter (spike)",
  description: "Renderer spike: Pixi 8, 384x216 virtual canvas scaled 5x, inlined sprite sheet.",
  width: 1920,
  height: 1080,
};

const VW = 384, VH = 216;

export default function StreetFighter({ track }: ThemeProps) {
  const host = useRef<HTMLDivElement>(null);
  const label = useRef<BitmapText | null>(null);

  useEffect(() => {
    let alive = true;
    let app: Application | null = null;
    (async () => {
      TextureSource.defaultOptions.scaleMode = "nearest";
      const a = new Application();
      await a.init({ width: VW, height: VH, resolution: 1, autoDensity: false, backgroundAlpha: 0,
        antialias: false, roundPixels: true, preference: "webgl", powerPreference: "low-power" });
      if (!alive || !host.current) { a.destroy(true); return; }
      app = a;
      const k = Math.max(1, Math.floor(Math.min(window.innerWidth / VW, window.innerHeight / VH)));
      a.canvas.style.width = `${VW * k}px`; a.canvas.style.height = `${VH * k}px`;
      a.canvas.style.imageRendering = "pixelated";
      host.current.appendChild(a.canvas);
      const img = new Image(); img.src = sheetUrl; await img.decode();
      const base = new TextureSource({ resource: img, scaleMode: "nearest" });
      const frames = [0, 1].map(i => new Texture({ source: base, frame: new Rectangle(i * 32, 0, 32, 32) }));
      const stage = new Container(); a.stage.addChild(stage);
      const rec = new Sprite(frames[0]!); rec.position.set(20, 60); stage.addChild(rec);
      const t = new BitmapText({ text: "INSERT COIN", style: { fontFamily: "monospace", fontSize: 8, fill: 0xfee761 } });
      t.position.set(124, 206); stage.addChild(t); label.current = t;
      let f = 0; a.ticker.add(() => { f++; if (f % 30 === 0) rec.texture = frames[(f / 30) % 2]!; rec.x = 20 + Math.round(8 * Math.sin(f / 20)); });
    })();
    return () => { alive = false; app?.destroy(true, { children: true }); };
  }, []);

  useEffect(() => { if (label.current && track) label.current.text = `${track.artist} - ${track.title}`.toUpperCase().slice(0, 17); }, [track]);

  return <div ref={host} style={{ width: "100vw", height: "100vh", background: "transparent" }} />;
}
