# Decisions, interfaces and decision rules

Every rule here is the specification the frozen tests enforce. `C-###` = claim in research/claims.json; `T-###` / `T-P##` = test;
`S-###` = plan step; `G-###` = human gate; `A-###` = assumption; `PK-##` = prevention rule in research/PRIOR_KNOWLEDGE.md.
Numbers that describe quality or speed are **unmeasured defaults** until a measurement step records them (PK-29).

---

## Architecture and platform

### D-001 Plugin framework
JUCE 9.0.3 (C-012), CMake ≥ 3.22, `project(... LANGUAGES C CXX)`, C++20, brace initialisation (PK-37). Formats: VST3 and
Standalone. Platforms: Windows x64 (MSVC, `windows-2022` runner) and Linux x64 (GCC 13, `ubuntu-24.04`) (A-008). macOS/AU are
out of scope. `COPY_PLUGIN_AFTER_BUILD FALSE`, `JUCE_VST3_CAN_REPLACE_VST2=0`, `JUCE_WEB_BROWSER=0`, `JUCE_USE_CURL=0` (PK-47).
`plugin/PluginProcessor.h` carries `static_assert (JUCE_MAJOR_VERSION == 9)`. The core library (`singvst_core`), the CLI and
the core tests do **not** use JUCE (JUCE modules compile into every target that links them, so sharing them between the core
and the plugin would duplicate symbols): JSON uses nlohmann/json 3.12.0 (MIT, C-049), SHA-256 and the MIDI-file reader (D-031)
are implemented in the core. Only the plugin and its tests link JUCE. Linux build packages are JUCE's documented list
(`docs/Linux Dependencies.md` at 9.0.3; C-050), including `libxi-dev`.

### D-002 Inference runtime
ONNX Runtime 1.31.0 CPU prebuilt packages from GitHub Releases (C-014), SHA-256 checked at configure time:
`onnxruntime-linux-x64-1.31.0.tgz` `cc5c72baf5ae5c8238a6841f0897227be2d02826b9cf98eaf02fdefaeeb03a57`,
`onnxruntime-win-x64-1.31.0.zip` `3958d8a44984160692c1b4ffd0de3cb48f8c39f9d34bb31e433db06e30b82195`.
Only the headers are used at compile time; nothing links `onnxruntime` (D-024). One process-wide `Ort::Env`; every session uses
`ORT_ENABLE_ALL`, inter-op threads 1, intra-op threads `min(4, max(1, hardware_concurrency / 2))`.

### D-003 Interfaces and stubs
The public interfaces are the headers `core/include/singvst/*.hpp`, `plugin/PluginProcessor.h` and the Python signatures in
`python/singvst_train/*.py`. Until a step implements them, C++ stubs (`core/src/stubs.cpp`, `plugin/PluginProcessor.cpp`)
throw `singvst::NotImplemented` (a `std::logic_error`, so no test that expects `ValidationError`, `ParseError` or
`Cancelled` can pass against a stub — PK-25) and Python stubs raise `NotImplementedError`. Interfaces freeze with the tests
(Phase 2E). The implementer adds private helpers freely but never changes a frozen signature or documented behaviour.

### D-020 Architecture: guide singer + voice converter
Pitch and lyrics are first sung by a **guide** (DiffSinger acoustic model + vocoder, ONNX; C-006, C-009) and the guide audio is
then **converted** to the target voice by an RVC v2 model trained on the owner's recordings (C-001, C-003). Rejected:
so-vits-svc (AGPL-3.0, archived; C-002); fine-tuning DiffSinger on the owner's data (needs phoneme-labelled singing — a later
option, out of scope); reusing RVCRealtimeVST (Windows-only Python worker; C-024). The guide voicebank is TIGER v102 (C-036)
subject to gate G-005; a different DiffSinger voicebank with the same input conventions can be packed instead (D-008).

---

## Lyrics, pronunciation and alignment

### D-004 Lyric grammar (`parseLyrics`)
Input is UTF-8; positions are 0-based **byte** offsets. Whitespace is space, tab, CR, LF. The scanner repeats:
1. Skip whitespace.
2. `]` here → `ParseError` at its offset.
3. `[` starts a phoneme group that ends at the next `]`. A `[` inside the group → `ParseError` at that inner `[`. No `]`
   before the end → `ParseError` at the opening `[`. The content is split on whitespace and each phone lower-cased (ASCII).
   If the byte after `]` is `-`, it is consumed and the token's `continuesWord` is true. An empty group (`[]`, `[ ]`) yields
   no token. Otherwise one `Phonemes` token.
4. `+` yields one `Extend` token.
5. Otherwise a *word* runs up to the next whitespace, `[`, `]`, `+` or end. It is split on `-`. Each part is cleaned: ASCII
   letters and digits are kept lower-cased, `'` is kept, every byte ≥ 0x80 is kept unchanged, everything else is dropped.
   Empty parts are dropped. Each remaining part is one `Text` token; all but the last have `continuesWord = true`; the last
   has it only if the word ends with `-` (so `Hel- lo` continues across whitespace).
Tests: T-001…T-006.

