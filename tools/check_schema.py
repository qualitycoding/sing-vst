"""Appendix C schema check, copied verbatim from planning-protocol.md v3.2."""
import pathlib, re, sys
REQUIRED = {
    "L": ["id", "title", "status", "supersedes", "recurrence_of", "occurrences", "severity", "tags", "recorded_by", "run", "recorded_at"],
    "K": ["id", "statement", "status", "supersedes", "tags", "applies_to_version", "source", "confidence", "derived_from", "discovered_by", "run", "recorded_at"],
}
FACETS = ("domain:", "tech:", "subject:", "phase:", "kind:", "applies:")
SECRET = re.compile(r"github_pat_[A-Za-z0-9_]{20,}|ghp_[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}|-----BEGIN [A-Z ]*PRIVATE KEY-----")
problems = []
for path in sorted([*pathlib.Path(".").glob("lessons/**/L-*.md"), *pathlib.Path(".").glob("knowledge/**/K-*.md")]):
    text = path.read_text(encoding="utf-8")
    parts = text.split("---", 2)
    head = parts[1] if text.startswith("---") and len(parts) == 3 else ""
    fields = dict(re.findall(r"^(\w+):[ \t]*(.*)$", head, re.M))
    problems += [f"{path}: missing field '{f}'" for f in REQUIRED[path.name[0]] if f not in fields]
    if fields.get("id", "").split("#")[0].strip() != path.stem:
        problems.append(f"{path}: id does not match the file name")
    tags = re.findall(r"[\w-]+:[\w.-]+", fields.get("tags", ""))
    if not tags:
        problems.append(f"{path}: no tags")
    problems += [f"{path}: unknown tag facet '{t}'" for t in tags if not t.startswith(FACETS)]
    if path.name.startswith("K-") and not any(t.startswith("subject:") for t in tags):
        problems.append(f"{path}: no subject: tag")
    if SECRET.search(text):
        problems.append(f"{path}: possible secret")
print("\n".join(problems) or "all entries valid")
sys.exit(1 if problems else 0)
