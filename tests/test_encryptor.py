"""Tests for envpatch.encryptor."""

import pytest

from envpatch.encryptor import (
    generate_key,
    encrypt_file,
    decrypt_file,
    _ENC_PREFIX,
    EncryptResult,
    DecryptResult,
)
from envpatch.parser import EnvEntry, EnvFile


def _entry(key: str, value: str, comment: str = "") -> EnvEntry:
    return EnvEntry(key=key, value=value, comment=comment, line_number=1)


def _make_file(*entries: EnvEntry) -> EnvFile:
    return EnvFile(entries=list(entries))


@pytest.fixture()
def key():
    return generate_key()


@pytest.fixture()
def mixed_file():
    return _make_file(
        _entry("APP_NAME", "myapp"),
        _entry("DATABASE_PASSWORD", "s3cr3t"),
        _entry("API_SECRET", "topsecret"),
        _entry("DEBUG", "true"),
    )


def test_generate_key_returns_bytes():
    k = generate_key()
    assert isinstance(k, bytes)
    assert len(k) > 0


def test_encrypt_secret_keys(key, mixed_file):
    result = encrypt_file(mixed_file, key)
    encrypted_values = {
        e.key: e.value for e in result.entries if e.key in ("DATABASE_PASSWORD", "API_SECRET")
    }
    for val in encrypted_values.values():
        assert val.startswith(_ENC_PREFIX)


def test_encrypt_plain_keys_untouched(key, mixed_file):
    result = encrypt_file(mixed_file, key)
    plain = {e.key: e.value for e in result.entries}
    assert plain["APP_NAME"] == "myapp"
    assert plain["DEBUG"] == "true"


def test_encrypt_count(key, mixed_file):
    result = encrypt_file(mixed_file, key)
    assert result.encrypted_count == 2
    assert result.skipped_count == 2


def test_already_encrypted_not_double_encrypted(key):
    already = _make_file(_entry("API_SECRET", f"{_ENC_PREFIX}sometoken"))
    result = encrypt_file(already, key)
    assert result.encrypted_count == 0
    assert result.skipped_count == 1
    assert result.entries[0].value == f"{_ENC_PREFIX}sometoken"


def test_decrypt_restores_original(key, mixed_file):
    enc_result = encrypt_file(mixed_file, key)
    dec_result = decrypt_file(enc_result.as_envfile(), key)
    values = {e.key: e.value for e in dec_result.entries}
    assert values["DATABASE_PASSWORD"] == "s3cr3t"
    assert values["API_SECRET"] == "topsecret"
    assert dec_result.decrypted_count == 2
    assert dec_result.failed_count == 0


def test_decrypt_wrong_key_increments_failed(mixed_file):
    key1 = generate_key()
    key2 = generate_key()
    enc_result = encrypt_file(mixed_file, key1)
    dec_result = decrypt_file(enc_result.as_envfile(), key2)
    assert dec_result.failed_count == 2


def test_encrypt_result_summary(key, mixed_file):
    result = encrypt_file(mixed_file, key)
    s = result.summary()
    assert "2" in s
    assert "secret" in s.lower()


def test_decrypt_result_summary(key, mixed_file):
    enc = encrypt_file(mixed_file, key)
    dec = decrypt_file(enc.as_envfile(), key)
    s = dec.summary()
    assert "2" in s
    assert "Decrypted" in s


def test_as_envfile_returns_envfile(key, mixed_file):
    result = encrypt_file(mixed_file, key)
    ef = result.as_envfile()
    assert isinstance(ef, EnvFile)
    assert len(ef.entries) == len(mixed_file.entries)
