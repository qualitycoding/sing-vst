#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Build blind A/B pairs from a reference directory and a candidate directory of WAV files.

Files are matched by stem (reference/c4.wav <-> candidate/c4.wav). Each pair is cut to one window, scaled to a common
RMS, faded, and written as pair-NN-A.wav / pair-NN-B.wav. Which side holds the reference is drawn from a seeded RNG.
The answer key is written base64-encoded and must stay undecoded until the listener has answered.

  python make_blind_pairs.py --ref ref/ --cand cand/ --out blind/ --seed 1 --pairs 12 [--window start|middle]
"""
import argparse
import base64
import json
import pathlib
import random
import sys

import numpy as np
import soundfile as sf


def mono(x):
    x = np.asarray(x, dtype=float)
    return x.mean(axis=1) if x.ndim > 1 else x


def resample(x, fs_from, fs_to):
    if fs_from == fs_to:
        return x
    from math import gcd
    from scipy.signal import resample_poly
    g = gcd(int(fs_from), int(fs_to))
    return resample_poly(x, int(fs_to) // g, int(fs_from) // g)


def cut(x, fs, seconds, window):
    """window=start: first `seconds` from the first sample above -40 dB of the peak (keeps the onset).
    window=middle: `seconds` centred in the file."""
    n = int(seconds * fs)
    if window == "start":
        above = np.flatnonzero(np.abs(x) > 0.01 * np.max(np.abs(x)))
        i0 = int(above[0]) if above.size else 0
    else:
        i0 = max(0, (len(x) - n) // 2)
    seg = x[i0:i0 + n]
    return np.pad(seg, (0, n - len(seg)))


def prepare(x, fs, args):
    seg = cut(resample(mono(x), fs, args.fs), args.fs, args.seconds, args.window)
    seg = seg - np.mean(seg)
    rms = np.sqrt(np.mean(seg ** 2))
    seg = seg * (10 ** (args.rms_db / 20) / max(rms, 1e-12))
    n = int(args.fade * args.fs)
    if args.window == "middle" and n:
        ramp = 0.5 - 0.5 * np.cos(np.pi * np.arange(n) / n)
        seg[:n] *= ramp
    if n:
        seg[-n:] *= (0.5 - 0.5 * np.cos(np.pi * np.arange(n) / n))[::-1]
    if np.max(np.abs(seg)) >= 1.0:
        raise SystemExit("clip would exceed full scale at the requested RMS; lower --rms-db")
    return seg


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--ref", required=True)
    ap.add_argument("--cand", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--seed", type=int, required=True, help="use a new seed after every round whose key the listener has seen")
    ap.add_argument("--pairs", type=int, default=12)
    ap.add_argument("--seconds", type=float, default=1.0)
    ap.add_argument("--window", choices=["start", "middle"], default="start",
                    help="start keeps the onset (the usual giveaway); middle tests the sustained part")
    ap.add_argument("--rms-db", type=float, default=-23.0)
    ap.add_argument("--fade", type=float, default=0.010)
    ap.add_argument("--fs", type=int, default=44100)
    a = ap.parse_args(argv)
    ref, cand = pathlib.Path(a.ref), pathlib.Path(a.cand)
    stems = sorted({p.stem for p in ref.glob("*.wav")} & {p.stem for p in cand.glob("*.wav")})
    if len(stems) < a.pairs:
        raise SystemExit(f"{len(stems)} matching stems, {a.pairs} pairs requested")
    rng = random.Random(a.seed)
    out = pathlib.Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    key, manifest = {}, {}
    for i, stem in enumerate(rng.sample(stems, a.pairs), 1):
        ref_is_a = rng.random() < 0.5
        r = prepare(*sf.read(ref / f"{stem}.wav"), a)
        c = prepare(*sf.read(cand / f"{stem}.wav"), a)
        name = f"pair-{i:02d}"
        first, second = (r, c) if ref_is_a else (c, r)
        sf.write(out / f"{name}-A.wav", first, a.fs, subtype="PCM_24")
        sf.write(out / f"{name}-B.wav", second, a.fs, subtype="PCM_24")
        key[name] = "A" if ref_is_a else "B"
        manifest[name] = stem
    (out / "key.json.b64").write_text(base64.b64encode(json.dumps(key, sort_keys=True).encode()).decode() + "\n")
    # the stem of each pair names the source note; keep it out of the listener's view until scoring
    (out / "sources.json.b64").write_text(base64.b64encode(json.dumps(manifest, sort_keys=True).encode()).decode() + "\n")
    print(f"{a.pairs} pairs written to {out} (seed {a.seed}, window {a.window})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
