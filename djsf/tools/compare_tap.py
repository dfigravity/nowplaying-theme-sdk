#!/usr/bin/env python3
"""Compare raw MIDI (midi_tap.html batches) with NP3's np:mix stream from the same recorder file.

Usage: python3 tools/compare_tap.py recordings/np3-<date>.jsonl [standalone-tap.jsonl]
Prints raw message counts per control (FLX10 names), state-side change counts, how many raw
messages collapse into each emitted state, fader and platter detail, controls that never reach the
state, and latency from raw MIDI to NP3's lastUpdateAt and to overlay arrival.
"""
import sys, json, bisect, statistics, collections, datetime as dt

def ts(s): return dt.datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp()
rows = [json.loads(l) for l in open(sys.argv[1]) if l.strip()]
raw = [m for r in rows if (r.get("data") or {}).get("type") == "midi-batch" for m in r["data"]["msgs"]]
if len(sys.argv) > 2:
    raw += [json.loads(l) for l in open(sys.argv[2]) if l.strip()]
mix = [r for r in rows if (r.get("data") or {}).get("type") == "np:mix" and r["data"]["state"]["mixer"]["sourceId"] == "midi"]
seen, states = set(), []
for r in mix:
    s = dict(r["data"]["state"]); s.pop("lastUpdateAt", None); k = json.dumps(s, sort_keys=True)
    if k in seen: continue
    seen.add(k); states.append(r)
if not raw or not states:
    sys.exit(f"raw MIDI messages: {len(raw)}, midi states: {len(states)} — need both in the same session")
raw.sort(key=lambda m: m["at"])
print(f"raw MIDI messages: {len(raw)}   np:mix states: {len(mix)} ({len(states)} unique)")

DECK_CC = {19: "fader", 51: "fader_lsb", 7: "eqHigh", 39: "eqHigh_lsb", 11: "eqMid", 43: "eqMid_lsb", 15: "eqLow", 47: "eqLow_lsb",
           4: "trim", 36: "trim_lsb", 34: "jog_platter", 35: "jog_platter_vinyloff", 33: "jog_ring", 31: "shift_jog", 41: "jog_beatjump", 0: "tempo", 32: "tempo_lsb"}
DECK_NOTE = {54: "jog_touch", 11: "play", 12: "cue", 13: "stem_drums", 14: "stem_vocal", 15: "stem_inst", 16: "loop_in", 17: "loop_out", 20: "loop_4beat", 88: "sync", 84: "pfl"}
GLOBAL_CC = {31: "crossfader", 63: "crossfader_lsb", 23: "color1", 24: "color2", 25: "color3", 26: "color4", 8: "master", 12: "hp_mix", 13: "hp_level", 3: "sampler_vol"}
def label(m):
    k, ch, d1 = m["kind"], m["ch"], m["d1"]
    if k == "cc" and 1 <= ch <= 4: return (ch, DECK_CC.get(d1, f"cc{d1}"))
    if k == "cc" and ch == 7: return (7, GLOBAL_CC.get(d1, f"cc{d1}"))
    if k == "cc" and ch == 5: return (5, {71: "fx_on", 2: "fx_level", 34: "fx_level_lsb"}.get(d1, f"fx_cc{d1}"))
    if k == "note_on" and 1 <= ch <= 4: return (ch, DECK_NOTE.get(d1, f"note{d1}"))
    if k == "note_on" and ch >= 8: return (ch, f"pad_note{d1}")
    return (ch, f"{k}{d1}")
cnt = collections.Counter(label(m) for m in raw)
print("\nraw messages by control (top 25):")
for (c, n), k in sorted(cnt.items(), key=lambda x: -x[1])[:25]: print(f"   ch{c:<2} {n:<22} {k}")

sc = collections.Counter()
for a, b in zip(states, states[1:]):
    for ca, cb in zip(a["data"]["state"]["channels"], b["data"]["state"]["channels"]):
        for k in ("channelFader", "eqLow", "eqMid", "eqHigh", "trim", "filter", "playing", "cueActive", "jogTouching", "looping"):
            if ca["signals"][k] != cb["signals"][k]: sc[(ca["channelNumber"], k)] += 1
    if a["data"]["state"]["mixer"]["crossfader"]["position"] != b["data"]["state"]["mixer"]["crossfader"]["position"]: sc[(0, "crossfader")] += 1
print("\nstate-side changes per signal:")
for (c, k), v in sorted(sc.items(), key=lambda x: -x[1]): print(f"   ch{c:<2} {k:<14} {v}")

st_t = [ts(r["at"]) for r in states]
raw_cc_t = sorted(ts(m["at"]) for m in raw if m["kind"] == "cc")
per = [bisect.bisect_right(raw_cc_t, b) - bisect.bisect_right(raw_cc_t, a) for a, b in zip(st_t, st_t[1:])]
busy = [p for p in per if p > 0]
if busy: print(f"\nraw CC messages collapsed into one emitted state (active windows): median {statistics.median(busy):.0f}, max {max(busy)}")
for ch in (1, 2, 3, 4):
    msb = [(ts(m["at"]), m["d2"]) for m in raw if m["kind"] == "cc" and m["ch"] == ch and m["d1"] == 19]
    if msb:
        runs = collections.Counter(bisect.bisect_right(st_t, t) for t, _ in msb)
        print(f"ch{ch} fader: raw MSB msgs {len(msb)}, distinct values {len(set(v for _, v in msb))}, state changes {sc[(ch, 'channelFader')]}, max raw msgs between two states {max(runs.values())}")
    pl = [m for m in raw if m["kind"] == "cc" and m["ch"] == ch and m["d1"] in (34, 35)]
    if pl:
        vals = [m["d2"] - 64 for m in pl]; tt = [ts(m["at"]) for m in pl]
        gaps = [b - a for a, b in zip(tt, tt[1:]) if b - a < 0.2]
        print(f"ch{ch} platter: {len(pl)} msgs over {tt[-1] - tt[0]:.1f}s, delta {min(vals)}..{max(vals)}, backward ticks {sum(v < 0 for v in vals)}, median gap {statistics.median(gaps) * 1000:.1f} ms" if gaps else f"ch{ch} platter: {len(pl)} msgs")
never = sorted({n for (c, n) in cnt if any(x in n for x in ("pad_", "stem_", "loop_", "shift_jog", "color", "jog_platter", "jog_ring", "jog_beatjump", "fx_"))})
print("\nraw-only controls (never represented in np:mix):", never)

raw_t = sorted(ts(m["at"]) for m in raw)
lat_s, lat_a = [], []
for r in states:
    a = ts(r["at"]); lu = r["data"]["state"].get("lastUpdateAt"); i = bisect.bisect_right(raw_t, a) - 1
    if i >= 0:
        lat_a.append((a - raw_t[i]) * 1000)
        if lu: lat_s.append((ts(lu) - raw_t[i]) * 1000)
q = lambda L, p: sorted(L)[min(len(L) - 1, int(len(L) * p))]
if lat_s: print(f"\nraw MIDI → NP3 lastUpdateAt (ms): p10 {q(lat_s, .1):.0f}  median {q(lat_s, .5):.0f}  p90 {q(lat_s, .9):.0f}")
if lat_a: print(f"raw MIDI → overlay arrival (ms):   p10 {q(lat_a, .1):.0f}  median {q(lat_a, .5):.0f}  p90 {q(lat_a, .9):.0f}")
print("Clocks: tap page and recorder share the Mac clock; lastUpdateAt is NP3's (cloud) clock, so small skew is possible.")
