"""Redact secret values from .env files before sharing or logging."""

from typing import Optional
from envpatch.parser import EnvFile, EnvEntry
from envpatch.differ import is_secret

DEFAULT_MASK = "***REDACTED***"
_PLACEHOLDER = "<redacted>"


def redact_entry(entry: EnvEntry, mask: str = DEFAULT_MASK) -> EnvEntry:
    """Return a copy of entry with its value replaced by mask if it is a secret."""
    if is_secret(entry.key):
        return EnvEntry(
            key=entry.key,
            value=mask,
            raw_line=f"{entry.key}={mask}",
            line_number=entry.line_number,
            comment=entry.comment,
        )
    return entry


def redact_file(env_file: EnvFile, mask: str = DEFAULT_MASK) -> EnvFile:
    """Return a new EnvFile with all secret values redacted."""
    redacted_entries = [redact_entry(e, mask) for e in env_file.entries]
    return EnvFile(entries=redacted_entries, path=env_file.path)


def redact_string(env_string: str, mask: str = DEFAULT_MASK) -> str:
    """Parse an env string, redact secrets, and return the redacted string."""
    from envpatch.parser import parse_env_string
    from envpatch.merger import as_string

    env_file = parse_env_string(env_string)
    redacted = redact_file(env_file, mask)
    lines: list[str] = []
    for entry in redacted.entries:
        if entry.comment:
            lines.append(f"{entry.key}={entry.value}  # {entry.comment}")
        else:
            lines.append(f"{entry.key}={entry.value}")
    return "\n".join(lines)


def summary(env_file: EnvFile) -> dict[str, int]:
    """Return counts of total keys and how many are secrets."""
    total = len(env_file.entries)
    secrets = sum(1 for e in env_file.entries if is_secret(e.key))
    return {"total": total, "secrets": secrets, "plain": total - secrets}
