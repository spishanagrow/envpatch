"""Formatter for strategy merge results."""
from envpatch.merger_strategy import StrategyResult


def _colorize(text: str, code: str) -> str:
    return f"\033[{code}m{text}\033[0m"


def format_strategy_report(
    result: StrategyResult,
    *,
    color: bool = True,
    show_kept: bool = True,
    show_overwritten: bool = True,
) -> str:
    if not result.resolved:
        msg = "No conflicts detected."
        return _colorize(msg, "32") if color else msg

    lines: list[str] = []

    if show_overwritten and result.overwritten:
        header = f"Overwritten ({len(result.overwritten)}):"
        lines.append(_colorize(header, "33") if color else header)
        for key in result.overwritten:
            prefix = _colorize("  ~ ", "33") if color else "  ~ "
            lines.append(f"{prefix}{key}")

    if show_kept and result.kept:
        header = f"Kept ({len(result.kept)}):"
        lines.append(_colorize(header, "34") if color else header)
        for key in result.kept:
            prefix = _colorize("  = ", "34") if color else "  = "
            lines.append(f"{prefix}{key}")

    return "\n".join(lines)


def format_strategy_summary(result: StrategyResult, *, color: bool = True) -> str:
    msg = result.summary()
    if not result.resolved:
        return _colorize(msg, "32") if color else msg
    return _colorize(msg, "33") if color else msg