### D-005 Pronunciation dictionary and syllables
`Dictionary::fromCmuText`: for each line, drop text from the first `#`, trim; skip empty lines and lines starting with `;;;`.
The first field is the word; a word ending in `(<digits>)` is a variant and is skipped. Words are lower-cased (ASCII); the
first entry of a word wins. Phones are normalised: trailing digits removed, lower-cased. `size()` counts distinct words;
`hasPhone(p)` normalises `p` the same way. The plugin and CLI embed CMUdict at commit 74790861 (C-016,
`third_party/cmudict/cmudict.dict`, SHA-256 `81917843c7f44ce2b094ac63873c2c7a4cf802040792c455ba3ca406891c3d22`, BSD-style
licence kept beside it). The plugin and the CLI load `cmudict.dict` from the folder of their own binary, where the build copies it
next to the ONNX Runtime library (D-024); the CLI's `--dict` overrides. Vowels: `aa ae ah ao aw ay eh er ey ih iy ow oy uh uw` (normalised).
`syllabify(phones, n)`: let `V` be the vowel indices. No vowel: `n == 1` → `[phones]`, else `ValidationError`. `n == 0` or
`n > |V|` → `ValidationError`. Otherwise cut between consecutive vowels `V[j-1]`, `V[j]` for `j = 1..n-1` after
`V[j-1] + 1 + floor(c/2)` phones, where `c` is the number of consonants between them (coda gets `floor(c/2)`, onset
`ceil(c/2)`); everything after the cut for `j = n-1` (including further vowels) is the last syllable. Tests: T-007…T-012.

### D-006 Monophony and alignment
`toMonophonic`: (1) discard notes with `endBeat - startBeat <= 1e-9`; (2) stable-sort by `startBeat`; (3) group
consecutive notes whose start is within `1e-9` beats of the group's first start — they are simultaneous — and keep the
highest pitch of each group (ties: the first in input order), unchanged; (4) walk the kept notes in order: if the previous
note ends after this note's start, its end becomes this note's start; (5) discard notes of length `<= 1e-9`.

`align(notes, tokens, dict)` builds **units** from tokens, in order:
- A `Text` group = a `Text` token plus the following `Text` tokens while the previous one has `continuesWord`. Its word is
  the concatenation of the group's texts and `g` is the group size. Unknown word → warning `unknown word '<word>'` and `g`
  units `["ah"]`. Otherwise `k` = vowel count of the pronunciation, `m = 1` if `k == 0` else `min(g, k)`, units =
  `syllabify(pron, m)`; if `g > m`, warning `word '<word>' has <g> syllables marked but <max(k,1)> vowel(s)` and `g - m`
  extension units.
- A `Phonemes` token: phones present in the dictionary (`hasPhone`) or equal to `sp`/`ap` are kept (`sp` → `SP`, `ap` →
  `AP`); others → warning `unknown phonemes <space-separated list>`; one unit of the kept phones, or `["ah"]` if none.
- An `Extend` token: one extension unit.
Each note `j` takes unit `j`; notes beyond the units are *surplus*. A syllable unit assigns its phones. An extension or
surplus note with no earlier assignment gets `["ah"]`, `isExtension = true` (and, for an `Extend` unit, the warning
`melisma '+' with no preceding syllable`); otherwise it gets `[v]`, `isExtension = true`, where `v` is the last vowel of the
previous assignment's phones, or its last phone if it has no vowel. Then warnings `<n> note(s) have no lyric` when there are
surplus notes and `<n> syllable(s) have no note` when units exceed notes. Warnings appear in the order produced. `align`
never throws for content. Tests: T-013…T-018.

---

## Timing, pitch and gain

### D-007 Phoneme layout, pitch curve, frames
Beats → seconds: `sec(b) = (b - first note's startBeat) * 60 / bpm`.
`layoutPhonemes(notes, bpm, c = 0.06)` requires notes sorted, non-overlapping (start ≥ previous end − 1e-9 beats), of positive
length, each with ≥ 1 phone; otherwise `ValidationError`. Segments: each note is a note segment `[s, e)`; a gap of more than
`1e-12` s before a note is a gap segment. For a note segment with phones `ph` and first vowel at `fv`:
- onset = `ph[:fv]`, coda = `ph[fv+1:]` (everything after the first vowel, including later vowels);
- coda: total `min(len(coda)·c, 0.4·dur)`, split equally, at the segment's tail;
- onset: for the first segment, total `min(len·c, 0.4·dur)` at its own head; otherwise total `min(len·c, 0.4·prevdur)`
  appended to the **previous** segment's tail (a gap or a note), after its own coda;
- a segment with no vowel keeps its tail and shares the rest equally among its phones;
- if a note segment's head + tail exceed `0.8·dur`, both are scaled by `0.8·dur / (head + tail)`.
Each segment emits head spans, then the nucleus (`SP` for a gap, the first vowel for a note; or the equal split), then tail
spans; the last span of a segment ends exactly at the segment end. Spans are contiguous from 0 to the last note's end.

