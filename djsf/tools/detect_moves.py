#!/usr/bin/env python3
"""Prototype move detector for DJ Street Fighter.

Reads a Protocol Spy recording (JSON lines with {at, origin, data}) and turns the
np:mix state stream into (1) primitive signal EDGES and (2) named MOVES, to prove
what is detectable from today's NP3 payload. Musical time uses the on-air track's
BPM when present (default 124).

Usage: python3 detect_moves.py recordings/np3-2026-10-05_223636.jsonl
"""
import json, sys, datetime as dt
from collections import deque

EQ_CUT = -0.5          # NP3's own eqCutThreshold
FADER_OPEN = 0.5

def parse_at(s):
    return dt.datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp()

def load(path):
    rows = []
    for line in open(path):
        line = line.strip()
        if not line:
            continue
        j = json.loads(line)
        d = j.get("data") or {}
        if d.get("type") != "np:mix":
            continue
        st = d["state"]
        if st["mixer"]["sourceId"] != "midi":
            continue
        rows.append((parse_at(j["at"]), st))
    # dedupe (NP3 sends each state twice)
    out, last = [], None
    for t, st in rows:
        fp = json.dumps({k: v for k, v in st.items() if k != "lastUpdateAt"}, sort_keys=True)
        if fp == last:
            continue
        last = fp
        out.append((t, st))
    return out

def bpm_of(st):
    for ch in st["channels"]:
        if ch.get("track") and ch["signals"].get("playing") and ch["track"].get("bpm"):
            return ch["track"]["bpm"]
    return 124

def edges(states):
    """Primitive edges between consecutive deduped states."""
    ev = []
    prev = None
    for t, st in states:
        if prev is not None:
            for a, b in zip(prev["channels"], st["channels"]):
                ch = b["channelNumber"]
                sa, sb = a["signals"], b["signals"]
                # fader
                fa, fb = sa["channelFader"], sb["channelFader"]
                if fa != fb:
                    ev.append((t, ch, "fader", fa, fb))
                    if fa >= FADER_OPEN and fb < 0.08:
                        ev.append((t, ch, "fader_cut", fa, fb))
                    if fa < 0.08 and fb >= FADER_OPEN:
                        ev.append((t, ch, "fader_slam", fa, fb))
                for band in ("eqLow", "eqMid", "eqHigh"):
                    va, vb = sa[band], sb[band]
                    if va != vb:
                        ev.append((t, ch, band, va, vb))
                        if va > EQ_CUT and vb <= EQ_CUT:
                            ev.append((t, ch, band + "_cut", va, vb))
                        if va <= EQ_CUT and vb > EQ_CUT:
                            ev.append((t, ch, band + "_restore", va, vb))
                for flag in ("playing", "cueActive", "jogTouching", "looping"):
                    if sa[flag] != sb[flag]:
                        ev.append((t, ch, flag + ("_on" if sb[flag] else "_off"), sa[flag], sb[flag]))
                if sa.get("filter") != sb.get("filter"):
                    ev.append((t, ch, "filter", sa.get("filter"), sb.get("filter")))
            xa = prev["mixer"]["crossfader"]["position"]; xb = st["mixer"]["crossfader"]["position"]
            if xa != xb:
                ev.append((t, 0, "crossfader", xa, xb))
            oa = prev["onAir"]["currentOnAir"]["channelNumber"]; ob = st["onAir"]["currentOnAir"]["channelNumber"]
            if oa != ob:
                ev.append((t, ob, "on_air_change", oa, ob))
        prev = st
    return ev

