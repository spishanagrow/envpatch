"""Format TagResult for CLI output."""
from __future__ import annotations

from typing import List

from envpatch.tagger import TagResult

TAG_COLOR = "\033[36m"   # cyan
KEY_COLOR = "\033[33m"   # yellow
RESET = "\033[0m"


def _colorize(text: str, color: str, use_color: bool) -> str:
    if not use_color:
        return text
    return f"{color}{text}{RESET}"


def format_tag_report(result: TagResult, use_color: bool = True) -> str:
    if not result.tag_map:
        return "No tagged entries found."

    lines: List[str] = []
    all_tags = sorted(result.all_tags())

    for tag in all_tags:
        keys = sorted(result.keys_with_tag(tag))
        tag_label = _colorize(f"[{tag}]", TAG_COLOR, use_color)
        key_labels = ", ".join(_colorize(k, KEY_COLOR, use_color) for k in keys)
        lines.append(f"{tag_label}  {key_labels}")

    return "\n".join(lines)


def format_tag_summary(result: TagResult, use_color: bool = True) -> str:
    summary = result.summary()
    return _colorize(summary, TAG_COLOR, use_color)


def format_keys_for_tag(result: TagResult, tag: str, use_color: bool = True) -> str:
    keys = result.keys_with_tag(tag)
    if not keys:
        return f"No keys tagged with '{tag}'."
    return "\n".join(_colorize(k, KEY_COLOR, use_color) for k in sorted(keys))
