# Mailer Module - Plan

**Project:** emailcert  
**Module:** mailer (email sending)  
**Status:** Planning  
**Last Updated:** 2026-09-02

---

## 1. Purpose

Reusable, provider-agnostic Python module to send emails with optional attachments. Designed to be imported standalone (`from emailcert.mailer import SmtpMailer`) without depending on `certgen` or `tracker`. Caller owns templating and orchestration; mailer owns validation and delivery.

---

## 2. Scope

### 2.1 In Scope (Must Have)
- Initialize mailer with config object (`MailerConfig`) containing `from_address`, credentials/api keys
- Send single email via `send(to_address, subject, body, body_type, attachment)` where `to_address` is required and at least one of `subject/body/attachment` is required (after stripping); caller specifies `body_type` (`"html"` or `"text"`) when `body` is provided
- Validate all caller inputs before network call (email format, non-empty checks, attachment size)
- Provider-agnostic via `BaseMailer` ABC; concrete providers (`SmtpMailer`, `BrevoMailer`) implement same `send()` signature
- Raise on error, return on success (no `error: msg` dict returns)
- Comprehensive logging at each step

### 2.2 Out of Scope (Explicitly NOT Doing)
- **Already-emailed check / idempotent tracking** — belongs to `tracker/` + `cli.py` orchestrator. Mailer is stateless, no DB/JSON reads.
- **Automatic retry** — mailer raises `SendError` with details; caller decides to retry/persist. No internal retry loop.
- **Templating (`{{name}}` replacement)** — caller builds `subject`/`body` strings before calling `send()`.
- **Certificate generation** — no import from `certgen`.
- **Bulk send as default** — `BaseMailer.send()` sends one email. Bulk is optional `send_bulk()` extension, not mandatory for v1.
- **Failed-email persistence (DB/JSON)** — mailer returns/raises failure details; persistence is orchestrator's responsibility. Mailer does not write to storage.

---

## 3. Config

### 3.1 MailerConfig Dataclass

```python
@dataclass
class MailerConfig:
    from_address: str              # required, must contain @
    password: str | None = None    # required for SMTP, ignored for API-key providers
    smtp_host: str | None = None   # e.g. smtp.gmail.com
    smtp_port: int = 587
    brevo_api_key: str | None = None  # for Brevo provider
    # Provider-specific keys are optional at dataclass level but validated per provider
```

### 3.2 Config Validation

- `from_address` always required, must contain `@` and be non-empty after `strip()` — else `ConfigError` at `__init__`
- Provider-specific required fields validated at `__init__`:
  - `SmtpMailer` requires `smtp_host` + `password`
  - `BrevoMailer` requires `brevo_api_key`
- If caller calls `Mailer()` with no config / missing required fields → raise `ConfigError` immediately, not at `send()` time
- Empty string / whitespace-only considered as `None` (treated as missing)

---

## 4. I/O & Workflow

### 4.1 Input

- **Init:** `mailer = SmtpMailer(config: MailerConfig)`
- **Send arg:** `request: EmailRequest` dataclass:

```python
@dataclass
class EmailRequest:
    to_address: str
    subject: str | None = None
    body: str | None = None
    body_type: str = "text"  # "html" or "text" — used when body is present
    attachment: tuple[bytes, str] | None = None  # (file_bytes, filename)
    # No validation here — plain data holder, validated at send() via validator.py
```

- `to_address` required single email; `subject/body/attachment` at least one required after stripping (empty `""/"   "` treated as missing)

### 4.2 Output

- Success: `return True` (or `return message_id` if provider gives one)
- Failure: `raise MailerError` subclass — never `return {"error": ...}`

### 4.3 Workflow (inside `send()`)

```
1. Validate config already done at __init__ (fail fast)
2. BaseMailer.send(request) validates via validator.py (single validation point):
   - to_address: strip, check non-empty, contains @ else ValidationError
   - subject/body/attachment: strip, check at least one non-empty/valid else ValidationError
   - body_type: normalized to lowercase in validator, default "text" if body present else ignored — must be "html"/"text" else ValidationError
   - attachment: bytes length > 0 and filename non-empty after strip else ValidationError
3. Delegate to provider's transport (smtplib / Brevo API) — provider sets MIME subtype from normalized request.body_type
4. On provider failure (timeout, auth, network): raise SendError with original cause
5. On success: log and return True
```