def moves(ev, states):
    """Pattern rules over the edge stream. Windows in bars using the live BPM."""
    bpm = bpm_of(states[-1][1]) if states else 124
    beat = 60.0 / bpm
    bar = 4 * beat
    found = []
    recent = deque(maxlen=64)
    for e in ev:
        t, ch, name, a, b = e
        # BASSLINE SWAP: one channel's low cut and another's low restored within 1 bar
        if name in ("eqLow_cut", "eqLow_restore"):
            want = "eqLow_restore" if name == "eqLow_cut" else "eqLow_cut"
            for r in reversed(recent):
                if r[2] == want and r[1] != ch and t - r[0] <= bar:
                    found.append((t, "BASSLINE SWAP", f"ch{r[1]}→ch{ch}", f"{(t-r[0])*1000:.0f} ms"))
                    break
        # FULL KILL: all three bands cut on one channel within 1 bar
        if name == "eqHigh_cut" or name == "eqLow_cut" or name == "eqMid_cut":
            bands = {name}
            for r in reversed(recent):
                if r[1] == ch and r[2].endswith("_cut") and r[2].startswith("eq") and t - r[0] <= bar:
                    bands.add(r[2])
            if bands >= {"eqLow_cut", "eqMid_cut", "eqHigh_cut"}:
                found.append((t, "FULL KILL", f"ch{ch}", "3 bands"))
        # QUICK CUT: fader cut on one channel while another channel is open, within 2 s of its slam / or on-air change
        if name == "fader_cut":
            for r in reversed(recent):
                if r[2] == "fader_slam" and r[1] != ch and t - r[0] <= 2.0:
                    found.append((t, "QUICK CUT", f"ch{r[1]} in, ch{ch} out", f"{(t-r[0])*1000:.0f} ms"))
                    break
        # FADER SLAM: 0 → open in one or two updates (<= 250 ms)
        if name == "fader_slam":
            found.append((t, "FADER SLAM", f"ch{ch}", f"{a:.2f}→{b:.2f}"))
        # SWEEP IN: a band restored through >= 4 intermediate values over <= 4 bars (monotonic rise)
        if name in ("eqLow", "eqMid", "eqHigh") and b > a:
            steps = [r for r in recent if r[1] == ch and r[2] == name and t - r[0] <= 4 * bar]
            rising = [r for r in steps if r[4] > r[3]]
            if len(rising) >= 4 and all(rising[i][4] <= rising[i+1][3] + 1e-9 for i in range(len(rising)-1)) and b >= -0.05 and a < -0.05:
                found.append((t, "EQ SWEEP IN", f"ch{ch} {name}", f"{len(rising)+1} steps over {(t-rising[0][0]):.1f} s"))
        # SCRATCH / JOG: touch while playing
        if name == "jogTouching_on":
            found.append((t, "JOG TOUCH", f"ch{ch}", "needs rotation events to classify scratch/backspin"))
        # HIGH CUT + RESTORE within 1 bar = "DUCK"
        if name == "eqHigh_restore":
            for r in reversed(recent):
                if r[2] == "eqHigh_cut" and r[1] == ch and t - r[0] <= 2 * bar:
                    found.append((t, "HIGH DUCK", f"ch{ch}", f"{(t-r[0])*1000:.0f} ms"))
                    break
        recent.append(e)
    return found, bpm

def main():
    path = sys.argv[1]
    states = load(path)
    print(f"deduped midi states: {len(states)}")
    gaps = [b[0] - a[0] for a, b in zip(states, states[1:])]
    small = sorted(g for g in gaps if g < 1.0)
    if small:
        print(f"inter-update gaps < 1 s: n={len(small)} min={small[0]*1000:.0f} ms median={small[len(small)//2]*1000:.0f} ms")
    ev = edges(states)
    print(f"\nprimitive edges: {len(ev)}")
    t0 = states[0][0]
    for t, ch, name, a, b in ev:
        if name in ("fader", "eqLow", "eqMid", "eqHigh"):
            continue  # raw value changes are noisy; show the semantic ones
        print(f"  +{t - t0:7.2f}s  ch{ch:<2} {name:<16} {a} → {b}")
    found, bpm = moves(ev, states)
    print(f"\nMOVES (bpm {bpm}, bar {240/bpm:.2f} s):")
    for t, name, who, detail in found:
        print(f"  +{t - t0:7.2f}s  {name:<14} {who:<22} {detail}")

if __name__ == "__main__":
    main()
