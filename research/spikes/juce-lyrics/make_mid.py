import sys, mido
mf = mido.MidiFile(ticks_per_beat=480); tr = mido.MidiTrack(); mf.tracks.append(tr)
tr.append(mido.MetaMessage("set_tempo", tempo=mido.bpm2tempo(120), time=0))
for n, l in [(60, "Hel-"), (62, "lo"), (64, "world")]:
    tr.append(mido.MetaMessage("lyrics", text=l, time=0)); tr.append(mido.Message("note_on", note=n, velocity=90, time=0)); tr.append(mido.Message("note_off", note=n, velocity=0, time=480))
mf.save(sys.argv[1])
