import { useEffect, useReducer, useRef } from "react";
import type { ThemeMeta, ThemeProps } from "../theme";
import {
  controllerValue,
  type MixProcessorState,
  type ThemeControllerSnapshot,
} from "../events";

/**
 * Pipeline Probe: a diagnostic theme for the controller -> NP3 -> overlay path.
 *
 * It renders what each feed delivers and measures how it arrives: update rate,
 * age at arrival, and how many discrete presses were folded into one snapshot
 * (a counter that jumps by 3 between snapshots means two presses were never seen
 * as their own update). Run the same gestures through each input path (USB MIDI
 * in the playground, the NP3 desktop feed, the real overlay URL) and compare.
 * "Download log" saves every received snapshot with its arrival time.
 */
export const meta: ThemeMeta = {
  id: "pipeline-probe",
  name: "Pipeline Probe",
  width: 960,
  height: 600,
  description:
    "Diagnostic: shows what the track, mix and controller feeds deliver, their rate, age and coalesced presses.",
  events: ["track", "mix", "controller"],
};

const COUNTERS = [
  ["playPressCount", "PLAY"],
  ["cuePressCount", "CUE"],
  ["loopInCount", "LOOP IN"],
  ["loopOutCount", "LOOP OUT"],
  ["loopHalfCount", "LOOP 1/2"],
  ["loopDoubleCount", "LOOP x2"],
  ["jogSequence", "JOG"],
] as const;

const TOGGLES = [
  ["playing", "playing"],
  ["cueActive", "cue"],
  ["syncActive", "sync"],
  ["loopActive", "loop"],
  ["keyLock", "key lock"],
  ["jogTouching", "jog touch"],
] as const;

const CONTINUOUS = [
  ["channelFader", "fader"],
  ["eqHigh", "hi"],
  ["eqMid", "mid"],
  ["eqLow", "low"],
  ["filter", "filter"],
  ["trim", "trim"],
  ["tempo", "tempo"],
] as const;

const RATE_WINDOW_MS = 5000;
const LOG_CAP = 20000;
const EVENT_LINES = 14;

interface FeedStats {
  count: number;
  lastAt: number;
  arrivals: number[];
  ageMs: number | null; // arrival time minus the feed's own timestamp
}

interface CounterStats {
  seen: number; // sum of positive deltas = presses that happened
  updates: number; // snapshots in which the counter moved
  coalesced: number; // presses that shared a snapshot with another press
}

interface ProbeState {
  feeds: Record<"track" | "mix" | "controller", FeedStats>;
  counters: Record<string, CounterStats>;
  prev: ThemeControllerSnapshot | null;
  events: string[];
  log: { at: number; feed: string; data: unknown }[];
  startedAt: number;
}

const emptyFeed = (): FeedStats => ({ count: 0, lastAt: 0, arrivals: [], ageMs: null });

function freshState(): ProbeState {
  return {
    feeds: { track: emptyFeed(), mix: emptyFeed(), controller: emptyFeed() },
    counters: {},
    prev: null,
    events: [],
    log: [],
    startedAt: Date.now(),
  };
}

function arrive(feed: FeedStats, now: number, sourceTs: number | null) {
  feed.count++;
  feed.lastAt = now;
  feed.arrivals.push(now);
  while ((feed.arrivals[0] ?? Infinity) < now - RATE_WINDOW_MS) feed.arrivals.shift();
  feed.ageMs = sourceTs ? now - sourceTs : null;
}

const rate = (f: FeedStats) => (f.arrivals.length / (RATE_WINDOW_MS / 1000)).toFixed(1);
const fmt = (v: unknown) =>
  typeof v === "number" ? v.toFixed(2) : typeof v === "boolean" ? (v ? "on" : "off") : "—";
const clock = (t: number) => new Date(t).toISOString().slice(11, 23);

function decksOf(c: ThemeControllerSnapshot | null | undefined, m: MixProcessorState | null | undefined) {
  const fromController =
    c?.availableControls.flatMap((p) => {
      const match = /^deck([1-6])\./.exec(p);
      return match ? [Number(match[1])] : [];
    }) ?? [];
  const fromMix = m?.channels.map((ch) => ch.channelNumber) ?? [];
  const all = [...new Set([...fromController, ...fromMix])].sort((a, b) => a - b);
  return all.length ? all : [1, 2, 3, 4];
}

