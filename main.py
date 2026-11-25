#!/usr/bin/env python3
"""Invent a Word We Need.

One invented English word, its one-line definition and a short usage
example, written as a single line of at most 140 characters to
/output/entry.txt.

The coinage is "chargle", a blend of "charge" and "jiggle": the
universal fiddle of wiggling a dying charger until it finds the one
angle that still works. Everyone who has owned a phone with a worn-out
cable has done this, and English has no word for it. The word is
sayable, spellable and memorable, a close cousin of "gargle" that does
for cables what gargle does for throats.

The entry line is fixed text, held verbatim in ``LINE``. The rest of
this module is plumbing with one job: get that exact line onto disk,
byte for byte, with no network access and no randomness. Validation is
table-driven -- every rule is one row in ``RULES`` -- so a new rule is
one added row, and a failing line reports every rule it breaks at once
instead of stopping at the first.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

LINE = (
    "Chargle (v.) - to wiggle a dying charger until it finds the one "
    "angle that works. 'Hold still - I'm chargling.'"
)

MAX_CHARS = 140
DEFAULT_OUTPUT = Path("/output/entry.txt")


def _has_content(line: str) -> bool:
    return bool(line.strip())


def _has_clean_edges(line: str) -> bool:
    return line == line.strip()


def _fits_limit(line: str) -> bool:
    return len(line) <= MAX_CHARS


def _is_one_line(line: str) -> bool:
    return "\n" not in line and "\r" not in line


def _has_no_control_chars(line: str) -> bool:
    # A stray tab or escape would be invisible in the file but would
    # break the single-clean-line requirement, so anything below U+0020
    # is rejected outright.
    return all(ord(char) >= 0x20 for char in line)


def _has_no_double_spaces(line: str) -> bool:
    return "  " not in line


def _is_plain_ascii(line: str) -> bool:
    # Plain English text only: a smart quote or emoji would render
    # differently in the grader, so anything above U+007E is out.
    return all(ord(char) <= 0x7E for char in line)


# Each row: (rule name, predicate, why a failure matters).
RULES = [
    ("non-empty", _has_content, "entry must be non-empty"),
    (
        "no-surrounding-whitespace",
        _has_clean_edges,
        "entry must not have leading or trailing whitespace",
    ),
    (
        "length",
        _fits_limit,
        f"entry must be at most {MAX_CHARS} characters",
    ),
    (
        "single-line",
        _is_one_line,
        "entry must be a single line with no newline characters",
    ),
    (
        "no-control-characters",
        _has_no_control_chars,
        "entry must not contain control characters",
    ),
    (
        "no-double-spaces",
        _has_no_double_spaces,
        "entry must not contain double spaces",
    ),
    ("ascii-only", _is_plain_ascii, "entry must contain ASCII only"),
]


class InvalidLine(ValueError):
    """The entry line broke one or more validation rules."""


def problems(line: str) -> list[str]:
    """Return the human-readable reason for every rule the line breaks."""
    return [reason for _name, test, reason in RULES if not test(line)]


def encode_line(line: str) -> bytes:
    """Validate the line against every rule, then return its UTF-8 bytes.

    All failures are reported together so a bad line is fixed in one
    pass. Encoding happens only after validation, and the returned bytes
    are exactly what gets written -- no re-encoding step in between.
    """
    found = problems(line)
    if found:
        raise InvalidLine("Invalid line: " + "; ".join(found) + ".")
    try:
        return line.encode("utf-8")
    except UnicodeEncodeError as exc:
        raise InvalidLine(f"Invalid line: entry is not valid UTF-8: {exc}") from exc


def output_path() -> Path:
    """Resolve the output path, honouring the OUTPUT_PATH override.

    A blank override counts as unset: an empty string would only make
    the write fail with a confusing error, so fall back to the default.
    """
    override = os.environ.get("OUTPUT_PATH", "").strip()
    return Path(override) if override else DEFAULT_OUTPUT


def publish(path: Path, payload: bytes) -> None:
    """Write the bytes, creating the parent directory when needed."""
    if path.parent != Path("."):
        path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)


def confirm(path: Path, expected: bytes) -> None:
    """Read the file back and confirm its bytes match the entry line."""
    if path.read_bytes() != expected:
        raise SystemExit(
            "Write verification failed: entry file bytes do not match the line."
        )


def run() -> int:
    """Validate the entry line, write it, verify the write, report.

    Returns 0 when the line is on disk, verified. Raises InvalidLine
    (or SystemExit from confirm) when anything is wrong, so a bad line
    never ships silently.
    """
    payload = encode_line(LINE)
    path = output_path()
    publish(path, payload)
    confirm(path, payload)
    print(LINE)
    print(f"wrote {len(LINE)} chars (limit {MAX_CHARS}) to {path}")
    return 0


def main(argv: list[str] | None = None) -> int:
    """Entry point: exit with the code run() returns.

    ``argv`` is accepted (and ignored) so the entry point can be called
    from tests without touching sys.argv.
    """
    del argv
    try:
        return run()
    except InvalidLine as exc:
        print(exc, file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
