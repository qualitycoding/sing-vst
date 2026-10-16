"""Planning check (D-038, T-069): the SMF bytes T-069 builds parse as intended with mido 1.3.3.
Run: ../venv-lock/bin/python -I research/spikes/premortem-r1/limits_fixture_check.py"""
import io
import mido


def varlen(v):
    out = [v & 0x7F]
    v >>= 7
    while v:
        out.insert(0, 0x80 | (v & 0x7F))
        v >>= 7
    return bytes(out)


def smf(body):
    body += b"\x00\xFF\x2F\x00"
    return b"MThd\0\0\0\x06\0\0\0\x01\x01\xE0" + b"MTrk" + len(body).to_bytes(4, "big") + body


def many(n):
    return smf(b"".join(varlen(0) + b"\x90\x3C\x40" + varlen(48) + b"\x80\x3C\x00" for _ in range(n)))


def late(end_beat):
    return smf(varlen((end_beat - 1) * 480) + b"\x90\x3E\x40" + varlen(480) + b"\x80\x3E\x00")


def summary(data):
    f = mido.MidiFile(file=io.BytesIO(data))
    t, ons, last_off = 0, 0, 0
    for m in f.tracks[0]:
        t += m.time
        if m.type == "note_on" and m.velocity > 0:
            ons += 1
        if m.type == "note_off":
            last_off = t
    return ons, last_off / 480, last_off / 480 * 60 / 120


for name, d in [("many(5000)", many(5000)), ("many(5001)", many(5001)), ("late(1799)", late(1799)), ("late(1801)", late(1801))]:
    n, end_beats, end_s = summary(d)
    print(f"{name}: notes {n}, last end {end_beats:g} beats = {end_s:g} s at 120 bpm")