`midiToHz(m) = 440 · 2^((m − 69)/12)` (A4 = MIDI 69 = 440 Hz; PK-32, PK-36).
`f0Curve(notes, bpm, fr, total, port, vib, vhz)` has `ceil(total·fr − 1e-9)` frames at times `i/fr`, 0 = unvoiced. Frame
`i` belongs to note `[s, e)` when `s ≤ i/fr < e` (tolerance 1e-12 s). A note is *legato* when its start equals the previous
note's end within 1e-9 beats; then over its first `pw = min(port, e − s)` seconds the pitch moves from the previous note's
frequency along `exp(ln fp + (ln f − ln fp)(1 − cos(π u))/2)`, `u = (t − s)/pw`. Vibrato multiplies by
`2^(vib · sin(2π·vhz·(t − s)) / 1200)` (phase 0 at the note start, also during portamento).

`rvcCoarsePitch(h)`: `m = 1127 ln(1 + h/700)`; if `m > 0`: `m = (m − m50)·254/(m1100 − m50) + 1`; clamp to [1, 255];
round half to even (numpy `rint`; C-021).

`spansToFrameDurations(spans, fr)`: `N` spans, `total = floor(lastEnd·fr + 0.5)`; `N == 0` or `total < N` →
`ValidationError`. Boundaries `B[-1] = 0`, `B[k] = min(max(floor(end_k·fr + 0.5), B[k−1] + 1), total − (N − 1 − k))`,
`B[N−1] = total`; durations `B[k] − B[k−1]` (each ≥ 1, sum exactly `total`).

The oracle `research/spikes/oracle/oracle.py` implements D-004…D-007, D-009, D-012 (noise) and passes the invariant checks in
`properties.py` (lesson L-20261014T203000Z). Tests: T-019…T-026.

### D-021 Gain staging
Renders are kept **unclipped** in `RenderedTake::samples` and `unclippedPeak` records their peak (PK-30). The only clipping
is at the output: `softClip(x, c = 0.98)`: non-finite → 0; `|x| ≤ 0.8c` → `x`; else
`sign(x)·(0.8c + 0.2c·tanh((|x| − 0.8c)/(0.2c)))` — odd, monotonic, never exceeds `c` (it equals `c` only where `tanh`
rounds to 1 in floating point). The `gain` parameter
(−36…+12 dB) is applied before the soft clip. The CLI applies the same output stage unless `--raw`. Tests: T-027, T-033.

---

## Voice package

