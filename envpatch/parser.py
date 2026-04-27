"""Parser for .env files — handles reading and tokenizing key-value pairs."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

_LINE_RE = re.compile(
    r"^\s*(?P<key>[A-Za-z_][A-Za-z0-9_]*)\s*=\s*(?P<value>.*)$"
)
_COMMENT_RE = re.compile(r"^\s*#")


@dataclass
class EnvEntry:
    key: str
    value: str
    comment: Optional[str] = None  # inline comment stripped from value
    line_number: int = 0


@dataclass
class EnvFile:
    path: Optional[Path] = None
    entries: List[EnvEntry] = field(default_factory=list)

    def as_dict(self) -> Dict[str, str]:
        return {e.key: e.value for e in self.entries}


def _strip_inline_comment(raw: str) -> tuple[str, Optional[str]]:
    """Split 'value  # comment' into (value, comment)."""
    # Only strip unquoted inline comments
    if raw.startswith(("'", '"')):
        quote = raw[0]
        end = raw.find(quote, 1)
        if end != -1:
            return raw[1:end], None
    idx = raw.find(" #")
    if idx != -1:
        return raw[:idx].strip(), raw[idx + 1:].strip()
    return raw.strip(), None


def parse_env_string(text: str, source: Optional[Path] = None) -> EnvFile:
    """Parse a .env file string into an EnvFile object."""
    env_file = EnvFile(path=source)
    for lineno, line in enumerate(text.splitlines(), start=1):
        if not line.strip() or _COMMENT_RE.match(line):
            continue
        m = _LINE_RE.match(line)
        if m:
            raw_value = m.group("value")
            value, comment = _strip_inline_comment(raw_value)
            env_file.entries.append(
                EnvEntry(
                    key=m.group("key"),
                    value=value,
                    comment=comment,
                    line_number=lineno,
                )
            )
    return env_file


def parse_env_file(path: Path) -> EnvFile:
    """Read and parse a .env file from disk."""
    text = path.read_text(encoding="utf-8")
    return parse_env_string(text, source=path)
