#!/usr/bin/env python3
"""Slice a recording by gesture markers from midi_tap.html.

Usage: python3 tools/slice_markers.py recordings/np3-<date>.jsonl [--window 6]
For each marker: raw MIDI messages in the next N seconds (default 6) grouped by control, the
np:mix states NP3 emitted in the same window, and what detect_moves-style edges appeared. This is the
labelled ground truth to hand Triode for gesture recognisers.
"""
import sys, json, collections, datetime as dt
def ts(s): return dt.datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp()
args = [a for a in sys.argv[1:] if not a.startswith("--")]
win = float(sys.argv[sys.argv.index("--window") + 1]) if "--window" in sys.argv else 6.0
rows = [json.loads(l) for l in open(args[0]) if l.strip()]
raw = sorted((m for r in rows if (r.get("data") or {}).get("type") == "midi-batch" for m in r["data"]["msgs"]), key=lambda m: m["at"])
marks = [(ts(r["at"]), r["data"]["label"]) for r in rows if (r.get("data") or {}).get("type") == "marker"]
mix = [(ts(r["at"]), r) for r in rows if (r.get("data") or {}).get("type") == "np:mix"]
if not marks: sys.exit("no markers in this recording (use the label buttons on the tap page)")
DECK_CC = {19: "fader", 7: "eqHigh", 11: "eqMid", 15: "eqLow", 4: "trim", 34: "platter", 35: "platter(vinyl off)", 33: "ring", 31: "shift+jog", 41: "jog+beatjump", 0: "tempo"}
DECK_NOTE = {54: "touch", 11: "play", 12: "cue", 13: "stem drums", 14: "stem vocal", 15: "stem inst", 16: "loop in", 17: "loop out", 20: "4beat/exit", 88: "sync", 94: "beatjump<", 95: "beatjump>"}
def label(m):
    k, ch, d1 = m["kind"], m["ch"], m["d1"]
    if k == "cc" and 1 <= ch <= 4 and d1 in DECK_CC: return f"deck{ch} {DECK_CC[d1]}"
    if k == "cc" and 1 <= ch <= 4 and d1 - 32 in DECK_CC: return None  # LSB
    if k == "cc" and ch == 7: return {31: "crossfader", 23: "color1", 24: "color2", 25: "color3", 26: "color4"}.get(d1, None if d1 >= 32 else f"global cc{d1}")
    if k == "cc" and ch == 5: return {71: "fx on", 2: "fx level"}.get(d1, f"fx cc{d1}")
    if k == "note_on" and 1 <= ch <= 4 and m["d2"] > 0: return f"deck{ch} {DECK_NOTE.get(d1, f'note{d1}')}"
    if k == "note_on" and ch >= 8 and m["d2"] > 0:
        deck = {8: 1, 9: 1, 10: 2, 11: 2, 12: 3, 13: 3, 14: 4, 15: 4}[ch]; mode = ["hot cue", "pad fx1", "beat jump", "sampler", "keyboard", "pad fx2", "beat loop", "key shift"][d1 // 16]
        return f"deck{deck} pad {mode} #{d1 % 8 + 1}{' (shift)' if ch % 2 else ''}"
    return None
for i, (t, lab) in enumerate(marks):
    end = min(t + win, marks[i + 1][0]) if i + 1 < len(marks) else t + win
    seg = [m for m in raw if t <= ts(m["at"]) < end]
    c = collections.Counter(filter(None, (label(m) for m in seg)))
    plat = [m for m in seg if m["kind"] == "cc" and 1 <= m["ch"] <= 4 and m["d1"] in (34, 35)]
    ring = [m for m in seg if m["kind"] == "cc" and 1 <= m["ch"] <= 4 and m["d1"] == 33]
    faders = [m for m in seg if m["kind"] == "cc" and 1 <= m["ch"] <= 4 and m["d1"] == 19]
    xf = [m for m in seg if m["kind"] == "cc" and m["ch"] == 7 and m["d1"] == 31]
    def burst(ms, name, signed=False):
        if not ms: return
        tt = [ts(m["at"]) for m in ms]; dur = tt[-1] - tt[0]
        if signed:
            d = [m["d2"] - 64 for m in ms]; print(f"    {name}: {len(ms)} msgs over {dur*1000:.0f} ms, ticks sum {sum(d):+d}, peak |delta| {max(abs(x) for x in d)}, backward {sum(x < 0 for x in d)}/{len(d)}, rate {len(ms)/max(dur,0.001):.0f}/s")
        else:
            v = [m["d2"] for m in ms]; print(f"    {name}: {len(ms)} msgs over {dur*1000:.0f} ms, value {v[0]}→{v[-1]} (min {min(v)}, max {max(v)}), rate {len(ms)/max(dur,0.001):.0f}/s")
    states = [r for st, r in mix if t <= st < end]
    print(f"\n=== {lab}  @ {dt.datetime.fromtimestamp(t):%H:%M:%S}  ({end - t:.1f}s window) ===")
    print(f"  raw: {len(seg)} msgs | np:mix states: {len(states)}")
    for k, v in c.most_common(10): print(f"    {k:<28} {v}")
    for ch in (1, 2, 3, 4):
        burst([m for m in plat if m["ch"] == ch], f"deck{ch} platter", signed=True)
        burst([m for m in ring if m["ch"] == ch], f"deck{ch} ring", signed=True)
        burst([m for m in faders if m["ch"] == ch], f"deck{ch} fader MSB")
    burst(xf, "crossfader MSB")
    if states:
        a, b = states[0]["data"]["state"], states[-1]["data"]["state"]
        for ca, cb in zip(a["channels"], b["channels"]):
            d = {k: (round(ca["signals"][k], 2), round(cb["signals"][k], 2)) for k in ("channelFader", "eqLow", "eqMid", "eqHigh", "trim", "filter") if ca["signals"][k] != cb["signals"][k]}
            fl = {k: cb["signals"][k] for k in ("playing", "cueActive", "jogTouching") if ca["signals"][k] != cb["signals"][k]}
            if d or fl: print(f"    state ch{ca['channelNumber']} first→last: {d} {fl}")