### D-008 Voice package format v1
A directory with `manifest.json` and the files it references (never committed to any repository — A-011, D-026):
```
{ "format": "singvoice", "format_version": 1, "name": "<non-empty>", "consent": "<non-empty>", "guide_licence": "<non-empty>",
  "guide": { "type": "diffsinger", "sample_rate": 44100, "hop_size": 512, "language": "en", "steps": 20, "depth": 0.4,
             "files": { "acoustic": "...", "vocoder": "...", "phonemes": "...", ["speaker": "..."], ["languages": "..."] } },
  "converter": null | { "type": "rvc-v2", "sample_rate": 48000 | 32000, "speaker_id": 0, "files": { "synth": "...", "content": "..." } },
  "sha256": { "<relative path>": "<64 lower-case hex>", ... } }
```
Rules (each violation → `ValidationError` naming the field): valid JSON object; exact `format`/`format_version`; non-empty
strings; `guide.type == "diffsinger"`, `sample_rate == 44100`, `hop_size == 512`, `steps` integer 1…1000, `depth` number in
(0, 1], `language` non-empty (default `en` when absent); required file roles present, no unknown role; `converter` absent,
null, or `type == "rvc-v2"`, `sample_rate` ∈ {48000, 32000} (C-005), `speaker_id` integer ≥ 0 (default 0), roles `synth`
and `content` only; every file path is *safe* — non-empty `/`-separated segments of `[A-Za-z0-9._-]`, no segment `.` or
`..`, no leading `/`, no `\`, no `:` — and the set of `sha256` keys equals the set of referenced paths, each value 64
lower-case hex digits. Unknown top-level keys are ignored. `validatePackage` then checks each referenced file is a regular
file under the directory, at most `maxFileBytes`, with a matching SHA-256 (D-001: `juce::SHA256`). Speaker embedding file:
raw little-endian float32. Phonemes file: `.json` = object phone → integer id; otherwise text, id = 0-based line index
(lines split on `\n`, a trailing `\r` removed, a final empty line ignored) (C-033). `pack_voice` (Python) writes this format;
T-P13 checks the C++ parser accepts what it writes. Tests: T-028…T-031, T-P13, T-P14.

---

## Inference

### D-011 Resampler
`resample(x, from, to)`: identity (same vector) when rates match; output length `round(len·to/from)` (half away from 0).
Kaiser-windowed sinc, β = 8.6, cutoff `fc = 0.95·min(from, to)/2`, half-width 32 zero crossings of the `fc` sinc; `y[m] =
Σ x[n]·h(m·from/to − n)` with `h` normalised to unit DC gain; samples outside the input are 0. Tests (T-040): length rule,
identity, 1 kHz sine 48 k→16 k peak within 1 % in the interior, DC gain within 1e-3 in the interior, a 20 kHz tone at
44.1 k→16 k attenuated below −40 dB.

### D-012 ONNX contracts
**Guide (`GuideEngine`).** Inputs are discovered from the acoustic model at load. Required: `tokens` int64[1,n],
`durations` int64[1,n], `f0` float[1,T]. Supported optional inputs: `gender` float[1,T] (= 0), `velocity` float[1,T]
(= 1), `spk_embed` float[1,T,E] (the speaker file repeated per frame; E must equal the file's value count and a static model
dimension if one is declared, else `ValidationError`; required when the model has this input), `languages` int64[1,n],
`steps` int64, `depth` (float or int64), `speedup` int64. Any other input name (e.g. `energy`, `breathiness`, `voicing`,
`tension`) → `ValidationError` at load. Scalars are fed at the rank the model declares (0 or 1; C-041).
Step/depth inputs (C-034): with `steps`: steps = `guide.steps`, `depth` (float) = `guide.depth`. With `speedup` (legacy):
if the model has `depth`: `d = llround(depth·1000)`, `speedup = max(1, d / steps)`, `d = d / speedup · speedup` (integer
division), feed `depth` int64 = d; without `depth`: `speedup` = the largest divisor of 1000 that is ≤ `1000 / steps`.
Tokens: span phoneme `p` → id of `p`, else of `<language>/<p>`, else `ValidationError("unknown phoneme '<p>'")`; `languages`
= the languages-map id of `guide.language` for tokens found through the prefix, 0 otherwise (C-035).
Rendering (`render(spans, f0)`): `durations = spansToFrameDurations(spans, 44100/512)`; `f0.size()` must equal their sum,
else `ValidationError`. Unvoiced frames (0) take the value of the nearest voiced frame over the whole take (ties → the
earlier frame); no voiced frame at all → `ValidationError`. The take is split into **phrases** at `SP` spans of ≥ 22 frames
(≈ 0.25 s): those frames are output as exact zeros; every other maximal run of spans is a phrase rendered on its own with 8
`SP` frames before and after (C-038; padded f0 = the phrase's first/last value; per-frame inputs cover the padded length).
Acoustic output `mel` float[1,T+16,128] goes to the vocoder with the padded f0 (inputs `mel`, `f0`; output `waveform`
float[1,(T+16)·512]); 8·512 samples are trimmed from each end. Output length is exactly `sum(durations)·512`. `cancel` is
checked before every model run → `Cancelled`. The acoustic model draws its own noise (C-040): the guide is not reproducible.

**Converter (`ConverterEngine`).** `content` model: input `source` float[1,N] at 16 kHz → output `units` float[1,Tc,768]
(RVC v2: hubert final layer, 320-sample hop; C-020). `synth` model: inputs `phone` float[1,T,768], `phone_lengths`
int64[1] (= T), `pitch` int64[1,T], `pitchf` float[1,T], `ds` int64[1] (= `speaker_id`), `rnd` float[1,192,T]; output
`audio` float[1,1,T·hop] with `hop = sample_rate/100` (C-048: 480 at 48 kHz). Conversion of a take: resample the guide to
16 kHz; `T = min(len(f0), floor(N16/160))`; `pitch[t] = rvcCoarsePitch(f0[t])`, `pitchf[t] = f0[t]`; prior noise
`rnd[c][t] = standardNormal(seed, 192·T)[c·T + t]` for the **whole take** (C-003; the exporter scales it by 0.66666 inside
the graph). The take is processed in **chunks**: core frame ranges `[1500k, min(1500(k+1), T))`, each with up to 100 frames of context
on each side (clipped to `[0, T)`): the chunk's 16 kHz slice goes through `content`, each unit is repeated twice (50 → 100 fps), the result is cut or
extended (repeating the last unit) to the chunk's frame count, `synth` runs on the chunk's frames with the matching slices of
`pitch`, `pitchf` and `rnd`, and only the core frames' samples are kept. Output length is `T·hop`. Deterministic for a seed on
one platform. `standardNormal(seed, n)`: SplitMix64 from `seed`; per pair `u1 = ((x1>>11)+1)·2^-53`, `u2 = (x2>>11)·2^-53`,
`z0 = √(−2 ln u1) cos 2πu2`, `z1 = √(−2 ln u1) sin 2πu2`; order z0, z1, …; double precision, stored as float.
Golden values (oracle): seed 0 → −0.452757740, 0.207766039, 2.650605812, −0.490422825, −0.988604125; seed 42 → 0.414719750,
0.652681222, −0.891886214, 1.326833563, 1.729593088. Tests: T-039, T-042…T-047, T-P19.

### D-024 Runtime loading
ONNX Runtime is loaded by **explicit absolute path**, never by search order (C-026, C-042): `dlopen(path, RTLD_NOW |
RTLD_LOCAL)` on Linux, `LoadLibraryExW(path, nullptr, LOAD_WITH_ALTERED_SEARCH_PATH)` on Windows; `OrtGetApiBase` resolved by
name; `GetApi(ORT_API_VERSION)` must be non-null and `GetVersionString()` must equal `1.31.0`; then `Ort::InitApi`. The core
is compiled with `ORT_API_MANUAL_INIT`. Library location: the plugin uses the bundled file (`bundledOrtFileName()`) in the
same folder as its own binary inside the VST3 bundle (`Contents/x86_64-win/` or `Contents/x86_64-linux/`) or the Standalone
executable; the CLI uses `--ort-lib` or the file beside its executable; tests use `SINGVST_TEST_ORT_LIB` (compile-time
absolute path). The build copies the library to those places. Tests: T-041 (both OSes in CI), T-059 (pluginval).

### D-013 Render pipeline and background renderer
`renderTake`: `mono = toMonophonic(notes)`; no notes → `ValidationError`; `align` (warnings appended); `layoutPhonemes(bpm)`;
`durations = spansToFrameDurations(spans, 44100/512)`; `f0g = f0Curve(…, fr = 44100/512, total = sum(durations)/fr,
portamento, vibrato)`; `guide.render`; if `conversionEnabled` and a converter is present: `f0c = f0Curve(…, fr = 100, total =
len(guide)/44100, …)`, `converter.convert(guide, 44100, f0c, seed)`; finally `resample` to `outputSampleRate`.
`startBeat` = first monophonic note's start, `bpm`, `sampleRate`, `unclippedPeak = peakAbs(samples)`, `contentHash =
phraseHash(request.notes, request.tokens, request.params)` (the request as submitted). No clipping.
`Renderer`: one worker thread. `submit` sets the in-flight job's cancel flag and queues the new request (only the newest
queued request is kept). A request whose hash equals the current Ready take's `contentHash` is not rendered (status stays
Ready). On success the take replaces `latest()` and status is Ready; on an exception status is Failed, `lastError()` holds
`what()`, and `latest()` keeps the previous take; a `Cancelled` job is discarded silently. `renderCount()` counts completed,
non-discarded renders. The destructor cancels and joins within 5 s. Tests: T-048…T-051.

---

## Playback and plugin

### D-009 Host time mapping and phrase hash
Take sample for host PPQ `q`: stale when `|hostBpm − take.bpm| > tol` → none; else `k = floor((q − startBeat)·60/bpm·sr + 0.5)`,
valid when `0 ≤ k < size`. `phraseHash`: FNV-1a 64 (offset 14695981039346656037, prime 1099511628211) over the UTF-8 string
made of, per note, `n:<start %.9f>:<end %.9f>:<midi>;`, per token `t:<kind 0|1|2>:<text>:<phonemes joined by ' '>:<0|1>;`,
then `p:<voiceId>:<bpm %.9f>:<outputSampleRate>:<0|1 conversion>:<portamento %.9f>:<vibrato %.9f>:<seed>;`
(`%.9f` = C `printf`, '.' decimal point regardless of locale). Golden: one note (0, 1, 60), token `la`, params
(`v1`, 120, 48000, true, 0.06, 0, 0) → `14710552853263154277`. Tests: T-032, T-034.

### D-022 Audio thread
`processBlock` never locks, allocates, frees or waits (PK-38). The current take is handed over through `TakeSlot`
(single writer = message thread, single reader = audio thread): `publish` stores the new take as current and retires the old
one; `acquire` marks the current take in use and returns it; `release` clears the mark; `collect` (writer side, timer) frees
retired takes not in use. `renderBlock` (header) produces the mono signal; the plugin copies it to every output channel.
Incoming MIDI is ignored except while capturing (D-010). Tests: T-033, T-037, T-038, T-055.

### D-010 Plugin behaviour and parameters
Parameters are exactly `kParams` (`params.hpp`), in that order, JUCE `ParameterID{id, 1}` (PK-40); `docs/PARAMETERS.md` is
generated from the same table (S-018). Lyrics come from the editor's text box or from **MIDI-file import**, because hosts
cannot pass lyric text to a JUCE VST3 (C-011): import uses `importMidi` (D-031) and replaces the stored notes,
lyrics and bpm; a malformed or SMPTE file → `false` + `lastError`, nothing replaced. Capture: `Idle → Armed` (arm button) → `Capturing` (first block with transport playing
while armed; event positions = block PPQ + sample offset · bpm / (60 · sample rate)) → on the first stopped block:
`CaptureRecorder::finish` at the end of the last playing block (its PPQ + block length in beats),
stored notes replaced, bpm taken from the host, render submitted, back to `Idle`; disarm returns to `Idle` and keeps stored
notes. Renders are submitted (message thread, 4 Hz timer) after: capture end, import, voice load, lyric edits (500 ms after
the last keystroke), changes of `convert`/`portamento`/`vibrato`/`seed`, a host tempo differing from the take's by > 0.1
bpm, or a host sample rate differing from the take's. `gain` never triggers a render. No voice loaded → no render and
`lastError()` = `Load a voice`. `lastWarnings()` = the warnings of the most recent import or completed render, whichever was
last. Capture never allocates on the audio thread (D-022): `arm(true)` preallocates a buffer of 4096 raw note events; the
audio thread appends `(ppq, note, on/off)` without allocating (events beyond 4096 are dropped and counted); the message-thread
timer feeds them to `CaptureRecorder`, and after the stop it stores the notes (a dropped-event count > 0 adds the warning
`capture buffer full: <n> events dropped`). The plugin finds `cmudict.dict` and the ONNX Runtime library beside its own
binary (`juce::File::currentExecutableFile`, which is the plug-in module itself when hosted; D-024). State = `PluginState` JSON (UTF-8) carrying lyrics, voice path, stored notes, render params and
gain; restore applies the parameters, loads the voice if the path exists (else `lastError`, notes and lyrics kept) and
submits a render; malformed state → defaults kept and `lastError` set. Tests: T-035, T-036, T-053…T-058.

### D-027 Editor
One resizable window: lyrics text editor (multi-line), buttons *Load voice…*, *Import MIDI…*, *Arm capture* (toggle),
a status line (render status, last error) and a warnings list, and the five parameters as sliders/toggle (generated from
`kParams`). Behaviour that cannot be exercised headless (layout, focus, file dialogs, keystroke debounce feel) is
**implemented, unverified** and listed in the G-001 checklist (PK-39).

### D-031 Standard MIDI File import (`importMidi`)
The bytes are untrusted (PK-42): every read is bounds-checked and any violation → `ValidationError` naming it.
Header `MThd`, length ≥ 6, format 0 or 1 (2 → error), track count, division: bit 15 set (SMPTE) → error; PPQ must be > 0.
Chunks follow; `MTrk` chunks are parsed, other chunk types are skipped by their length; a length past the end → error.
Events: delta time as a variable-length quantity of at most 4 bytes; running status for channel messages (a data byte with
no running status → error); `8x` note-off, `9x` note-on (velocity 0 = note-off), `Ax`/`Bx`/`Ex` two data bytes, `Cx`/`Dx`
one; `F0`/`F7` sysex skipped by length; `FF` meta: type, length, data — `05` lyric, `51` tempo (3 bytes, µs per quarter;
other lengths → error), `2F` end of track; other metas ignored. Notes: keyed by (channel, key); a note-on while the key is
held closes the held note at that tick and starts a new one; a note-off with nothing held is ignored; notes still held at
the end of their track close at the track's last tick; zero-length notes are dropped; beats = ticks / PPQ; sorted by
(start, pitch). Lyrics: all lyric events of all tracks ordered by (tick, track, order in track), each trimmed of ASCII
whitespace, empty ones skipped, joined with one space (so `hel-`, `lo` → `hel- lo`, D-004). Tempo: the event with the lowest
tick (then lowest track) sets `bpm = 60e6 / µs`; none → 120; any tempo event at a later tick with a different value adds the
warning `tempo changes after beat <b> are ignored` (b = its beat, `%g`). Tests: T-064…T-066.

### D-014 CLI `singvst-render`
`singvst-render --voice DIR --midi FILE --out FILE.wav [--lyrics TEXT | --lyrics-file FILE] [--dict FILE] [--seed N]
[--no-convert] [--bpm X] [--rate HZ] [--gain-db X] [--raw] [--ort-lib PATH]` and `singvst-render --check-voice DIR`.
Notes, lyrics and tempo come from the MIDI file as in D-010 unless overridden. Output: mono 32-bit float WAV at `--rate`
(default 48000), soft-clipped (D-021) unless `--raw`, plus `<out>.provenance.json` with `git_commit` (compile-time),
`voice_sha256` (of manifest.json), `params`, `seeds` (`{"converter": <seed>}`), `utc_timestamp`, `hardware`, `threads`, `ort_version`, `warnings`,
`unclipped_peak`, `render_seconds`, `audio_seconds`. `--check-voice` prints `ok <name>` (exit 0). Exit codes: 0 success; 2
usage, missing file or invalid voice (stderr names the cause, containing the word `voice` for voice errors); 3 render
failure. Tests: T-P13, T-P18.

---

## Training, evaluation and Python toolkit

### D-015 Python toolkit
Package `python/singvst_train` (Python 3.12): `prepare`, `pipeline`, `provenance`, `metrics`, `pack`, `security`,
`rvc_files`, `export_rvc`, `evaluate`, `cli`. Signatures are frozen in the stubs. Every result file gets a provenance sidecar
`<file>.provenance.json` with `git_commit`, `lockfile_sha256`, `seeds`, `params`, `utc_timestamp` (ISO-8601 `Z`),
`hardware` (platform, CPU, GPU name or `none`), `threads` (protocol 2B.2). pyworld is loaded through its compiled extension
(`metrics.load_pyworld`) because `import pyworld` fails with setuptools 84 (C-046). The frozen interface record
`tests/python/interfaces.json` (signatures, docstring hashes, constants; `tools/gen/interfaces.py`) is checked by T-P27.
Tests: T-P01…T-P15, T-P24…T-P27.

### D-016 Training on a free hosted GPU
Training runs where the owner has a free GPU (A-009): **Google Colab** free tier (primary) or **Kaggle** (fallback), driven by
`notebooks/train_voice_colab.ipynb` / `notebooks/train_voice_kaggle.ipynb`, which the owner runs at gate G-004 (the
implementer cannot reach these hosts; C-044). Rules (C-017, C-018, C-019): the first code cell runs `nvidia-smi`; a consent
cell requires `CONSENT_CONFIRMED = True` plus a one-line attestation (A-011); every training action is a notebook cell that
calls `python -m singvst_train.cli <command>` — no web UI, no tunnels, no `--share`; data moves to and from Drive (or Kaggle
datasets) as single `tar` archives. Stages are resumable (`pipeline.run_stages`, markers on Drive) and RVC resumes from the
newest checkpoint in `logs/<exp>` (C-047), which is kept on Drive (Colab) or in the output dataset (Kaggle); checkpoints every
10 epochs with `-l 1 -sw 1` (C-022). The notebooks pin RVC 81eed5e, install its CUDA requirements from the official indexes
(D-019), download the RVC assets from Hugging Face (C-032), and run: prepare → RVC preprocess/f0/features/train (48 kHz, v2,
f0, rmvpe; C-022, C-029, C-030) → export (D-012) → build `singvst-render` (core only) → evaluate (D-017) → pack (D-008) →
archive to Drive. Budget: ≤ 20 GPU-hours per voice (A-015), each session ≤ 10 h of work.

### D-017 Evaluation (unknown outcomes)
Procedure (frozen as code in `evaluate.py` and `eval/PROCEDURE.md`; values recorded at G-001, never typed — PK-05):
the five original **evaluation phrases** in `eval/phrases/` (MIDI with lyric meta events; written for this project, no
third-party lyrics) are transposed by whole semitones so their median pitch is nearest the median F0 of the training data,
then rendered twice with `singvst-render` (seed 0): with and without conversion.
- **Speaker similarity**: cosine between the Resemblyzer 0.1.4 embedding (C-028) of each converted render and the mean
  embedding of the held-out source recordings (10 % by file, `split_heldout`, never trained on); the guide-only render gives
  the **baseline** (PK-35); gain = converted − baseline.
- **F0 accuracy**: pyworld harvest + stonemask (f0 50–1100 Hz, 10 ms) on each converted render; per note, frames more than
  50 ms from both note edges (PK-33); RMS of cents error against `midiToHz` (A4 = 440 Hz); frames with |error| > 600 cents are
  counted as tracker octave errors, reported, and excluded (PK-31).
- **Intelligibility**: Whisper `small.en` (openai-whisper 20250625) transcript of each converted render; WER against the
  phrase lyrics after `normalise_text`.
- **Speed**: real-time factor of `singvst-render` on the notebook's CPU (render seconds / audio seconds), and on the owner's
  computer at G-001.
`eval/thresholds.json` holds the **unmeasured defaults** (similarity ≥ 0.75, gain ≥ 0.15, F0 ≤ 25 cents RMS, WER ≤ 0.25,
RTF ≤ 1.0) with `"status": "unmeasured-default"`; `judge` reports verdicts against them, and G-001 decides which values bind
(PK-29). The metrics themselves are validated on known-answer signals (T-P09…T-P11; PK-31).

### D-019 Python environments
1. Toolkit (CI, sandbox): `python/requirements-lock.txt` (complete `pip freeze --all`, includes pip/setuptools/wheel;
   pip-audit clean; reproduced exactly in a clean venv on 2026-10-14). 2. RVC training (notebooks): RVC's own
   `requirments_cu128_py312.txt` with the mirror indexes replaced by pypi.org / download.pytorch.org (C-023), plus the toolkit
   installed `--no-deps` and `onnx==1.17.0` for export, `resemblyzer==0.1.4`, `openai-whisper==20250625` for evaluation.
3. CI export-parity job: RVC's `requirments_cpu_py312.txt` (torch 2.4.1+cpu) the same way.

### D-025 De-reverb
Optional and **off by default**. The candidate (audio-separator 0.47.0 with the MelBand-Roformer de-reverb model; C-043) has no
stated model licence, so the owner decides at G-004 whether to use it; otherwise the owner supplies dry recordings (or the
dryest subset). `prepare --dereverb` is the only switch.

---

## Process

### D-018 Continuous integration
GitHub Actions workflow `.github/workflows/ci.yml`, triggered on push and pull request (no `workflow_dispatch` on the critical
path; PK-15). Jobs: `repo` (freeze manifest, workflow lint, ignore rules, claim references, secret scan, lock audit),
`cpp` (matrix `ubuntu-24.04`, `windows-2022`: build, ctest, pluginval 1.0.4 strictness 5 with `--skip-gui-tests`
on Linux under xvfb; C-015), `sanitizers` (Linux, ASan+UBSan for all C++ tests; TSan for T-038, T-050, T-051), `python`
(toolkit tests with the Linux CLI artifact), `python-torch` (export parity T-P19). Action major tags per C-045. Results are
read through the GitHub REST API (jobs, steps, check-run annotations), because the Actions results host is unreachable from the
sandbox (C-044, PK-14); failing steps emit `::error::` annotations with the failing test names.

### D-023 Red-verification exemptions
Tests that check repository or environment properties, not stub behaviour, are exempt from "must fail against stubs":
T-059 (pluginval: the silent stub plugin is a valid VST3), T-060 (freeze manifest), T-061 (workflow lint), T-062 (ignore
rules), T-P21 (lock reproducible and audit clean), T-P22 (cited IDs exist), T-P23 (README citations; written at S-019),
T-P27 (interface record). Record: research/spikes/red-verification/. Every other test must fail cleanly (PK-25).

### D-026 Licences
sing-vst code: Apache-2.0. JUCE 9.0.3: AGPLv3 or commercial (C-012) — any distributed plugin binary is under AGPLv3 unless the
owner holds a JUCE licence; no binaries are released by this plan (G-002). ONNX Runtime: MIT (shipped beside the binary with
its licence). CMUdict: BSD-style (licence file beside the dictionary). RVC: MIT (C-001); its pretrained base models are trained
on VCTK (C-031). TIGER guide voicebank: CC BY-NC-ND 4.0 + Commons Clause / MIT-style non-commercial (C-037) — personal,
non-commercial use only, **never committed, bundled or redistributed**; voice packages that contain it stay on the owner's
machine or private Drive (G-005). openvpi vocoders (fallback only): CC BY-NC-SA 4.0 (C-007). `THIRD_PARTY_NOTICES.md` lists
all of these (S-018).

### D-029 Git and checkpoint rules
The implementer works on `impl-<run_id>` (from the generation branch). Every command that writes into the repository ends
with `bash tools/save.sh "<msg>" <paths>` (commit + push in the same call; lesson L-20261014T195500Z); one commit per plan
step at minimum, rewriting `.checkpoints/state.json` with `tools/checkpoint.py`, appending `EXECUTION_LOG.md`; the last call
of every turn is `bash tools/turn_end_check.sh` (PK-01, PK-03). At the end a pull request impl → `main` is opened (S-018);
merging it is the owner's decision.

### D-030 Claims about behaviour
Every sentence in README.md or docs/ that states behaviour cites a test ID; statements about how the voice *sounds* appear only
with a G-001 listening record (PK-04, PK-46). T-P23 checks the citations exist.

---

## Decision rules (if → then)

**Engineering forks** `[software]`
- DR-01 An ONNX model's input or output name/shape differs from D-012 → do not adapt the engine silently: if it is a
  documented optional input, use it as D-012 says; otherwise `ValidationError` at load, and if it is the TIGER pack or an RVC
  export produced by this plan, halt and write `BLOCKED.md`.
- DR-02 A pinned download fails its SHA-256 → halt, `BLOCKED.md`; never update the hash to match.
- DR-03 A pinned dependency fails to install or build → retry once; if the failure is an upstream outage, wait for the next
  turn; otherwise `BLOCKED.md` (no version changes without a decision record).
- DR-04 A frozen test is wrong → `TEST_CHALLENGE.md` and halt (Rule 2E.4); never edit it (PK-24).
- DR-05 pluginval fails at strictness 5 → fix the plugin; if the failure is a pluginval defect reproduced with a JUCE example
  plugin, record it in `DEVIATIONS.md` with the log and continue.
- DR-06 Windows explicit-path loading (T-041) fails in CI → try `LoadLibraryExW` with `LOAD_LIBRARY_SEARCH_DLL_LOAD_DIR |
  LOAD_LIBRARY_SEARCH_DEFAULT_DIRS`; if it still fails, `BLOCKED.md`.
- DR-07 pip-audit reports a vulnerability in the lock → upgrade that package to the first fixed version, regenerate the lock in
  a clean venv, re-run the whole Python suite; if the fix is incompatible, `BLOCKED.md`.
- DR-08 Guide RTF on the CI Linux runner > 3 (C-039 measured 1.10 on 2 threads) → record it; reduce `steps` only at G-001.
- DR-09 A host cannot load the plugin (owner report) → collect the host log at G-001; no speculative fixes.

**Result-pivot rules** `[computational]` (Rule 8)
- DR-10 Converted similarity does not exceed the guide baseline (gain ≤ 0) → record the values, do not tune evaluation, halt at
  G-001 with the options: more/cleaner data, more epochs, de-reverb (D-025), or a different guide speaker embedding.
- DR-11 F0 RMS error above the default, or octave errors > 5 % of scored frames → re-run the tracker check on a known tone
  (T-P10) to rule out the metric, then record and halt at G-001.
- DR-12 WER above the default → compare with the guide-only render's WER; record both; halt at G-001.
- DR-13 Training does not finish within the budget (D-016) → stop at the last checkpoint, export it, evaluate, halt at G-001.
- DR-14 Export parity (T-P19) exceeds 1e-3 → do not loosen the tolerance; inspect the noise input and fp16 → fp32 cast
  (C-048); if unresolved, `BLOCKED.md`.

**Default rule** `[All]`: choose the most reversible option that does not expand scope, log it in `DEVIATIONS.md` with
rationale, and continue — unless it touches frozen tests, security, data integrity, a public interface, research integrity,
licences or consent, in which case halt and write `BLOCKED.md`.
