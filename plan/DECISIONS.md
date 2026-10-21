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
`ORT_ENABLE_ALL`, inter-op threads 1, intra-op threads `min(4, max(1, hardware_concurrency / 2))`, the session config
entry `session.set_denormal_as_zero` = `1` (R-045), and the CPU memory arena disabled (`DisableCpuMemArena`) so a long
phrase's peak is not retained (R-060).

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
`m50 = 1127·ln(1 + 50/700)` and `m1100 = 1127·ln(1 + 1100/700)` (RVC's f0_min/f0_max in mel; C-021).

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
Required keys: `format`, `format_version`, `name`, `consent`, `guide_licence`, `guide.type`, `guide.sample_rate`,
`guide.hop_size`, `guide.steps`, `guide.depth`, `guide.files`, `sha256`, and — when `converter` is an object — `type`,
`sample_rate`, `files`. Defaults: `guide.language` = `en`, `converter.speaker_id` = 0, `converter` absent = null. A missing
required key is a violation. Rules (each violation → `ValidationError` naming the field): valid JSON object; exact `format`/`format_version`; non-empty
strings; `guide.type == "diffsinger"`, `sample_rate == 44100`, `hop_size == 512`, `steps` integer 1…1000, `depth` number in
(0, 1], `language` non-empty (default `en` when absent); required file roles present, no unknown role; `converter` absent,
null, or `type == "rvc-v2"`, `sample_rate` ∈ {48000, 32000} (C-005), `speaker_id` integer ≥ 0 (default 0), roles `synth`
and `content` only; every file path is *safe* — non-empty `/`-separated segments of `[A-Za-z0-9._-]`, no segment `.` or
`..`, no leading `/`, no `\`, no `:` — and the set of `sha256` keys equals the set of referenced paths, each value 64
lower-case hex digits. Unknown top-level keys are ignored. `validatePackage` then checks each referenced file is a regular
file under the directory, at most `maxFileBytes`, with a matching SHA-256 (`sha256Hex`, FIPS 180-4, implemented in the core; D-001). Speaker embedding file:
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
`SP` frames before and after; a phrase longer than 2584 frames (30 s) is split further, recursively, at its longest
internal `SP` span, else at the span boundary nearest its middle frame whose next span starts with a consonant (`isVowel`,
D-005 — so the seam falls before an onset, not inside a vowel), else at the span boundary nearest its middle; an internal
`SP` span shorter than 22 frames belongs whole to the earlier part; each part is padded like any phrase and the output
length stays exactly `sum(durations)·512`, so memory per model run is bounded (R-060, R-077) (C-038; padded f0 = the phrase's first/last value; per-frame inputs cover the padded length).
Acoustic output `mel` float[1,T+16,128] goes to the vocoder with the padded f0 (inputs `mel`, `f0`; output `waveform`
float[1,(T+16)·512]); 8·512 samples are trimmed from each end. Output length is exactly `sum(durations)·512`. `cancel` is
checked before every model run → `Cancelled`; while a model run is in flight a watcher polls `cancel` every 10 ms and calls
`Ort::RunOptions::SetTerminate()` on that run's `RunOptions`, and the resulting ONNX Runtime error is reported as
`Cancelled` (R-025). The acoustic model draws its own noise (C-040): the guide is not reproducible — the plugin recalls
takes from the take cache (D-038), never by re-rendering. Both engines reject at load, with `ValidationError`, a model
whose initializers use external data (R-027), detected by a bounded protobuf walk of the model bytes: ModelProto field 7
(graph) → GraphProto field 5 (initializer) → TensorProto field 14 (`data_location`) = 1 (EXTERNAL) or any field 13
(`external_data`); malformed bytes → `ValidationError`. S-008 verifies it with a throw-away check (not a committed test: `tests/` is frozen) — a program under
`research/spikes/s008-external-data/` linked against `../build-core/core/libsingvst_core.a`, loading a copy of a fixture model saved
by `onnx.save(..., save_as_external_data=True)`.

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
non-discarded renders. The destructor cancels and joins (never detaches); with the D-012 terminate watcher a real
engine stops within one graph node, and T-051 bounds the fake at 5 s. Engines are owned through `std::shared_ptr`: the
`RenderFn` a job runs holds its own references, so loading another voice or destroying the plugin never frees an engine a
running job uses (R-025). Before `align`, `renderTake` rejects a monophonic take of more than 5000 notes or ending more
than 900 s after its first note at `params.bpm`, with a `ValidationError` naming the limit (D-038, T-070; R-027).
Tests: T-048…T-052, T-070.

---

## Playback and plugin

### D-009 Host time mapping and phrase hash
Take sample for host PPQ `q`: stale when `|hostBpm − take.bpm| > tol` → none; else `k = floor((q − startBeat)·60/bpm·sr + 0.5)`,
valid when `0 ≤ k < size`, where `bpm` = `take.bpm` (the take's own tempo, set when it was rendered) and `sr` =
`take.sampleRate`; `hostBpm` only decides staleness (T-032). `phraseHash`: FNV-1a 64 (offset 14695981039346656037, prime 1099511628211) over the UTF-8 string
made of, per note, `n:<start %.9f>:<end %.9f>:<midi>;`, per token `t:<kind 0|1|2>:<text>:<phonemes joined by ' '>:<0|1>;`,
then `p:<voiceId>:<bpm %.9f>:<outputSampleRate>:<0|1 conversion>:<portamento %.9f>:<vibrato %.9f>:<seed>;`
(`%.9f` = C `printf`, '.' decimal point regardless of locale). Golden: one note (0, 1, 60), token `la`, params
(`v1`, 120, 48000, true, 0.06, 0, 0) → `14710552853263154277`. Tests: T-032, T-034.

### D-022 Audio thread
`processBlock` never locks, allocates, frees or waits (PK-38). The current take is handed over through `TakeSlot`
(single writer = message thread, single reader = audio thread): `publish` stores the new take as current and retires the old
one; `acquire` marks the current take in use and returns it; `release` clears the mark; `collect` (writer side, timer) frees
retired takes not in use. **Protocol** (R-024; all atomics `seq_cst`; `BUSY` = the address of a private static sentinel):
`acquire`: `inUse.store(BUSY)`; `p = current.load()`; `inUse.store(p)`; return `p`. `release`: `inUse.store(nullptr)`.
`publish` (writer mutex): `old = current.exchange(new)`; a non-null `old` goes to `retired`. `collect` (writer mutex): `u =
inUse.load()`; `u == BUSY` → free nothing; else free every retired take `!= u`. S-005 implements exactly this sequence.
`renderBlock` (header) produces the mono signal; the plugin renders into channel 0 and copies it to the other channels (no
scratch buffer). Incoming MIDI is ignored except while capturing (D-010). **Plugin threading** (R-026): the capture buffer
is a single-producer/single-consumer FIFO (`juce::AbstractFifo` over 4096 preallocated events) allocated once in the
constructor. The capture state is one `std::atomic<int>` with an internal fourth value `Stopping` (reported as `Capturing`):
every transition is a compare-and-swap on both threads (R-078): the message thread moves `Idle`→`Armed`,
`Armed`→`Idle` and `Capturing`→`Cancelling` (disarm during a capture; a fifth internal value, reported as `Idle`);
`processBlock` moves `Armed`→`Capturing` and `Capturing`→`Stopping` and writes FIFO events only while `Capturing`; a
failed CAS means the other thread won and the loser does nothing; the timer, after draining the FIFO in `Stopping`,
finishes the capture (stored notes replaced, warning `stored notes replaced; the previous take stays in the take cache`),
or in `Cancelling` discards the drained events (stored notes kept), then resets the FIFO indices and stores `Idle` — the indices are never reset while the audio
thread may write (R-064). Host bpm, sample rate and transport state reach the message thread
through `std::atomic` values written by `processBlock`; every other piece of state (lyrics, stored notes, voice, engines,
render parameters) is guarded by one message-side mutex that `processBlock` never takes, and `get/setStateInformation`
take it too. `processBlock` runs under `juce::ScopedNoDenormals` (R-045). Tests: T-033, T-037, T-038, T-055.

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
bpm. A host sample rate differing from the take's never re-renders (R-059, R-072): `RenderParams::outputSampleRate` is
always 48000 (the state default), so the request and its cache key never depend on the host rate; the plugin owns a
second worker (one `std::thread`, newest request wins) that, whenever the original take (the Renderer's `latest()` or a
cache hit) or the host rate changes, publishes `resampleTake(original, hostRate)` (D-038, T-071) — always from the
original, never from a resampled copy — or the original itself when the rates match. `gain` never triggers a render. Blocking conditions are checked in this order and only the first that holds is reported:
no voice, lyrics that fail to parse, no stored notes. No voice loaded → no render and
`lastError()` = `Load a voice`. Lyrics that fail `parseLyrics` → no render, `lastError()` = `Lyrics: <ParseError message>`.
No stored notes → no render and no error (status stays as it was). The renderer's function is
`cachedRender(fn, <user application data>/sing-vst/takes)` (`juce::File::userApplicationDataDirectory`; D-038), so a
restored project, a voice reload or an undo plays the stored take bit-for-bit instead of a new performance (R-017); the
cache is never pruned automatically (README says where it is). The status line shows the loaded voice's manifest name
and the first 8 hex digits of its `voice_sha256` (R-015). On restore the plugin first looks the restored request up
in the take cache (`phraseHash` of the stored notes, `parseLyrics` of the stored lyrics and the stored params, whose
`voiceId` is the voice's SHA) and publishes a hit even when the voice folder cannot be found (status "voice not found —
playing the stored take"); a miss on a restored project with notes adds the warning `approved take not found in the take
cache; a new performance was rendered` (R-059). The status line also shows the cache's total size (R-058). `lastWarnings()` = the warnings of the most recent import or completed render, whichever was
last. Capture never allocates on the audio thread (D-022, whose **Plugin threading** rule wins: the 4096-event FIFO is
allocated once in the constructor; D-022 governs the capture state and FIFO reset); the
audio thread appends `(ppq, note, on/off)` without allocating (events beyond 4096 are dropped and counted); the message-thread
timer feeds them to `CaptureRecorder`, and after the stop it stores the notes (a dropped-event count > 0 adds the warning
`capture buffer full: <n> events dropped`). The plugin finds `cmudict.dict` and the ONNX Runtime library beside its own
binary (`juce::File::currentExecutableFile`, which is the plug-in module itself when hosted; D-024). State = `PluginState` JSON (UTF-8) carrying lyrics, voice path, stored notes, render params and
gain; restore applies the parameters, loads the voice if the path exists (else `lastError`, notes and lyrics kept) and
submits a render; malformed state → defaults kept and `lastError` set. Tests: T-035, T-036, T-053…T-058.

### D-027 Editor
One resizable window: lyrics text editor (multi-line), buttons *Load voice…*, *Import MIDI…*, *Arm capture* (toggle),
a status line (render status, last error) and a warnings list, and the five parameters as sliders/toggle (generated from
`kParams`). File dialogs use `juce::FileChooser::launchAsync`; the editor runs no modal loop (R-048). Behaviour that cannot be exercised headless (layout, focus, file dialogs, keystroke debounce feel) is
**implemented, unverified** and listed in the G-001 checklist (PK-39).

### D-031 Standard MIDI File import (`importMidi`)
The bytes are untrusted (PK-42): every read is bounds-checked and any violation → `ValidationError` naming it. Limits
(R-027, T-069): more than 5000 notes, or a note ending more than 900 s after time 0 at the file's `bpm`, → `ValidationError`
naming the limit. Running status persists across meta (`FF`) and sysex (`F0`/`F7`) events, as common readers do (R-046).
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
`unclipped_peak`, `render_seconds`, `audio_seconds`. `git_commit` is written into a generated header by a build-time custom
command that runs on every build, so an incremental rebuild never stamps an old commit (R-047). Shapes: `params` = the effective options after defaults, `{"bpm",
"rate", "gain_db", "raw", "convert", "dict", "lyrics_source": "midi"|"text"|"file"}`; `hardware` = `{"os": <uname
sysname + release, or the Windows version>, "cpu": <CPU model string, or "unknown">, "logical_cores":
std::thread::hardware_concurrency()}`; `threads` = the ONNX Runtime intra-op thread count used (integer);
`render_seconds` = wall-clock seconds of the `renderTake` call only (model, dictionary and runtime loading excluded);
`audio_seconds` = output samples / `--rate`. `--seed` defaults to 0. `--check-voice` prints `ok <name>` (exit 0). Exit codes: 0 success; 2
usage, missing file or invalid voice (stderr names the cause, containing the word `voice` for voice errors); 3 render
failure. Mechanical rule: the CLI itself calls, in order, argument parsing, `parseManifest` + `validatePackage`, engine loading,
`importMidi`, `parseLyrics`, dictionary loading and `toMonophonic` (empty result → "no notes"); any exception from these
exits 2. It then calls `renderTake`; **any** exception from `renderTake` (including `ValidationError`, e.g. an unknown
phoneme, and ONNX Runtime errors) exits 3.
`--check-voice` runs `parseManifest`, `validatePackage`, `GuideEngine::load` and, when present, `ConverterEngine::load`.
`RenderParams::voiceId` is the voice's `voice_sha256` (SHA-256 of its manifest.json) in the CLI and the plugin, so loading a
different voice always changes the phrase hash. Tests: T-P13, T-P18.

---

## Training, evaluation and Python toolkit

### D-015 Python toolkit
Package `python/singvst_train` (Python 3.12): `prepare`, `pipeline`, `provenance`, `metrics`, `pack`, `security`,
`rvc_files`, `export_rvc`, `evaluate`, `cli`. Signatures are frozen in the stubs. The result files — `dataset.json`
(`prepare`) and `report.json` (`evaluate`) — get a provenance sidecar (renders get the D-014 one; intermediate files —
`split.json`, ONNX exports, the voice package, `verdict.json` (derived from `report.json`), `budget.json` — get none)
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
datasets) as single `tar` archives, except the RVC experiment and weights, which D-035 keeps on Drive through symlinks (R-033). Stages are resumable (`pipeline.run_stages`, markers on Drive) and RVC resumes from the
newest checkpoint in `logs/<exp>` (C-047), which is kept on Drive (Colab) or in the output dataset (Kaggle); checkpoints every
10 epochs with `-l 1 -sw 1` (C-022). The notebooks pin RVC 81eed5e, install its CUDA requirements from the official indexes
(D-019), download the RVC assets from Hugging Face (C-032), and run: prepare → RVC preprocess/f0/features/train (48 kHz, v2,
f0, rmvpe; C-022, C-029, C-030) → export (D-012) → build `singvst-render` (core only) → evaluate (D-017) → pack (D-008) →
archive to Drive. Budget: ≤ 20 GPU-hours per voice (A-015), each session ≤ 10 h of work.

### D-017 Evaluation (unknown outcomes)
Procedure (frozen as `eval/PROCEDURE.md` and implemented in `evaluate.py`; values recorded at G-001, never typed — PK-05):
the five original **evaluation phrases** in `eval/phrases/` (MIDI with lyric meta events; written for this project, no
third-party lyrics) are transposed by one whole-semitone shift so their pooled median pitch is nearest the median F0 of the
**held-out** recordings (eval/PROCEDURE.md wins over any other wording),
then rendered with `singvst-render` (seed 0) with and without conversion, `evaluate.REPEATS` = 5 times each because the
guide's noise is unseeded (C-040); every metric is the mean over the repeats and `spread.json` holds the per-repeat values
(R-018). At G-001 a threshold that lies within a metric's [min, max] spread is reported as **indeterminate** for that
metric (`spread.json`'s "numeric report keys" are exactly the seven metrics `speaker_similarity`, `guide_similarity`,
`f0_rms_cents`, `octave_fraction`, `wer`, `guide_wer`, `realtime_factor`; inclusive bounds; for `similarity_gain` the per-repeat values are `speaker_similarity[i] − guide_similarity[i]`). `ceiling.json` (held-out against training-file embeddings) is shown beside the similarity as its same-singer
ceiling (R-032); similarity is a proxy that only the G-001 listening record confirms.
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
   installed `--no-deps` and `onnx==1.23.2` and `onnxruntime==1.31.0` for export (same pins as the lock; the cu128 export is
   checked in the notebook by running T-P19 before training — D-035), `resemblyzer==0.1.4`, `openai-whisper==20250625` for evaluation.
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
`cpp` (matrix `ubuntu-24.04`, `windows-2022`: on Linux `sudo locale-gen de_DE.UTF-8` for T-034 (C-056) and plugin tests
under `xvfb-run -a`; build, ctest, pluginval 1.0.4 strictness 5 with `--skip-gui-tests`
on Linux under xvfb; C-015), `sanitizers` (Linux, ASan+UBSan for all C++ tests; TSan for T-038, T-050, T-051), `python`
(toolkit tests with the Linux CLI artifact), `python-torch` (export parity T-P19). Action major tags per C-045. Results are
read through the GitHub REST API (jobs, steps, check-run annotations), because the Actions results host is unreachable from the
sandbox (C-044, PK-14); failing steps emit `::error::` annotations with the failing test names.

### D-023 Red-verification exemptions
Tests that check repository or environment properties, not stub behaviour, are exempt from "must fail against stubs":
T-059 (pluginval: the silent stub plugin is a valid VST3), T-060 (freeze manifest), T-061 (workflow lint), T-062 (ignore
rules), T-P21 (lock reproducible and audit clean), T-P22 (cited IDs exist), T-P23 (README citations; red until S-018 writes the README section),
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
of every turn is `bash tools/turn_end_check.sh` (PK-01, PK-03). At the end a pull request impl → `main` is opened (S-019);
merging it is the owner's decision.

### D-030 Claims about behaviour
Every sentence in README.md or docs/ that states behaviour cites a test ID — except `docs/UNVERIFIED.md`, whose bullets are
explicitly labelled implemented-but-unverified behaviour (PK-04, PK-39); statements about how the voice *sounds* appear only
with a G-001 listening record (PK-04, PK-46). T-P23 checks the citations exist.

### D-032 Figures (2C)
The `computational` profile applies 2C only to deliverable figures. This plan has none: results are `report.json`, its
provenance sidecar and audio renders reviewed at G-001. No `figures/SPEC.md` is produced; if the owner later asks for plots
of the evaluation, that is a new planning amendment.

### D-033 Implementation conventions
Code compiles with GCC ≥ 11 and MSVC 2022 (no `<format>`, `<print>` or `std::expected`; the notebook builds the CLI with the
hosted image's compiler, R-023). Private helpers and private headers live in `core/src/` (never `core/include/singvst/`, whose files are all frozen;
T-060). Each core step adds `core/src/<module>.cpp` for its header and **deletes the matching definitions from
`core/src/stubs.cpp`** in the same commit (`core/CMakeLists.txt` globs `src/*.cpp`, so a duplicate definition is a link
error, not a silent override). The plugin step replaces `plugin/PluginProcessor.cpp` and adds `plugin/PluginEditor.*`; the
CLI step replaces `cli/main.cpp`; Python steps replace the bodies in `python/singvst_train/*.py` without touching any
signature or docstring (T-P27). Helpers in those modules are named with a leading underscore, no new upper-case module constants
are added, and heavy optional packages (torch, onnx, onnxruntime in export code, audio_separator, resemblyzer, whisper) are
imported inside the functions that use them, so the toolkit imports in the lock venv (T-P25, T-P27). Private helpers may be
added freely in new modules named with a leading underscore. `standardNormal` (declared in engine.hpp) lives in
`core/src/random.cpp` (S-007).

### D-034 Protocol version
The run started under planning protocol v3.2 and adopts **v3.3** (qualitycoding/skills `9636a79`, read 2026-10-15) from
Phase 3 onward: checkpoints carry `sequence`, `active_step_id`, `execution_context` and `active_variables`, are written
atomically (`state.tmp.json` → `state.json`) with a snapshot in `.checkpoints/snapshots/`, on every save and before every
high-latency action (subagent, long build, web research, gate wait) — `tools/checkpoint.py`, called by `tools/save.sh`.
The implementer resumes with the zero-context procedure of v3.3 1.2.3 (HANDOFF.md §Resume).

### D-035 Toolkit CLI and training notebook
**Exit codes and errors:** as `cli.main` (0 success, 2 usage or input error, 3 run failure; `singvst-train: <command>: <message>`
on stderr). Paths are absolute or relative to the working directory.
| Command | Options | Effect |
|---|---|---|
| `split` | `--files-dir D --seed N [--fraction 0.1] --out F` | as the `build_parser` docstring |
| `prepare` | `--in D --out D [--sr 48000] [--threshold-db -40] [--min-sec 2] [--max-sec 15] [--dereverb] [--lockfile F]` | for each `*.wav` in `--in` (sorted): read with soundfile, average channels, resample to `--sr` (`scipy.signal.resample_poly`), `slice_on_silence`, `normalise` each slice, write `OUT/segments/<stem>_<k:03d>.wav` (PCM_16; `k` 0-based, in the order `slice_on_silence` returns the slices), then `build_dataset_manifest(OUT, segments, params)` with segment `file` = `segments/<stem>_<k:03d>.wav`, `source` = the input file name, `start`/`end` = sample indices of the resampled signal, `params` = the CLI options as a dict, and a provenance sidecar for `OUT/dataset.json` (`params` the same dict, `seeds` `{}`, `lockfile` = `--lockfile`, default the repository's `python/requirements-lock.txt`); `--dereverb` first runs `prepare.dereverb(IN, OUT/dry)` and uses `OUT/dry`; no input audio → exit 2 |
| `rvc-files` | `--exp-dir D --rvc-root D [--sr-tag 48k] [--speaker-id 0] [--seed 0]` | `write_filelist` + `copy_config`; prints both paths |
| `rvc-train-command` | `--exp-name S [--sr-tag 48k] [--batch-size 8] [--epochs 200] [--save-every 10] [--gpus 0] [--python PY]` | prints `train_command(...)` as one JSON list (`--python` default `sys.executable`) |
| `export` | `--rvc-root D (--weights F \| --exp-name S) --out-dir D` | `export_synth` → `OUT/rvc_synth.onnx`, `export_content` → `OUT/content.onnx`; `--exp-name` uses `latest_weights` |
| `make-test-weights` | `--rvc-root D --out F [--seed 0]` | `make_test_weights` |
| `pack` | `--out D --name S --consent S --guide-licence S --acoustic F --vocoder F --phonemes F [--speaker F] [--languages F] [--synth F --content F] [--language en] [--steps 20] [--depth 0.4] [--converter-sample-rate 48000] [--speaker-id 0]` | `pack_voice` (`--synth`/`--content` together or not at all) |
| `evaluate` | `--voice D --heldout D --phrases D --render-bin F --out D [--seed 0] [--thresholds eval/thresholds.json] [--lockfile F]` | `evaluate_voice` (`lockfile` = `--lockfile`; held-out files = the sorted `*.wav` directly in `--heldout`; a `ValueError` from
a metric or a failed render makes the report "invalid: <reason>" with `null` metrics instead of propagating), then writes
`OUT/verdict.json` = `metrics.judge(report, thresholds)` for a measured report, or `{"all": false, "status": <the report's
status>}` for an invalid one (judge is not called); exit 0 whenever `report.json` was written, 3 otherwise; the report's provenance `params` = `{"voice_name": <manifest name>, "voice_sha256", "phrases": <dir>, "heldout_files": <count>}`, `seeds` = `{"converter": <seed>}` (eval/PROCEDURE.md) |
| `provenance` | `--result F --params JSON --seeds JSON [--repo .] [--lockfile python/requirements-lock.txt]` | `collect` + `write_sidecar` |

**Notebook environment.** Every Python command of the notebook runs in a uv-managed Python 3.12 venv, whatever the runtime's
Python (C-060): `pip install uv==0.13.1`; `uv venv --python 3.12 --python-preference only-managed $VENV`;
`os.environ["PATH"] = f"{VENV}/bin:" + os.environ["PATH"]`, so every later `!python …` — spelled exactly
`python -m singvst_train.cli <cmd>` for toolkit calls (T-P17) — and RVC's scripts run in the venv. Installs, all with
`uv pip install --python $VENV/bin/python`, in this order (R-020: each package name comes from exactly one index):
(i) `--index-url https://download.pytorch.org/whl/cu128 torch==2.7.1+cu128 torchaudio==2.7.1+cu128` — RVC's cu128 file
does **not** list torch; its header comment prescribes this pair as a separate first stage (C-062); (ii) `--index-url
https://pypi.org/simple -r rvc-req.txt`, where `rvc-req.txt` is RVC's `requirments_cu128_py312.txt` without its index lines
(`grep -vE -- '--(extra-)?index-url'`); (iii) `uv pip uninstall onnxruntime-gpu onnxruntime` (RVC's file pins
onnxruntime-gpu < 1.20, which provides the same `onnxruntime` package; C-023); (iv) from PyPI: `onnx==1.23.2
onnxruntime==1.31.0 pyworld==0.3.5 mido==1.3.3 pytest==9.1.1 nbformat==5.10.4 PyYAML==6.0.3 openai-whisper==20250625
webrtcvad-wheels==2.0.14` (+ `audio-separator==0.47.0` only when `DEREVERB`), then `resemblyzer==0.1.4 --no-deps` (its
`webrtcvad` dependency imports `pkg_resources` unconditionally; `webrtcvad-wheels` provides the same module through
`importlib.metadata`, and librosa, numpy, scipy and torch are already installed; C-062); (v) the toolkit with
`-e <sing-vst>/python --no-deps`. Every session (step (4e), after the Colab mount) writes `uv pip freeze --python
$VENV/bin/python` to `<run>/out/env/<session>.freeze.txt` and `<run>/out/env/<session>.json` = `{"python", "torch",
"cuda", "gpu", "driver", "image"}` (`<session>` = the session's UTC start, `YYYYmmddTHHMMSSZ`; files of earlier
sessions are kept, R-054; `--lockfile` arguments name the current session's freeze file) (`torch.__version__`,
`torch.version.cuda`, `torch.cuda.get_device_name(0)`, `nvidia-smi --query-gpu=driver_version`, the platform name)
(R-019). `ffmpeg` must be on PATH for Whisper (C-059): `which ffmpeg || apt-get install -y ffmpeg`. The Colab Drive is
mounted **after** these installs (R-020), at step (4d).
**Paths.** Colab: `<root>` = `/content/drive/MyDrive/singvst/<VOICE>`, `<rvc>` = `/content/rvc`, `<sing-vst>` =
`/content/sing-vst`, `VENV` = `/content/py312`, recordings in `<root>/raw/`. Kaggle: `<root>` = `/kaggle/working`, `<rvc>` =
`/tmp/rvc`, `<sing-vst>` = `/tmp/sing-vst`, `VENV` = `/tmp/py312`, recordings in the input dataset
`/kaggle/input/singvst-<VOICE>/` (read-only; `raw/` below means that folder). `<LOCAL>` = `/content/local` (Colab) or
`/tmp/local` (Kaggle): local disk for the build tree and the binary — no executable or build tree is ever placed on Drive
(R-052). **Runs** (R-013, R-014, R-015, R-053): the first G-004 issue and each G-001 `retrain` start a new run number `RUN`
(1, 2, …); a `failed:` re-issue keeps `RUN` and its experiment and changes only `EXPECTED_COMMIT`. Each run has its own run root `<run>` = `<root>/run<RUN>/`, holding `params.json`, `state/`,
`raw_wav/`, `split.json`, `train/`, `heldout/`, `prepared/` and `out/`; the RVC experiment name is `<exp>` =
`<VOICE>-run<RUN>`, and `pack --name <exp>`. Nothing of one run is read, overwritten or deleted by another; earlier runs'
voice packages stay where they are. `<rvc>` and `<sing-vst>` are re-cloned every session; the RVC experiment and weights
live on persistent storage: `<rvc>/logs/<exp>` and `<rvc>/assets/weights` are symlinks to `<root>/logs/<exp>` and
`<root>/weights` (this rule wins over D-016's "single tar archives" for the experiment; R-033). Stage-table paths starting
`logs/` or `assets/` are under `<rvc>`; all other relative paths are under `<run>`. RVC commands (cells (9), (11)) run with
cwd `<rvc>`; every other command runs with cwd `<run>`.
**Owner-edited cells:** (2) consent and (2a) parameters only; GATE-G-004.md states what to enter. In (2) the owner sets
`CONSENT_CONFIRMED = True` and `ATTESTATION` = "I confirm these recordings are my own voice, or are used with the
singer's consent, and that this use is within the platform's terms." (A-011). **Parameters cell** (2a): `VOICE = "myvoice"`
(lower-case letters, digits and `-`), `RUN = 1`, `EXPECTED_COMMIT = "<40-hex commit named in GATE-G-004.md>"`,
`RESUME = False` (Kaggle: False for the voice's first version, True for every later one; R-068),
`DEREVERB = False`, `EPOCHS = 200` (a multiple of 10, asserted in (2a); `train_command` requires `--save-every` 10 to divide
it), `SPEAKER_ID = 0`, `GUIDE = "tiger"` (or the G-005 alternative). At the end of cell (4) — after the Colab mount, so
nothing is written under the Drive path before it is mounted — the first session of a
run writes `<run>/params.json` = these values except `EXPECTED_COMMIT` (each session's commit goes to
`budget.json` `sessions[].commit`); every later session asserts its values equal the file's, else stops with
"parameters changed within run <RUN>: set RUN = <RUN+1> for a new run" (R-013). `params.json` is an input of every stage.
`--consent` = the attestation text; `--guide-licence` = the D-035 §Guide voicebank string. **Memory and disk check**
(cell (10a), PK-43): print GPU name, GPU memory, RAM and free space on `<root>`'s file system; batch size 8 when GPU memory ≥
14 GiB, else 4; RAM < 10 GiB → stop with a message to choose a High-RAM runtime; free space < 3 × the size of `raw/` +
8 GiB (features, G/D checkpoints and their `.bak`, 20 weight snapshots; on Kaggle twice that, because `state.tar` is written
beside its inputs) → stop with a message to free Drive space,
naming earlier runs' `logs/<exp>/` as the largest deletable items (R-033, R-063).
**GPU time** = the wall-clock time of the stages rvc-f0, rvc-features, train, export and evaluate, plus cell (16); each
session also records `session_hours` = wall-clock from cell (1) to its end, which is what platform quotas charge (R-062).
**Kernel and helpers** (shared by all cells; names fixed): the notebook kernel (not the venv) runs the orchestration; after
step (4a) it does `sys.path.insert(0, f"{SINGVST}/python")` and imports `pipeline` lazily inside `make_stages` and later
cells (`pipeline.py` is standard-library only). Globals: `PLATFORM` ("colab"|"kaggle"), `ROOT`, `RUNDIR`, `LOCAL`, `RVC`,
`SINGVST`, `VENV`, `SESSION`, `STOP`, `HEARTBEAT`, `HEARTBEAT_ERROR`, and `class SessionEnd(Exception)`; cell (3) derives
every path from `PATH_ROOTS = globals().get("PATH_ROOTS", {"content": "/content", "kaggle": "/kaggle", "tmp": "/tmp"})`,
so the S-016 dry run remaps them by pre-setting `PATH_ROOTS`. `sh(cmd, cwd, timeout=None) -> (rc, output)` runs `bash -c
cmd` in `cwd` in a new process group (`start_new_session=True`) with `VENV/bin` first on PATH, streams and captures
stdout+stderr, and on timeout sends SIGTERM to the whole group (RVC's `train.py` trains in `multiprocessing` child
processes, C-065), then SIGKILL to the group after 60 s, returning rc 124; after a train-stage timeout the notebook
checks `nvidia-smi --query-compute-apps=pid --format=csv,noheader` is empty before anything else runs, else SIGKILLs those
PIDs and re-checks (R-070); venv-side Python checks (the checkpoint guard's `torch.load`) run
through `sh` and print their result. A non-train stage whose command returns rc ≠ 0 raises `RuntimeError` (command and
last 50 output lines). **Train-stage outcomes:** `train.py` exits 0 and `<exp>.pth` exists → complete; the stage timeout
is computed by the main thread's exact counters as `t = min(t_session, t_budget)` with `t_session` = 10 h − elapsed −
0.5 h and `t_budget` = 20 h − 1 h − the voice's `gpu_hours` (1 h reserved for export, evaluate and T-P20; R-075). When
`t_budget` is the smaller term and ≤ 0, or binds and `sh` returns 124 → DR-13 copy of `latest_weights` → complete; when
`t_session` binds and is ≤ 0 or `sh` returns 124 → `STOP = True` and `raise SessionEnd` (no marker; the next session
resumes); checkpoint guard or restart detection fails, or any other rc ≠ 0 → `RuntimeError` (a real failure, reported
as `failed:`). On restart detection the notebook first copies `G_2333333.pth.bak`/`D_2333333.pth.bak` (still at `e0`)
back over the restarted files and writes `logs/<exp>/RESTART_DETECTED`; while that file exists the guard never
overwrites a `.bak` (R-076). `.bak` files are named `<file>.pth.bak`, which RVC's `G_*.pth` glob does not match. Every cell that calls `run_stages` catches `SessionEnd` only,
printing "start a new session". The 9.5-h check before each stage also raises `SessionEnd`.
**Guarded cells** (R-069): from cell (5) through (16), each cell's body runs inside `guarded(<cell number>, body)`, which does
nothing when `STOP` is set and otherwise catches every exception: `SessionEnd` → `STOP_REASON` = "start a new
session"; any other exception (including every "stop" this decision names after cell (4)) → its traceback is printed,
`STOP = True` and `STOP_REASON` = `failed: <cell number> <first line of the error>` — the line the owner pastes as the G-004
response. So no cell from (5) on raises and every version reaches cell (17), which is not guarded: it runs its `STOP` or normal
branch inside its own `try`/`finally`, whose `finally` always stops the heartbeat, writes the budget files and (Kaggle)
runs `pack_state`. Cells (1)–(4)
may raise: nothing has been written yet.
**Ending a session** (R-055): a stop condition (9.5 h, train timeout, or a guarded failure) sets `STOP = True`; every later cell
starts with `if STOP:` printing "skipped — start a new session", so a Kaggle version always completes without an error
and keeps its output (outputs are limited to 500 items, C-064 — hence `state.tar`). This applies on both platforms; with
`STOP` set, cell (17) only stops the heartbeat, writes `budget.json` and `budget-voice.json` a final time, (Kaggle) writes
`state.tar`, and prints `STOP_REASON` — no upload tar.
Kaggle's weekly quota cannot be read from code: the notebook prints a reminder to check it in Kaggle's settings before the
train stage.
**Notebook layout** (Colab: Google Drive folder `MyDrive/singvst/<VOICE>/`; Kaggle: input dataset `singvst-<VOICE>` and the
notebook's `/kaggle/working` output): `raw/` the owner's recordings (WAV or FLAC; the split stage first writes every one as
WAV to `raw_wav/<stem>.wav` with soundfile, same sample rate, subtype PCM_24), `<run>/state/` stage markers
(`pipeline.run_stages`), `logs/<exp>/` the RVC experiment (kept for resume, C-047), `<run>/out/` exports, voice package and
evaluation. Cells, in order (19 code cells): (1) `!nvidia-smi` (Kaggle: also the visibility reminder);
(2) consent (`CONSENT_CONFIRMED = False`, `ATTESTATION = ""`, then `assert CONSENT_CONFIRMED and ATTESTATION`); (2a) the
Parameters cell; (3) set paths and define `make_stages(run, rvc, sh)` (the cell containing `def make_stages`; it returns
the eleven `pipeline.Stage` objects of the stage table, each stage's `run` calling `sh(<command>)`, using the globals
`VOICE`, `RUN`, `EPOCHS`, `DEREVERB`, `SPEAKER_ID`, `GUIDE`; cells (7)–(15) call `run_stages` on its slices); cell (3) also defines `pack_state(dst_dir)` and `restore_state(src_dir)` (used by cells (3) and (17) and by the S-016 dry
run, R-079). Kaggle only: restore the previous session (R-016, R-055, R-068) — `prev =
glob("/kaggle/input/*/state.tar")`; the Parameters cell's `RESUME` (False for the very first Kaggle version of this voice,
True for every later one; GATE-G-004.md says so) decides: `RESUME` and no match → raise "attach the previous version's
output (Add Input → Your Work)"; not `RESUME` and a match → raise "set RESUME = True"; more than one match → raise naming
them; one → its `state.tar.sha256` must match, then `restore_state` extracts it with `tarfile` `filter="data"` into
`/kaggle/working` (it holds every `run*/`, `logs/`, `weights/`, `assets-archive/`, `budget-voice.json`) and the session
records the restored tar's SHA-256 as `restored_from` in its `sessions[]` entry; (4) in exactly this order (R-051): (a) clone sing-vst and check out `EXPECTED_COMMIT` (`git rev-parse HEAD` must equal
it, else stop; R-029) and RVC 81eed5e; (b) create the venv and install exactly as §Notebook environment; (c) the GPU's
compute capability must be in `torch.cuda.get_arch_list()`, else stop naming both (R-044); (d) Colab only:
`drive.mount('/content/drive')` — no cell writes under `/content/drive` before this point; (e) create the `<run>/`
directories and the RVC symlinks, write or check `<run>/params.json` (above), write this session's freeze and env files,
append this session to `budget.json` `sessions[]` (with its commit) and start the budget heartbeat (§Time and budget);
(f) build `singvst-render` on local disk, never on Drive (R-052): `g++ --version`; `cmake -S <sing-vst> -B
<LOCAL>/build-render -DCMAKE_BUILD_TYPE=Release -DSINGVST_BUILD_PLUGIN=OFF -DSINGVST_BUILD_TESTS=OFF && cmake --build
<LOCAL>/build-render --target singvst-render --parallel 4` (C-055), then run `<LOCAL>/build-render/cli/singvst-render
--check-voice <sing-vst>/tests/fixtures/voice-convert`, which must print `ok …` — a failure stops the run before GPU time
is spent (R-023);
(5) RVC assets with `hf download` exactly as C-052 but with `--revision <the SHA recorded in plan/ENVIRONMENT.md by S-013>`
(hubert_base, rmvpe.pt, pretrained_v2, mute.zip → `logs/`) in a separate venv for huggingface_hub 2.2.0 (C-054), taken from
`<root>/assets-archive/` when present there with matching SHA-256, else downloaded and then copied there with their SHA-256
(R-042); (6) checks before any GPU stage: `SINGVST_RVC_ROOT=<rvc> python -m pytest -q -m torch` (T-P19) from the sing-vst
checkout, and `python -c "import resemblyzer, whisper; whisper.load_model('small.en')"` (R-022; the Whisper weights are
archived like (5)) — stop if either fails; (7) the split stage: write `raw_wav/`, `python -m singvst_train.cli split
--files-dir raw_wav --seed 0 --out split.json`, then copy each name of `split.json` `train` into `train/` and of `heldout`
into `heldout/`; stop before training when `heldout/` is empty or holds < 30 s, or `train/` holds < 10 min, with a message to
supply at least 10 recordings (R-031); (8) `prepare --in train --out prepared --lockfile out/env/<session>.freeze.txt`; (9) in the RVC
checkout: `python train/preprocess.py <run>/prepared/segments 48000 <n_cpu = os.cpu_count()> <rvc>/logs/<exp> False 3.0`;
`python train/dataset/extract_f0.py cuda 1 0 0 <rvc>/logs/<exp> False`; `python train/dataset/extract_hubert_feature.py
cuda 1 0 0 <rvc>/logs/<exp> v2 False` (full precision, RVC's fp32 path, works on every GPU type; rmvpe is RVC's fixed f0
method in cuda mode; argv verified in C-057); (10) `rvc-files`; (10a) the Memory and disk check; (11) the train stage:
**checkpoint guard** (R-035, R-057) — when `logs/<exp>/G_2333333.pth` or `D_2333333.pth` exists, each must load with
`torch.load(path, map_location="cpu")` (exactly as RVC loads it, C-063) and `e0` = the G checkpoint's `"iteration"`; a file that fails is replaced by its `.bak` when that loads,
else the cell stops ("checkpoint unreadable; delete logs/<exp> to restart this run"); after the check both are copied to
`.bak`; then run the JSON argv printed by `rvc-train-command` (RVC resumes from `logs/<exp>` automatically, C-047, C-061;
no retrieval index is trained — the converter does not use it, D-012); after it exits, in a session that started with a
checkpoint: the G checkpoint's `"iteration"` must be ≥ `e0` (a restart from the pretrained model saves lower epochs),
and the `logs/<exp>/train.log` lines written in this session must contain neither RVC's pretrained-fallback message
"已加载生成器预训练模型" nor its en_US translation "Loaded generator pretrained model" (RVC logs through `i18n`, C-063);
else stop ("training restarted from the pretrained model"); **completion**: the stage is
complete when `assets/weights/<exp>.pth` exists (RVC writes it at `total_epoch` and exits, C-061); (12) `export --exp-name
<exp>`, then `python -c` calling `export_rvc.parity(<rvc>, assets/weights/<exp>.pth, out/conv/rvc_synth.onnx)` — above
1e-3 → stop (DR-14, R-050); (13) the render-bin stage: `mkdir -p <LOCAL>/bin && cp <LOCAL>/build-render/cli/singvst-render
<LOCAL>/build-render/cli/cmudict.dict <LOCAL>/build-render/cli/onnxruntime-LICENSE.txt
<LOCAL>/build-render/cli/libonnxruntime.so* <LOCAL>/bin/` (the build copies the runtime files beside the binary; D-024,
D-005; `<LOCAL>` is rebuilt every session, so a resumed session re-runs render-bin and, because the binary's bytes differ,
evaluate); (14) the guide voicebank (§Guide voicebank,
into `<root>/voicebank/`, the zip archived like (5)) and `python -m singvst_train.cli pack --out out/voice --name <exp> …`,
then `out/training.json` = `{"voice_name": <exp>, "epochs_requested": EPOCHS, "epochs_trained": <N of the newest
<exp>_e<N>_s<M>.pth, or EPOCHS>, "stopped_by_budget": <bool>, "weights_sha256", "env_files": [the session freeze/env files], "stage_commits":
{stage: commit it last ran under}, "commit"}` (R-019, R-054; `make_stages` records `stage_commits` in
`<run>/state/commits.json` whenever a stage runs);
(15) `python -m singvst_train.cli evaluate --voice out/voice --heldout heldout --phrases <sing-vst>/eval/phrases
--render-bin <LOCAL>/bin/singvst-render --out out/eval --thresholds <sing-vst>/eval/thresholds.json --lockfile
out/env/<session>.freeze.txt`; then `out/eval/ceiling.json` = `{"heldout_vs_train": mean over held-out files of cosine(embedding of
the file, mean embedding of the `train/` files)}` with the PROCEDURE step 4 Resemblyzer settings (R-032); (16) `python -m pytest -q -m
voice --junitxml=out/eval/t-p20.xml` (T-P20) with `SINGVST_VOICE`, `SINGVST_HELDOUT`, `SINGVST_RENDER_BIN` set to the
paths above; a non-zero exit is a guarded failure (`failed: 16 …`), so no upload tar is written for a failing T-P20 (R-071); (17) stop the budget
heartbeat and write `budget.json` a final time; `tar` the `out/` folder to `<root>/out-run<RUN>.tar` (Drive / Kaggle output); write
`<root>/upload-run<RUN>.tar` holding the upload files (§Upload) and print its `sha256sum` line (R-036, R-056); Kaggle: then
`pack_state` writes `/kaggle/working/state.tar` (+ `state.tar.sha256`, also recorded as `state_tar_sha256` in the session's
`sessions[]` entry) of every `run*/`, `logs/`, `weights/`, `assets-archive/` and `budget-voice.json`, deletes those
untarred copies and `voicebank/` (re-extracted from `assets-archive/` each session), and asserts `/kaggle/working` holds
at most 20 items (R-055, R-073).
Every stage from (7) runs through `pipeline.run_stages` with markers in `<run>/state/` and these inputs → outputs; every
stage also has `params.json` as an input (R-013); the notebook prints the list `run_stages` returns and appends it to
`budget.json` `sessions[].stages_run` (the RVC experiment directory `logs/<exp>/` and its `G_*.pth`/`D_*.pth` checkpoints are
**never** a stage output, so a rerun never deletes them; C-047):
| Stage | Inputs | Outputs |
|---|---|---|
| split | `raw/` | `raw_wav/`, `split.json`, `train/`, `heldout/` |
| prepare | `train/` | `prepared/` |
| rvc-preprocess | `prepared/segments` | `logs/<exp>/0_gt_wavs`, `logs/<exp>/1_16k_wavs` |
| rvc-f0 | `logs/<exp>/1_16k_wavs` | `logs/<exp>/2a_f0`, `logs/<exp>/2b-f0nsf` |
| rvc-features | `logs/<exp>/1_16k_wavs` | `logs/<exp>/3_feature768` |
| rvc-files | `logs/<exp>/0_gt_wavs`, `…/3_feature768`, `…/2a_f0`, `…/2b-f0nsf` | `logs/<exp>/filelist.txt`, `logs/<exp>/config.json` |
| train | `logs/<exp>/filelist.txt`, `logs/<exp>/config.json` | `assets/weights/<exp>.pth` |
| export | `assets/weights/<exp>.pth` | `out/conv/` |
| render-bin | `<LOCAL>/build-render/cli/singvst-render` | `<LOCAL>/bin/` |
| pack | `out/conv/`, `<root>/voicebank/` | `out/voice/`, `out/training.json` |
| evaluate | `out/voice/`, `heldout/`, `<LOCAL>/bin/` | `out/eval/` |
**Time and budget.** `out/budget.json` holds `{"gpu_hours", "sessions": [{"commit", "start", "end", "gpu_hours",
"session_hours", "stages_run"}]}`, and `<root>/budget-voice.json` holds `{"gpu_hours", "runs": {RUN: gpu_hours}}` summed
over every run of the voice (A-015 is per voice; R-062). A background thread started at step (4e) — a module-level singleton: (4e) stops and joins any heartbeat left from an
earlier run of the cells in the same runtime before starting a new one, and each write re-reads the files and updates only
its own `<session>` entry (R-074) — rewrites both with
`pipeline.atomic_write_text` every 5 minutes with the running session's GPU time, so a killed session loses at most 5
minutes of accounting; `gpu_hours` is therefore a lower bound and GATE-G-001.md says so (R-034). The thread stores any
exception instead of dying silently; before every stage and in cell (17) the notebook checks the thread is alive and has
stored no exception, else stops naming it (R-051). Before each stage the notebook prints the session's elapsed time, the
cumulative `gpu_hours` and (Kaggle) the reminder to check the weekly quota, and stops with "start a new session" when the
session has run ≥ 9.5 h. The train stage runs `train.py` with the timeout of §Kernel and helpers (session term, budget term with 1 h reserved);
on timeout the next session resumes it (C-047; the checkpoint guard covers a save cut by the timeout). When the budget term binds (A-015) the train stage copies the newest `assets/weights/<exp>_e<N>_s<M>.pth` (`latest_weights`) to
`assets/weights/<exp>.pth`, records `"stopped_by_budget": <N>` in `budget.json` and completes (DR-13). **Epochs:**
`--epochs` = `EPOCHS` (200 unless GATE-G-004.md states another value); the owner reports the value used in the G-004
response; `--save-every` 10.
**Upload to the implementer (G-004):** `upload-run<RUN>.tar` holding `report.json`, `report.json.provenance.json`,
`verdict.json`, `spread.json`, `ceiling.json`, `budget.json`, `budget-voice.json`, `training.json`, `state/commits.json`
(the final stage→commit table, R-054), `out/eval/t-p20.xml` (R-071) and `out/env/` (every session's freeze and env file), attached to the conversation, plus the `sha256sum` line cell (17) printed (the only part
that may be pasted as text; R-056).
Renders and voice packages stay on the owner's Drive or machine (A-011, T-062).
**Visibility (R-021):** the Kaggle dataset `singvst-<VOICE>` and the Kaggle notebook are **Private** and no version is
published; the Drive folder is not shared. Cell (1) of the Kaggle notebook prints this reminder; GATE-G-004.md requires it.