/** Compare two controller snapshots; record counter jumps and state edges. */
function diffController(s: ProbeState, prev: ThemeControllerSnapshot | null, next: ThemeControllerSnapshot) {
  const now = Date.now();
  const lines: string[] = [];
  for (const deck of decksOf(next, null)) {
    for (const [key, label] of COUNTERS) {
      const path = `deck${deck}.${key}`;
      const a = controllerValue(prev, path);
      const b = controllerValue(next, path);
      if (typeof b !== "number") continue;
      const st = (s.counters[path] ??= { seen: 0, updates: 0, coalesced: 0 });
      if (typeof a !== "number") continue; // first observation: no delta yet
      const delta = b - a;
      if (delta < 0) lines.push(`${clock(now)}  D${deck} ${label} counter reset (${a} -> ${b})`);
      if (delta > 0) {
        st.seen += delta;
        st.updates++;
        if (delta > 1) st.coalesced += delta - 1;
        if (key !== "jogSequence" || delta > 1)
          lines.push(`${clock(now)}  D${deck} ${label} +${delta}${delta > 1 ? `  (${delta - 1} coalesced)` : ""}`);
      }
    }
    for (const [key, label] of TOGGLES) {
      const path = `deck${deck}.${key}`;
      const a = controllerValue(prev, path);
      const b = controllerValue(next, path);
      if (typeof b === "boolean" && typeof a === "boolean" && a !== b)
        lines.push(`${clock(now)}  D${deck} ${label} ${b ? "ON" : "off"}`);
    }
    const fa = controllerValue(prev, `deck${deck}.channelFader`);
    const fb = controllerValue(next, `deck${deck}.channelFader`);
    if (typeof fa === "number" && typeof fb === "number") {
      if (fa > 0.1 && fb <= 0.1) lines.push(`${clock(now)}  D${deck} fader closed`);
      if (fa < 0.8 && fb >= 0.8) lines.push(`${clock(now)}  D${deck} fader open${fa <= 0.1 ? "  (slam: closed->open in one update)" : ""}`);
    }
    for (const band of ["eqLow", "eqMid", "eqHigh"] as const) {
      const a = controllerValue(prev, `deck${deck}.${band}`);
      const b = controllerValue(next, `deck${deck}.${band}`);
      if (typeof a !== "number" || typeof b !== "number") continue;
      if (a > -0.8 && b <= -0.8) lines.push(`${clock(now)}  D${deck} ${band.slice(2).toUpperCase()} kill`);
      if (a <= -0.8 && b > -0.8) lines.push(`${clock(now)}  D${deck} ${band.slice(2).toUpperCase()} back`);
    }
  }
  if (lines.length) s.events = [...lines.reverse(), ...s.events].slice(0, EVENT_LINES);
}

