#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Score a blind A/B test against chance.

  python score_blind.py --key blind/key.json.b64 --answers "A,a,a,b,..."   # one letter per pair, in pair order

Prints the per-pair result, the number correct, and the one-sided exact binomial p-value against chance (p = 0.5).
Run it only after the listener has answered; it decodes the key.
"""
import argparse
import base64
import json
import math
import pathlib
import sys


def p_value(correct, n):
    return sum(math.comb(n, k) for k in range(correct, n + 1)) / 2 ** n


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--key", required=True)
    ap.add_argument("--answers", required=True, help="the side the listener picked as the reference, per pair")
    a = ap.parse_args(argv)
    key = json.loads(base64.b64decode(pathlib.Path(a.key).read_text()))
    picks = [s.strip().upper() for s in a.answers.replace(" ", ",").split(",") if s.strip()]
    names = sorted(key)
    if len(picks) != len(names):
        raise SystemExit(f"{len(picks)} answers for {len(names)} pairs")
    correct = 0
    for name, pick in zip(names, picks):
        hit = pick == key[name]
        correct += hit
        print(f"{name}: picked {pick}, reference was {key[name]} -> {'correct' if hit else 'wrong'}")
    n = len(names)
    print(f"{correct}/{n} correct; chance {n / 2:g}; one-sided p = {p_value(correct, n):.4f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
