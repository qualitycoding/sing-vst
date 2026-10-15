"""Command-line entry point used by the training notebooks (D-016): ``python -m singvst_train.cli <command>``.
Stub until plan step S-012 (commands are added by S-012..S-015)."""
from __future__ import annotations

COMMANDS = ("prepare", "split", "rvc-files", "rvc-train-command", "export", "make-test-weights", "pack", "evaluate",
            "provenance")


def build_parser():
    """``argparse.ArgumentParser`` (prog ``singvst-train``) with one sub-command per name in COMMANDS; each sub-parser
    has ``--help``. Unknown commands exit 2 via argparse."""
    raise NotImplementedError("build_parser")


def main(argv: list[str] | None = None) -> int:
    """Parse ``argv`` and dispatch; returns the process exit code (0 success, 2 usage or input error, 3 run failure).
    Errors are printed to stderr as ``singvst-train: <command>: <message>``."""
    raise NotImplementedError("main")


if __name__ == "__main__":
    raise SystemExit(main())