**Guide voicebank** (when G-005 answers `use-tiger`): the owner downloads
`https://github.com/spicytigermeat/tiger_diffsinger/releases/download/v102/TIGER_DS_v102_PACK.zip` inside the notebook,
checks SHA-256 `925ca2ad44287757d26628608b2744381e75748042d0e6fae356ee8cdae19f4e`, unzips it to `<root>/voicebank/pack/`, then unzips
`<root>/voicebank/pack/Voice Library/TIGER_DS_v102.zip` to `<root>/voicebank/tiger/`. Roles (relative to `voicebank/tiger/`): `acoustic` = `dsacoustic/tiger_acou.onnx`, `phonemes` = `dsacoustic/phonemes.txt`,
`speaker` = `dsacoustic/tiger_fresh.emb`, `vocoder` = `dsvocoder/tgm_hifigan.onnx` (research/spikes/tiger-guide). `steps` 20;
`depth` = `min(0.4, max_depth)` where `max_depth` is read from `dsacoustic/dsconfig.yaml` (divided by 1000 when it is > 1,
the legacy integer convention; C-034), 0.4 when the key is absent — the caller clamps, `pack_voice` does not (errata E-3).
`guide_licence` = "TIGER DiffSinger v102, CC BY-NC-ND 4.0 + Commons Clause, personal non-commercial use (C-037)".

