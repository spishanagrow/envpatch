# envpatch

> CLI tool to safely diff and merge `.env` files across environments without leaking secrets.

---

## Installation

```bash
pip install envpatch
```

Or with [pipx](https://pypa.github.io/pipx/):

```bash
pipx install envpatch
```

---

## Usage

**Diff two `.env` files** (values are masked by default):

```bash
envpatch diff .env.development .env.production
```

**Merge changes from one `.env` into another:**

```bash
envpatch merge .env.staging .env.production --output .env.production
```

**Show keys only, never values:**

```bash
envpatch diff .env .env.example --keys-only
```

**Check for missing keys between environments:**

```bash
envpatch check .env .env.example
```

Example output:

```
~ DB_HOST        [changed]
+ SENTRY_DSN     [added]
- OLD_API_KEY    [removed]
```

Secrets are never printed in plain text unless `--reveal` is explicitly passed.

---

## Options

| Flag | Description |
|------|-------------|
| `--keys-only` | Show only key names, hide all values |
| `--reveal` | Print actual values (use with caution) |
| `--output FILE` | Write merged result to a file |
| `--dry-run` | Preview changes without writing |

---

## License

[MIT](LICENSE) © envpatch contributors