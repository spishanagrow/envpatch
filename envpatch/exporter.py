"""Export redacted or full env files to various output formats."""

from __future__ import annotations

import json
from typing import Dict, List, Optional

from envpatch.parser import EnvFile
from envpatch.redactor import redact_file


def to_dict(
    env_file: EnvFile,
    redact: bool = False,
    mask: str = "***",
) -> Dict[str, str]:
    """Return a plain dict of key/value pairs from an EnvFile.

    Args:
        env_file: Parsed environment file.
        redact:   If True, secret values are replaced with *mask*.
        mask:     Replacement string used when *redact* is True.
    """
    source = redact_file(env_file, mask=mask) if redact else env_file
    return {entry.key: entry.value for entry in source.entries}


def to_json(
    env_file: EnvFile,
    redact: bool = False,
    mask: str = "***",
    indent: int = 2,
) -> str:
    """Serialise an EnvFile to a JSON string."""
    return json.dumps(to_dict(env_file, redact=redact, mask=mask), indent=indent)


def to_shell(
    env_file: EnvFile,
    redact: bool = False,
    mask: str = "***",
    export: bool = True,
) -> str:
    """Serialise an EnvFile to shell-sourceable export statements.

    Example output::

        export DB_HOST=localhost
        export DB_PASS=***
    """
    prefix = "export " if export else ""
    lines: List[str] = []
    source = redact_file(env_file, mask=mask) if redact else env_file
    for entry in source.entries:
        value = entry.value
        # Quote value if it contains spaces or special characters
        if any(ch in value for ch in (" ", "\t", "$", "`", '"', "'")):
            value = '"' + value.replace('"', '\\"') + '"'
        lines.append(f"{prefix}{entry.key}={value}")
    return "\n".join(lines)


def to_dotenv(
    env_file: EnvFile,
    redact: bool = False,
    mask: str = "***",
) -> str:
    """Re-serialise an EnvFile back to .env format, optionally redacted."""
    source = redact_file(env_file, mask=mask) if redact else env_file
    lines: List[str] = []
    for entry in source.entries:
        lines.append(f"{entry.key}={entry.value}")
    return "\n".join(lines)