### D-038 Pre-mortem round 1 hardening (premortem/round-1.md)
**Take cache** (R-017; `core/include/singvst/take_cache.hpp`, T-067, T-068). File `<16 lower-case hex digits of
contentHash>.take`, little-endian: `"SVTAKE01"` (8 bytes), `contentHash` u64, `startBeat` f64, `bpm` f64, `sampleRate` i32,
`unclippedPeak` f32, sample count `n` u64 (48-byte header), `n` × f32 samples, then FNV-1a-64 (D-009 constants) of all
preceding bytes (u64): size = 56 + 4n. `storeTake` writes `<name>.tmp` then renames; `loadTake` checks the size before
allocating, then magic, stored hash = requested hash, `sampleRate` > 0, `n` ≤ 901 × `sampleRate` (900 s plus frame-rounding slack, R-067), and the checksum; any
failure is a miss. `cachedRender` keys by `phraseHash(request)` and stores only a take whose `contentHash` equals it.
Implemented by S-009 (planning sketch: research/spikes/premortem-r1/take_cache_sketch.cpp passes T-067/T-068).
**resampleTake** (R-072; T-071): playback copy at another rate, from the original take only (D-010).
**Limits** (R-027): 5000 notes and 900 s per take, in `importMidi` (D-031, T-069, S-006) and `renderTake` (D-013, T-070,
S-009); external-data ONNX models rejected at engine load (D-012, S-008).
**Index of round-1 mitigations:** R-013/R-014/R-015/R-016/R-019/R-020/R-021/R-022/R-023/R-029/R-031/R-033/R-034/R-035/
R-042/R-044/R-050 → D-035 (notebook); R-017 → D-010, D-012, take cache; R-018/R-032 → D-017, eval/PROCEDURE.md,
`evaluate.REPEATS`; R-024/R-026/R-045 → D-022, D-002; R-025 → D-012, D-013; R-027 → limits; R-030/R-036/R-037 →
plan/GATES.md and S-017; R-038 → S-019 and research/PRIOR_KNOWLEDGE.md; R-039/R-040 → ci.yml, tools/ci_annotate.py;
R-041 → S-018 README; R-046 → D-031; R-047 → D-014; R-048 → D-027. R-028 (Medium) and R-043 (Low) stay open with the
partial controls listed in premortem/RISK_REGISTER.md.

