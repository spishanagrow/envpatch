"""Variable interpolation support for .env files.

Supports ${VAR} and $VAR style references within values,
resolving them against a provided context or the file itself.
"""

import re
from typing import Dict, Optional

from envpatch.parser import EnvFile

_VAR_PATTERN = re.compile(r'\$\{([^}]+)\}|\$([A-Za-z_][A-Za-z0-9_]*)')


def _resolve_value(
    value: str,
    context: Dict[str, str],
    visited: Optional[set] = None,
) -> str:
    """Recursively resolve variable references in *value*.

    Raises ValueError on circular references.
    """
    if visited is None:
        visited = set()

    def _replace(match: re.Match) -> str:
        var_name = match.group(1) or match.group(2)
        if var_name in visited:
            raise ValueError(f"Circular reference detected for variable '{var_name}'")
        if var_name not in context:
            # Leave unresolvable references as-is
            return match.group(0)
        visited_copy = visited | {var_name}
        return _resolve_value(context[var_name], context, visited_copy)

    return _VAR_PATTERN.sub(_replace, value)


def interpolate_file(
    env_file: EnvFile,
    extra_context: Optional[Dict[str, str]] = None,
) -> Dict[str, str]:
    """Return a dict of all keys with variable references fully resolved.

    Resolution order: extra_context overrides file-defined values.
    """
    from envpatch.parser import as_dict

    base: Dict[str, str] = as_dict(env_file)
    context: Dict[str, str] = {**base, **(extra_context or {})}

    resolved: Dict[str, str] = {}
    for key, value in base.items():
        resolved[key] = _resolve_value(value, context)
    return resolved


def find_unresolved(env_file: EnvFile) -> Dict[str, list]:
    """Return a mapping of key -> list of unresolvable variable names."""
    from envpatch.parser import as_dict

    context = as_dict(env_file)
    unresolved: Dict[str, list] = {}

    for key, value in context.items():
        missing = [
            m.group(1) or m.group(2)
            for m in _VAR_PATTERN.finditer(value)
            if (m.group(1) or m.group(2)) not in context
        ]
        if missing:
            unresolved[key] = missing

    return unresolved
