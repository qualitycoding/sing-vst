"""Command-line entry point used by the training notebooks (D-016): ``python -m singvst_train.cli <command>``.
Stub until plan step S-012 (commands are added by S-012..S-015)."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

COMMANDS = ("prepare", "split", "rvc-files", "rvc-train-command", "export", "make-test-weights", "pack", "evaluate",
            "provenance")


_HELP = {
    "prepare": "slice and normalise recordings into a training dataset",
    "split": "write the held-out split of a folder of recordings",
    "rvc-files": "write RVC's filelist and config for an experiment",
    "rvc-train-command": "print the RVC training command",
    "export": "export an RVC model to ONNX",
    "make-test-weights": "write small random RVC weights for tests",
    "pack": "write a voice package",
    "evaluate": "evaluate a voice package",
    "provenance": "write a provenance sidecar for a result file",
}


def _repo_root() -> Path:
    import singvst_train
    return Path(singvst_train.__file__).resolve().parents[2]


def _cmd_split(args) -> int:
    from singvst_train.pipeline import atomic_write_text
    from singvst_train.prepare import split_heldout
    names = sorted(p.name for p in args.files_dir.iterdir() if p.is_file() and p.suffix == ".wav")
    if not names:
        raise ValueError(f"no .wav files in {args.files_dir}")
    train, heldout = split_heldout(names, args.seed, args.fraction)
    atomic_write_text(args.out, json.dumps({"train": train, "heldout": heldout}, indent=1) + "\n")
    return 0


def _cmd_prepare(args) -> int:
    from math import gcd

    import numpy as np
    import soundfile as sf
    from scipy.signal import resample_poly

    from singvst_train import prepare, provenance

    params = {"in": str(args.in_dir), "out": str(args.out), "sr": args.sr, "threshold_db": args.threshold_db,
              "min_sec": args.min_sec, "max_sec": args.max_sec, "dereverb": bool(args.dereverb)}
    source_dir = args.in_dir
    if args.dereverb:
        prepare.dereverb(args.in_dir, args.out / "dry")
        source_dir = args.out / "dry"
    wavs = sorted(source_dir.glob("*.wav")) if source_dir.is_dir() else []
    if not wavs:
        raise ValueError(f"no .wav files in {source_dir}")
    seg_dir = args.out / "segments"
    seg_dir.mkdir(parents=True, exist_ok=True)
    segments = []
    for wav in wavs:
        data, rate = sf.read(str(wav), dtype="float64", always_2d=True)
        mono = data.mean(axis=1)
        if rate != args.sr:
            g = gcd(rate, args.sr)
            mono = resample_poly(mono, args.sr // g, rate // g)
        mono = mono.astype(np.float32)
        for k, (start, end) in enumerate(prepare.slice_on_silence(mono, args.sr, args.threshold_db, args.min_sec, args.max_sec)):
            rel = f"segments/{wav.stem}_{k:03d}.wav"
            sf.write(str(args.out / rel), prepare.normalise(mono[start:end]), args.sr, subtype="PCM_16")
            segments.append({"file": rel, "source": wav.name, "start": int(start), "end": int(end)})
    prepare.build_dataset_manifest(args.out, segments, params)
    lock = args.lockfile or _repo_root() / "python" / "requirements-lock.txt"
    record = provenance.collect(params, {}, _repo_root(), lock)
    provenance.write_sidecar(args.out / "dataset.json", record)
    print(f"{len(segments)} segments from {len(wavs)} recording(s) in {args.out / 'segments'}")
    return 0


def _cmd_pack(args) -> int:
    from singvst_train.pack import pack_voice
    if (args.synth is None) != (args.content is None):
        raise ValueError("--synth and --content go together or not at all")
    guide = {r: getattr(args, r) for r in ("acoustic", "vocoder", "phonemes", "speaker", "languages") if getattr(args, r) is not None}
    converter = None if args.synth is None else {"synth": args.synth, "content": args.content}
    pack_voice(args.out, args.name, args.consent, args.guide_licence, guide, converter, language=args.language,
               steps=args.steps, depth=args.depth, converter_sample_rate=args.converter_sample_rate, speaker_id=args.speaker_id)
    print(args.out / "manifest.json")
    return 0


def _cmd_rvc_files(args) -> int:
    from singvst_train import rvc_files
    print(rvc_files.write_filelist(args.exp_dir, args.rvc_root, args.speaker_id, args.sr_tag, args.seed))
    print(rvc_files.copy_config(args.exp_dir, args.rvc_root, args.sr_tag))
    return 0


def _cmd_rvc_train_command(args) -> int:
    from singvst_train import rvc_files
    command = rvc_files.train_command(args.python or sys.executable, args.exp_name, args.sr_tag, args.batch_size, args.epochs,
                                      args.save_every, args.gpus)
    print(json.dumps(command))
    return 0


def _cmd_export(args) -> int:
    from singvst_train import export_rvc
    weights = args.weights
    if weights is None:
        from singvst_train import rvc_files
        weights = rvc_files.latest_weights(args.rvc_root, args.exp_name)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    print(export_rvc.export_synth(args.rvc_root, weights, args.out_dir / "rvc_synth.onnx"))
    print(export_rvc.export_content(args.rvc_root, args.out_dir / "content.onnx"))
    return 0


def _cmd_make_test_weights(args) -> int:
    from singvst_train import export_rvc
    print(export_rvc.make_test_weights(args.rvc_root, args.out, args.seed))
    return 0


def _cmd_evaluate(args) -> int:
    from singvst_train import evaluate, metrics
    from singvst_train.pipeline import atomic_write_text
    thresholds = json.loads(args.thresholds.read_text(encoding="utf-8"))
    report = evaluate.evaluate_voice(args.voice, args.heldout, args.phrases, args.render_bin, args.out, args.seed, args.lockfile)
    if report["status"] == "measured":
        verdict = metrics.judge(report, thresholds)
    else:
        verdict = {"all": False, "status": report["status"]}
    atomic_write_text(args.out / "verdict.json", json.dumps(verdict, sort_keys=True, indent=1) + "\n")
    print(f"{report['status']} -> {args.out / 'report.json'}")
    return 0


def _cmd_provenance(args) -> int:
    from singvst_train import provenance
    record = provenance.collect(json.loads(args.params), json.loads(args.seeds), args.repo, args.lockfile)
    print(provenance.write_sidecar(args.result, record))
    return 0


_HANDLERS = {"split": _cmd_split, "prepare": _cmd_prepare, "pack": _cmd_pack, "provenance": _cmd_provenance,
             "export": _cmd_export, "make-test-weights": _cmd_make_test_weights, "rvc-files": _cmd_rvc_files,
             "rvc-train-command": _cmd_rvc_train_command, "evaluate": _cmd_evaluate}


def build_parser():
    """``argparse.ArgumentParser`` (prog ``singvst-train``) with one sub-command per name in COMMANDS; each sub-parser
    has ``--help``. Unknown commands exit 2 via argparse. ``split --files-dir DIR --seed N [--fraction F] --out FILE``
    lists ``*.wav`` names directly in DIR, applies ``prepare.split_heldout`` and writes ``{"train": [...], "heldout":
    [...]}`` (1-space indent) to FILE. The other commands' options are defined by the steps that implement them."""
    parser = argparse.ArgumentParser(prog="singvst-train", description="sing-vst training toolkit (D-015)")
    sub = parser.add_subparsers(dest="command", required=True, metavar="command")
    subs = {name: sub.add_parser(name, help=_HELP[name]) for name in COMMANDS}

    p = subs["split"]
    p.add_argument("--files-dir", required=True, type=Path)
    p.add_argument("--seed", required=True, type=int)
    p.add_argument("--fraction", type=float, default=0.1)
    p.add_argument("--out", required=True, type=Path)

    p = subs["prepare"]
    p.add_argument("--in", dest="in_dir", required=True, type=Path)
    p.add_argument("--out", required=True, type=Path)
    p.add_argument("--sr", type=int, default=48000)
    p.add_argument("--threshold-db", type=float, default=-40.0)
    p.add_argument("--min-sec", type=float, default=2.0)
    p.add_argument("--max-sec", type=float, default=15.0)
    p.add_argument("--dereverb", action="store_true")
    p.add_argument("--lockfile", type=Path, default=None)

    p = subs["pack"]
    p.add_argument("--out", required=True, type=Path)
    p.add_argument("--name", required=True)
    p.add_argument("--consent", required=True)
    p.add_argument("--guide-licence", required=True)
    for role in ("acoustic", "vocoder", "phonemes"):
        p.add_argument(f"--{role}", required=True, type=Path)
    for role in ("speaker", "languages", "synth", "content"):
        p.add_argument(f"--{role}", type=Path, default=None)
    p.add_argument("--language", default="en")
    p.add_argument("--steps", type=int, default=20)
    p.add_argument("--depth", type=float, default=0.4)
    p.add_argument("--converter-sample-rate", type=int, default=48000)
    p.add_argument("--speaker-id", type=int, default=0)

    p = subs["rvc-files"]
    p.add_argument("--exp-dir", required=True, type=Path)
    p.add_argument("--rvc-root", required=True, type=Path)
    p.add_argument("--sr-tag", default="48k")
    p.add_argument("--speaker-id", type=int, default=0)
    p.add_argument("--seed", type=int, default=0)

    p = subs["rvc-train-command"]
    p.add_argument("--exp-name", required=True)
    p.add_argument("--sr-tag", default="48k")
    p.add_argument("--batch-size", type=int, default=8)
    p.add_argument("--epochs", type=int, default=200)
    p.add_argument("--save-every", type=int, default=10)
    p.add_argument("--gpus", default="0")
    p.add_argument("--python", default=None)

    p = subs["export"]
    p.add_argument("--rvc-root", required=True, type=Path)
    group = p.add_mutually_exclusive_group(required=True)
    group.add_argument("--weights", type=Path)
    group.add_argument("--exp-name")
    p.add_argument("--out-dir", required=True, type=Path)

    p = subs["make-test-weights"]
    p.add_argument("--rvc-root", required=True, type=Path)
    p.add_argument("--out", required=True, type=Path)
    p.add_argument("--seed", type=int, default=0)

    p = subs["evaluate"]
    p.add_argument("--voice", required=True, type=Path)
    p.add_argument("--heldout", required=True, type=Path)
    p.add_argument("--phrases", required=True, type=Path)
    p.add_argument("--render-bin", required=True, type=Path)
    p.add_argument("--out", required=True, type=Path)
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--thresholds", type=Path, default=Path("eval/thresholds.json"))
    p.add_argument("--lockfile", type=Path, default=None)

    p = subs["provenance"]
    p.add_argument("--result", required=True, type=Path)
    p.add_argument("--params", required=True)
    p.add_argument("--seeds", required=True)
    p.add_argument("--repo", type=Path, default=Path("."))
    p.add_argument("--lockfile", type=Path, default=Path("python/requirements-lock.txt"))
    return parser


def main(argv: list[str] | None = None) -> int:
    """Parse ``argv`` and dispatch; returns the process exit code (0 success, 2 usage or input error, 3 run failure).
    Errors are printed to stderr as ``singvst-train: <command>: <message>``."""
    args = build_parser().parse_args(argv)
    handler = _HANDLERS.get(args.command)
    try:
        if handler is None:
            raise NotImplementedError(f"the {args.command} command is added by a later plan step")
        return handler(args)
    except (ValueError, FileNotFoundError, NotADirectoryError, json.JSONDecodeError) as exc:
        print(f"singvst-train: {args.command}: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:    # noqa: BLE001 - a run failure is reported, not hidden (exit 3)
        print(f"singvst-train: {args.command}: {exc}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
