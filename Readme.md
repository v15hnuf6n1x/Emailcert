# Emailcert

A reusable, event-agnostic tool for generating certificates from a template and emailing them to participants — built as two independent modules (`certificate` and `mailer`) so each can be used standalone or wired into other systems later.

## Why

Built out of a real need: sending 300+ hackathon certificates as personalized PDFs via email. Instead of a one-off script, this is designed to be dropped into future events with a new template and config — no code changes needed for the common case.

## Features

- Generate certificates as PDFs from an HTML/CSS template with per-participant data (name, team, etc.)
- Read participant data from CSV/Excel
- Send certificates via email with attachments, pluggable across providers (SMTP, Brevo, etc.)
- Idempotent sending — tracks who's already been emailed, safe to re-run and retry failures
- Dry-run mode to generate and inspect PDFs before sending anything

## Architecture

Two independent modules, no cross-imports between them:

- **`certificate/`** — takes participant data + an HTML template, returns a rendered PDF. Knows nothing about email.
- **`mailer/`** — takes a recipient, subject, body, and attachment, sends it. Knows nothing about certificates. Provider-agnostic via a `BaseMailer` interface.
- **`orchestrator.py`** — the CLI glue: loads participants → generates certificates → sends emails → tracks status. This is the only piece that depends on both modules.

This split means either module can be imported directly into another system (e.g. a web backend) without pulling in the CLI or the tracking layer.

## Tech Stack

- Python
- Jinja2 + WeasyPrint — HTML template → PDF
- SMTP / Brevo — email sending (swappable)
- SQLite — send-status tracking
- Typer — CLI

## Usage

Each event gets its own template and config file — the core tool stays generic.

```
emailcert generate --config events/sparkverse.yaml --dry-run
emailcert send --config events/sparkverse.yaml --retry-failed
```

## Status

Work in progress — built for SPARKVERSE 2K26, designed to be reused for future events.

## License

MIT
