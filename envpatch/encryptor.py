"""Encrypt and decrypt secret values in an EnvFile using Fernet symmetric encryption."""

from __future__ import annotations

import base64
import os
from dataclasses import dataclass, field
from typing import List, Optional

from cryptography.fernet import Fernet, InvalidToken

from envpatch.parser import EnvEntry, EnvFile
from envpatch.differ import is_secret


@dataclass
class EncryptResult:
    entries: List[EnvEntry]
    encrypted_count: int
    skipped_count: int
    key_used: bytes

    def as_envfile(self) -> EnvFile:
        return EnvFile(entries=self.entries)

    def summary(self) -> str:
        return (
            f"Encrypted {self.encrypted_count} secret(s), "
            f"skipped {self.skipped_count} plain value(s)."
        )


@dataclass
class DecryptResult:
    entries: List[EnvEntry]
    decrypted_count: int
    failed_count: int

    def as_envfile(self) -> EnvFile:
        return EnvFile(entries=self.entries)

    def summary(self) -> str:
        return (
            f"Decrypted {self.decrypted_count} value(s), "
            f"{self.failed_count} failed (wrong key or not encrypted)."
        )


_ENC_PREFIX = "enc:"


def generate_key() -> bytes:
    """Return a new URL-safe base64-encoded 32-byte Fernet key."""
    return Fernet.generate_key()


def encrypt_file(env_file: EnvFile, key: bytes) -> EncryptResult:
    """Encrypt all secret entries in *env_file*; leave plain entries untouched."""
    fernet = Fernet(key)
    new_entries: List[EnvEntry] = []
    encrypted = 0
    skipped = 0

    for entry in env_file.entries:
        if entry.key is None or not is_secret(entry.key):
            new_entries.append(entry)
            skipped += 1
            continue
        if entry.value and entry.value.startswith(_ENC_PREFIX):
            # already encrypted — leave as-is
            new_entries.append(entry)
            skipped += 1
            continue
        token = fernet.encrypt((entry.value or "").encode()).decode()
        new_entries.append(
            EnvEntry(
                key=entry.key,
                value=f"{_ENC_PREFIX}{token}",
                comment=entry.comment,
                line_number=entry.line_number,
            )
        )
        encrypted += 1

    return EncryptResult(
        entries=new_entries,
        encrypted_count=encrypted,
        skipped_count=skipped,
        key_used=key,
    )


def decrypt_file(env_file: EnvFile, key: bytes) -> DecryptResult:
    """Decrypt all *enc:* prefixed entries in *env_file*."""
    fernet = Fernet(key)
    new_entries: List[EnvEntry] = []
    decrypted = 0
    failed = 0

    for entry in env_file.entries:
        if entry.key is None or not (entry.value or "").startswith(_ENC_PREFIX):
            new_entries.append(entry)
            continue
        token = entry.value[len(_ENC_PREFIX):]
        try:
            plain = fernet.decrypt(token.encode()).decode()
            new_entries.append(
                EnvEntry(
                    key=entry.key,
                    value=plain,
                    comment=entry.comment,
                    line_number=entry.line_number,
                )
            )
            decrypted += 1
        except (InvalidToken, Exception):
            new_entries.append(entry)
            failed += 1

    return DecryptResult(
        entries=new_entries,
        decrypted_count=decrypted,
        failed_count=failed,
    )