### D-036 CI waiting, attempts and local loops
CI runs are read with `gh api "repos/qualitycoding/sing-vst/actions/runs?branch=<impl>&head_sha=<sha>&per_page=5"` (quoted;
the run for the commit just pushed). Poll every 5 minutes, at most 90 minutes; a run cancelled by a newer push is replaced by
the newer push's run; a run cancelled or failed for infrastructure reasons (runner lost, network) is re-run once with
`gh run rerun <id>`. A test **passes in CI** when its job step concluded `success`, or — for a step that runs several tests —
the step's `test-summary` notice annotation (written by `tools/ci_annotate.py` on every run, `if: always()`) lists its ID
under `passed:`. Missing summary notice → the run is unreadable: re-run once, then `BLOCKED.md`. The per-case `::error::`
annotations are diagnostics only (GitHub caps their number per step). If `gh run rerun` is refused (permission), trigger a
new run instead by appending a row to `EXECUTION_LOG.md` and saving (a new commit). One **attempt** for a CI-only test (T-059, T-P19, the
Windows parts of T-041…T-047; and, on the no-root path of S-000 action 3, T-034 and T-053…T-059) is one CI run of a new commit. No torch is installed locally (download.pytorch.org is
unreachable from the workspace; C-044); RVC is cloned locally to `../rvc` at 81eed5e for reading only.

