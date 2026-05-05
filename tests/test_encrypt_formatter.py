"""Tests for envpatch.encrypt_formatter."""

from envpatch.encryptor import generate_key, encrypt_file, decrypt_file, _ENC_PREFIX
from envpatch.encrypt_formatter import format_encrypt_report, format_decrypt_report
from envpatch.parser import EnvEntry, EnvFile


def _entry(key: str, value: str) -> EnvEntry:
    return EnvEntry(key=key, value=value, comment="", line_number=1)


def _make_file(*entries: EnvEntry) -> EnvFile:
    return EnvFile(entries=list(entries))


def test_format_encrypt_report_includes_key_names():
    key = generate_key()
    f = _make_file(_entry("API_SECRET", "s3cr3t"), _entry("APP_NAME", "app"))
    result = encrypt_file(f, key)
    report = format_encrypt_report(result)
    assert "API_SECRET" in report
    assert "APP_NAME" in report


def test_format_encrypt_report_shows_encrypted_label():
    key = generate_key()
    f = _make_file(_entry("API_SECRET", "s3cr3t"))
    result = encrypt_file(f, key)
    report = format_encrypt_report(result)
    assert "encrypted" in report.lower()


def test_format_encrypt_report_shows_plain_label():
    key = generate_key()
    f = _make_file(_entry("APP_NAME", "myapp"))
    result = encrypt_file(f, key)
    report = format_encrypt_report(result)
    assert "plain" in report.lower()


def test_format_encrypt_report_includes_summary():
    key = generate_key()
    f = _make_file(_entry("DB_PASSWORD", "pass"))
    result = encrypt_file(f, key)
    report = format_encrypt_report(result)
    assert result.summary() in report


def test_format_decrypt_report_includes_key_names():
    key = generate_key()
    f = _make_file(_entry("API_SECRET", "s3cr3t"))
    enc = encrypt_file(f, key)
    dec = decrypt_file(enc.as_envfile(), key)
    report = format_decrypt_report(dec)
    assert "API_SECRET" in report


def test_format_decrypt_report_shows_decrypted_label():
    key = generate_key()
    f = _make_file(_entry("API_SECRET", "s3cr3t"))
    enc = encrypt_file(f, key)
    dec = decrypt_file(enc.as_envfile(), key)
    report = format_decrypt_report(dec)
    assert "decrypted" in report.lower()


def test_format_decrypt_report_shows_failed_label_on_wrong_key():
    key1 = generate_key()
    key2 = generate_key()
    f = _make_file(_entry("API_SECRET", "s3cr3t"))
    enc = encrypt_file(f, key1)
    dec = decrypt_file(enc.as_envfile(), key2)
    report = format_decrypt_report(dec)
    assert "FAILED" in report


def test_format_decrypt_report_includes_summary():
    key = generate_key()
    f = _make_file(_entry("DB_PASSWORD", "pass"))
    enc = encrypt_file(f, key)
    dec = decrypt_file(enc.as_envfile(), key)
    report = format_decrypt_report(dec)
    assert dec.summary() in report
