"""Generate .env.example / template files from existing env files.

Replaces secret values with placeholder strings and preserves
comments, blank lines, and key ordering.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from envpatch.parser import EnvFile, EnvEntry
from envpatch.differ import is_secret

DEFAULT_PLACEHOLDER = "<YOUR_{key}_HERE>"
SECRET_PLACEHOLDER = "<SECRET>"


@dataclass
class TemplateResult:
    entries: list[EnvEntry]
    source_path: Optional[str]
    total: int
    redacted: int

    def as_string(self) -> str:
        """Render the template back to .env file content."""
        lines: list[str] = []
        for entry in self.entries:
            if entry.key is None:
                # blank line or comment — preserve as-is
                lines.append(entry.raw_line)
            else:
                lines.append(f"{entry.key}={entry.value}")
        return "\n".join(lines)

    @property
    def summary(self) -> str:
        return (
            f"Template generated: {self.total} keys, "
            f"{self.redacted} redacted, "
            f"{self.total - self.redacted} kept as-is."
        )


def _placeholder_for(key: str, use_key_name: bool) -> str:
    if use_key_name:
        return DEFAULT_PLACEHOLDER.format(key=key)
    return SECRET_PLACEHOLDER


def generate_template(
    env_file: EnvFile,
    *,
    use_key_name: bool = True,
    keep_non_secrets: bool = True,
    placeholder: Optional[str] = None,
) -> TemplateResult:
    """Return a TemplateResult with secret values replaced by placeholders.

    Args:
        env_file: Parsed source EnvFile.
        use_key_name: When True, embed the key name in the placeholder.
        keep_non_secrets: When True, non-secret values are left unchanged.
        placeholder: Override the placeholder string entirely (ignores use_key_name).
    """
    new_entries: list[EnvEntry] = []
    redacted = 0
    total = 0

    for entry in env_file.entries:
        if entry.key is None:
            new_entries.append(entry)
            continue

        total += 1
        if is_secret(entry.key):
            fill = placeholder if placeholder else _placeholder_for(entry.key, use_key_name)
            new_entries.append(
                EnvEntry(
                    key=entry.key,
                    value=fill,
                    raw_line=f"{entry.key}={fill}",
                    line_number=entry.line_number,
                )
            )
            redacted += 1
        else:
            value = entry.value if keep_non_secrets else ""
            new_entries.append(
                EnvEntry(
                    key=entry.key,
                    value=value,
                    raw_line=f"{entry.key}={value}",
                    line_number=entry.line_number,
                )
            )

    return TemplateResult(
        entries=new_entries,
        source_path=env_file.path,
        total=total,
        redacted=redacted,
    )