No automatic retry, no DB write. Caller catches `SendError` and decides to persist to `tracker`.

---

## 5. Validation Rules

| Field | Required | Empty handling | Rule | Error |
|-------|----------|----------------|------|-------|
| `from_address` (config) | Yes | `""` / `"   "` = missing | Must contain `@`, 1-254 chars, strip | `ConfigError` |
| `to_address` | Yes | `""` / `"   "` = missing | Single email, strip, must contain `@` | `ValidationError` |
| `subject` | At least one of subject/body/attachment required | `""` / `"   "` = missing | 0-998 chars if present, strip | `ValidationError` |
| `body` | At least one required | `""` / `"   "` = missing | Non-empty after strip if sole field | `ValidationError` |
| `body_type` | Required if body present | `""` / `"   "` = missing → default `text` | Must be `html` or `text` (case-insensitive), controls MIME subtype | `ValidationError` |
| `attachment` | At least one required | `b""` or `""` filename = missing | `bytes` len > 0, filename non-empty after strip, filename safe | `ValidationError` |
| Combination | — | — | If all of subject/body/attachment are missing/empty → fail | `ValidationError` |

Note: `to_address` is single email for v1. Bulk `list[str]` is considered for `send_bulk()` extension but not mandatory.

---

## 6. Exceptions

```python
class MailerError(Exception):  # base
    pass

class ConfigError(MailerError):
    """Raised at __init__ when config missing/invalid"""

class ValidationError(MailerError):
    """Raised at send() when caller input invalid (to, subject/body/attachment combo)"""

class SendError(MailerError):
    """Raised when provider transport fails (auth, network, timeout) — caller may retry"""
```

All errors use `raise`, never `return`. Provider's original exception chained via `raise SendError(...) from e`.

---

## 7. BaseMailer Interface

```python
from abc import ABC, abstractmethod

class BaseMailer(ABC):
    def __init__(self, config: MailerConfig):
        """Validate config, raise ConfigError if invalid"""

    @abstractmethod
    def send(self, request: EmailRequest) -> bool:
        """Send one email. Validates request via validator.py, normalizes body_type.
        Raises ValidationError/SendError, returns True on success."""

    # Optional extension (not mandatory for v1):
    # def send_bulk(self, requests: list[EmailRequest]) -> list[bool]: ...
```

- `SmtpMailer(BaseMailer)` and `BrevoMailer(BaseMailer)` share identical `send()` signature
- Caller swaps provider without changing call site: `mailer: BaseMailer = SmtpMailer(config)`

---

## 8. Logging & Env

### 8.1 Logging Points

- INFO: `Sending email to {to_address}`, `Email sent to {to_address}`
- WARNING: `Attachment large: {size} bytes`, `Config missing optional field`
- ERROR: `Validation failed for {to_address}: {reason}`, `Send failed: {error}`
- DEBUG: `Provider: smtp, host: {host}`, `Attachment: {filename} ({size}b)`

Logger via `logger.py` with `setup_logger(name, level)` pattern (same as `certgen`).

### 8.2 Environment Variables

```bash
MAILER_FROM_ADDRESS=noreply@event.com
MAILER_SMTP_HOST=smtp.gmail.com
MAILER_SMTP_PORT=587
MAILER_PASSWORD=app_password
MAILER_BREVO_API_KEY=xkeysib-...
MAILER_LOG_LEVEL=INFO
```

Loaded via `os.getenv`, never hardcoded. Follows `certgen` env pattern.

---

## 9. Architecture Notes

- No imports from `certgen` or `tracker` — standalone library
- File layout:
  ```
  mailer/
  ├── __init__.py      # re-exports BaseMailer, SmtpMailer, BrevoMailer, MailerConfig, EmailRequest, errors
  ├── base.py          # BaseMailer ABC
  ├── config.py        # MailerConfig dataclass
  ├── models.py        # EmailRequest dataclass (plain holder, no validation)
  ├── exceptions.py    # hierarchy above
  ├── validator.py     # validate_email, validate_attachment, validate_body_type, validate_combination
  ├── providers/smtp.py
  ├── providers/brevo.py
  ├── logger.py
  └── constants.py
  ```
- Thread safety: `send()` should not share mutable state; each call independent (same constraint as certgen)