### D-037 Errata for frozen comments
Frozen files cannot be edited, so comments that are wrong are corrected here and win over the comment:
- E-1 `core/include/singvst/params.hpp`: "T-049 checks the plugin exposes exactly these" → the test is **T-053**.
- E-2 `plugin/PluginProcessor.h`: `publishTakeForTesting` is used by **T-055** (not T-050/T-051).
- E-3 `core/include/singvst/voice.hpp` `GuideSpec::depth`: "clamped … by the packer" → the **caller of `pack`** clamps
  (D-035 §Guide voicebank); `pack_voice` validates (0, 1] only. The struct default 1.0 is never used: `depth` is required.
- E-4 test docstrings name sub-tests by function (`test_P13b_…`, `test_P19b_…`); they are parts of **T-P13** and **T-P19**.
- E-5 `tests/python/test_evaluate.py` T-P26 docstring "toward the training data's median pitch" → the **held-out**
  recordings' median F0 (D-017, eval/PROCEDURE.md).
- E-7 `core/include/singvst/synthesis.hpp` `f0Curve`: "i in [0, ceil(totalSec * frameRateHz))" → `ceil(total·fr − 1e-9)`
  frames (D-007, T-024).
- E-8 `core/include/singvst/g2p.hpp` `hasPhone`: "occurs in any entry" → in any **kept** entry (the first entry of a word;
  ignored duplicate lines do not count; D-005, T-007).
- E-6 `tests/cpp/test_playback.cpp` T-034 comment "CI installs de_DE.UTF-8 (D-018)" — true from this amendment on (D-018).

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
- DR-08 The report's `realtime_factor` (measured by `evaluate` in the notebook) or the owner's RTF at G-001 exceeds 3 (C-039
  measured 1.10 on 2 sandbox threads) → record both; changing `steps`/`depth` is a G-001 `retrain` response, never the implementer's choice.
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