export default function PipelineProbe({ track, mixState, controller, connected }: ThemeProps) {
  const ref = useRef<ProbeState>(freshState());
  const [, tick] = useReducer((n: number) => n + 1, 0);
  const s = ref.current;

  const record = (feed: string, data: unknown) => {
    if (s.log.length < LOG_CAP) s.log.push({ at: Date.now(), feed, data });
  };

  useEffect(() => {
    if (track === undefined) return;
    arrive(s.feeds.track, Date.now(), null);
    record("track", track);
    tick();
  }, [track]);

  useEffect(() => {
    if (!mixState) return;
    const ts = mixState.lastUpdateAt ? Date.parse(mixState.lastUpdateAt) : null;
    arrive(s.feeds.mix, Date.now(), Number.isFinite(ts) ? ts : null);
    record("mix", mixState);
    tick();
  }, [mixState]);

  useEffect(() => {
    if (!controller) return;
    arrive(s.feeds.controller, Date.now(), controller.timestamp || null);
    diffController(s, s.prev, controller);
    s.prev = controller;
    record("controller", controller);
    tick();
  }, [controller]);

  // Re-render twice a second so rates and "last seen" ages keep moving while idle.
  useEffect(() => {
    const id = window.setInterval(tick, 500);
    return () => window.clearInterval(id);
  }, []);

  const download = () => {
    const blob = new Blob(
      [JSON.stringify({ version: 1, probe: "pipeline-probe", startedAt: s.startedAt, frames: s.log }, null, 1)],
      { type: "application/json" },
    );
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = `pipeline-probe-${new Date(s.startedAt).toISOString().replace(/[:.]/g, "-")}.json`;
    a.click();
    URL.revokeObjectURL(a.href);
  };

  const now = Date.now();
  const decks = decksOf(controller, mixState);
  const totals = Object.values(s.counters).reduce(
    (t, c) => ({ seen: t.seen + c.seen, coalesced: t.coalesced + c.coalesced }),
    { seen: 0, coalesced: 0 },
  );

  const feedRow = (name: "track" | "mix" | "controller", detail: string) => {
    const f = s.feeds[name];
    const since = f.lastAt ? `${((now - f.lastAt) / 1000).toFixed(1)}s ago` : "never";
    return (
      <tr key={name} className="border-t border-zinc-800">
        <td className="py-1 pr-3 font-semibold text-zinc-200">{name}</td>
        <td className="pr-3 tabular-nums">{f.count}</td>
        <td className="pr-3 tabular-nums">{rate(f)}/s</td>
        <td className="pr-3 tabular-nums">{f.ageMs == null ? "—" : `${f.ageMs} ms`}</td>
        <td className="pr-3 tabular-nums">{since}</td>
        <td className="truncate text-zinc-400">{detail}</td>
      </tr>
    );
  };

  return (
    <div
      style={{ width: 960, maxWidth: "100%", fontFamily: "ui-monospace, Menlo, monospace" }}
      className="space-y-3 rounded-lg border border-zinc-800 bg-zinc-950 p-3 text-[11px] text-zinc-300"
    >
      <header className="flex items-center justify-between">
        <h1 className="text-sm font-semibold text-white">
          Pipeline Probe <span className="text-zinc-500">· {connected ? "connected" : "not connected"}</span>
        </h1>
        <div className="flex gap-2">
          <button className="rounded border border-zinc-700 px-2 py-0.5 hover:border-orange-400" onClick={download}>
            Download log ({s.log.length})
          </button>
          <button
            className="rounded border border-zinc-700 px-2 py-0.5 hover:border-orange-400"
            onClick={() => {
              ref.current = freshState();
              tick();
            }}
          >
            Reset
          </button>
        </div>
      </header>

      <table className="w-full text-left">
        <thead className="text-zinc-500">
          <tr>
            <th className="pr-3 font-normal">feed</th>
            <th className="pr-3 font-normal">updates</th>
            <th className="pr-3 font-normal">rate (5 s)</th>
            <th className="pr-3 font-normal">age at arrival</th>
            <th className="pr-3 font-normal">last seen</th>
            <th className="font-normal">detail</th>
          </tr>
        </thead>
        <tbody>
          {feedRow("track", track ? `${track.artist} — ${track.title}${track.bpm ? ` · ${track.bpm} BPM` : ""}` : "no track")}
          {feedRow("mix", mixState ? `source ${mixState.mixer.sourceId} · ${mixState.channels.length} channels` : "no mix state")}
          {feedRow(
            "controller",
            controller
              ? `source ${controller.sourceId} · ${controller.connected ? "connected" : "disconnected"} · ${controller.state?.controllerName ?? "unnamed"} · observed ${controller.observedControls.length}/${controller.availableControls.length} controls`
              : "no controller feed",
          )}
        </tbody>
      </table>

      <p className="text-zinc-400">
        Presses counted: <span className="text-white">{totals.seen}</span> · coalesced into a shared snapshot:{" "}
        <span className={totals.coalesced ? "text-orange-400" : "text-white"}>{totals.coalesced}</span>
        {totals.seen > 0 && ` (${Math.round((100 * totals.coalesced) / totals.seen)}%)`} · age is arrival time
        minus the feed's own timestamp, so it includes any clock difference between machines.
      </p>

      <div className="grid gap-2" style={{ gridTemplateColumns: `repeat(${Math.min(decks.length, 4)}, minmax(0, 1fr))` }}>
        {decks.slice(0, 4).map((deck) => {
          const cv = (k: string) => controllerValue(controller, `deck${deck}.${k}`);
          const ch = mixState?.channels.find((c) => c.channelNumber === deck);
          return (
            <section key={deck} className="rounded border border-zinc-800 p-2">
              <h2 className="mb-1 font-semibold text-zinc-200">Deck {deck}</h2>
              <table className="w-full">
                <thead className="text-zinc-500">
                  <tr>
                    <th className="text-left font-normal" />
                    <th className="text-right font-normal">ctrl</th>
                    <th className="text-right font-normal">mix</th>
                  </tr>
                </thead>
                <tbody className="tabular-nums">
                  {CONTINUOUS.map(([k, label]) => {
                    const sig = ch?.signals as unknown as Record<string, unknown> | undefined;
                    return (
                      <tr key={k}>
                        <td>{label}</td>
                        <td className="text-right text-white">{fmt(cv(k))}</td>
                        <td className="text-right">{fmt(sig?.[k])}</td>
                      </tr>
                    );
                  })}
                  {TOGGLES.map(([k, label]) => (
                    <tr key={k}>
                      <td>{label}</td>
                      <td className={`text-right ${cv(k) === true ? "text-orange-400" : "text-white"}`}>{fmt(cv(k))}</td>
                      <td className="text-right">
                        {fmt(k === "loopActive" ? ch?.signals.looping : (ch?.signals as unknown as Record<string, unknown> | undefined)?.[k])}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <div className="mt-1 border-t border-zinc-800 pt-1">
                {COUNTERS.map(([k, label]) => {
                  const v = cv(k);
                  const st = s.counters[`deck${deck}.${k}`];
                  return (
                    <div key={k} className="flex justify-between tabular-nums">
                      <span>{label}</span>
                      <span className="text-white">
                        {typeof v === "number" ? v : "—"}
                        {st?.coalesced ? <span className="text-orange-400"> ({st.coalesced} coalesced)</span> : null}
                      </span>
                    </div>
                  );
                })}
              </div>
            </section>
          );
        })}
      </div>

      <section>
        <h2 className="mb-1 font-semibold text-zinc-200">Controller events (derived from snapshot differences)</h2>
        <pre className="h-[150px] overflow-hidden whitespace-pre text-zinc-400">
          {s.events.length ? s.events.join("\n") : "Move a fader, press play or cue, touch a jog wheel…"}
        </pre>
      </section>
    </div>
  );
}
