"""Score an .env file for security and quality hygiene."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from envpatch.parser import EnvFile
from envpatch.profiler import _is_placeholder, profile_file
from envpatch.differ import is_secret


@dataclass
class ScoreReport:
    total_keys: int
    secret_keys: int
    placeholder_keys: int
    empty_keys: int
    score: int  # 0-100
    grade: str
    penalties: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "total_keys": self.total_keys,
            "secret_keys": self.secret_keys,
            "placeholder_keys": self.placeholder_keys,
            "empty_keys": self.empty_keys,
            "score": self.score,
            "grade": self.grade,
            "penalties": self.penalties,
        }


def _grade(score: int) -> str:
    if score >= 90:
        return "A"
    if score >= 75:
        return "B"
    if score >= 60:
        return "C"
    if score >= 40:
        return "D"
    return "F"


def score_file(env_file: EnvFile) -> ScoreReport:
    """Compute a hygiene score (0-100) for *env_file*."""
    entries = [e for e in env_file.entries if not e.is_comment and not e.is_blank]
    total = len(entries)

    if total == 0:
        return ScoreReport(
            total_keys=0,
            secret_keys=0,
            placeholder_keys=0,
            empty_keys=0,
            score=100,
            grade="A",
            penalties=[],
        )

    profile = profile_file(env_file)
    secret_count = profile.secret_count
    placeholder_count = sum(1 for e in entries if _is_placeholder(e.value))
    empty_count = sum(1 for e in entries if e.value == "")

    penalties: List[str] = []
    deduction = 0

    if placeholder_count > 0:
        ratio = placeholder_count / total
        pts = int(ratio * 40)
        deduction += pts
        penalties.append(f"-{pts} pts: {placeholder_count} placeholder value(s)")

    if empty_count > 0:
        ratio = empty_count / total
        pts = int(ratio * 30)
        deduction += pts
        penalties.append(f"-{pts} pts: {empty_count} empty value(s)")

    if total < 3:
        deduction += 5
        penalties.append("-5 pts: fewer than 3 keys defined")

    score = max(0, 100 - deduction)
    return ScoreReport(
        total_keys=total,
        secret_keys=secret_count,
        placeholder_keys=placeholder_count,
        empty_keys=empty_count,
        score=score,
        grade=_grade(score),
        penalties=penalties,
    )
