"""Format encrypt/decrypt results for terminal output."""

from __future__ import annotations

import sys

from envpatch.encryptor import EncryptResult, DecryptResult, _ENC_PREFIX

_GREEN = "\033[32m"
_YELLOW = "\033[33m"
_RED = "\033[31m"
_RESET = "\033[0m"


def _colorize(text: str, color: str) -> str:
    if sys.stdout.isatty():
        return f"{color}{text}{_RESET}"
    return text


def format_encrypt_report(result: EncryptResult) -> str:
    """Return a human-readable report of an encrypt operation."""
    lines = []
    for entry in result.entries:
        if entry.key is None:
            continue
        val = entry.value or ""
        if val.startswith(_ENC_PREFIX):
            label = _colorize("[encrypted]", _GREEN)
            lines.append(f"  {entry.key} {label}")
        else:
            label = _colorize("[plain]", _YELLOW)
            lines.append(f"  {entry.key} {label}")
    lines.append("")
    lines.append(_colorize(result.summary(), _GREEN))
    return "\n".join(lines)


def format_decrypt_report(result: DecryptResult) -> str:
    """Return a human-readable report of a decrypt operation."""
    lines = []
    for entry in result.entries:
        if entry.key is None:
            continue
        val = entry.value or ""
        if val.startswith(_ENC_PREFIX):
            label = _colorize("[FAILED]", _RED)
            lines.append(f"  {entry.key} {label}")
        else:
            label = _colorize("[decrypted]", _GREEN)
            lines.append(f"  {entry.key} {label}")
    lines.append("")
    if result.failed_count:
        lines.append(_colorize(result.summary(), _RED))
    else:
        lines.append(_colorize(result.summary(), _GREEN))
    return "\n".join(lines)
