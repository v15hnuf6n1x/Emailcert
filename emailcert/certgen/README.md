# CertGen — Certificate Generator

Generate personalized certificates from a PNG/SVG template + spreadsheet. One participant → one PDF + PNG, centered on dash lines, ready to email.

> Built for **SPARKVERSE 2K26** (NPR College). Works for any future event — just swap template and sheet, no code change.

---

## Table of Contents
1. [What it does](#what-it-does)
2. [Project Structure](#project-structure)
3. [Prerequisites](#prerequisites)
4. [Installation](#installation)
5. [Configuration - Where to set what (`.env`)](#configuration)
6. [Quick Start - 3 Commands](#quick-start---3-commands)
7. [How to Test (1 Sample, No Sheet)](#how-to-test-1-sample-no-sheet)
8. [How to Test With Your Sheet (1 Column)](#how-to-test-with-your-sheet-1-column)
9. [How to Run Production (278 Certs)](#how-to-run-production-278-certs)
10. [Spreadsheet Format](#spreadsheet-format)
11. [Template](#template)
12. [Output](#output)
13. [Python API (If you want code)](#python-api)
14. [Troubleshooting](#troubleshooting)

---

## What it does

```
Spreadsheet (75 rows, Team + 4 names per row)
    ↓  loader.load_sparkverse()  [expands to 278 participants]
Participant(name="Alice Bob", team="Tech Hari")
    ↓  renderer.generate()  [PIL overlay at (X,Y) on PNG, centered]
PNG (2000x1414, 0.4s)  →  PDF (via png_bytes_to_pdf, 300 DPI)
    ↓
certificates/pdf/*.pdf  (for email)  +  certificates/png/*.png  (preview)
```

- **One-by-one, not batch** — ~10MB RAM, safe for 300+ certs (~2 min for 278).
- **Smart fallbacks:** font → OS fonts → PIL default; template path → `./` → `events/sparkverse/`; output dir → `certificates/`.
- **Strict validation:** name/team 1–100 chars (letters, numbers, space, `- . ' ( ) & / + ²`), email optional with `@`.

## Project Structure

```
Emailcert/
├── emailcert/certgen/src/cert-img.png   # Your clean template (2000x1414, RGB, no C2PA noise)
├── emailcert/certgen/src/sparkverse26-registrations-2026-08-31.csv.xlsx  # 75 teams → 278 participants
├── emailcert/certgen/fonts/DancingScript-Regular.ttf  # Cursive for name/team (you asked)
├── .env.example                         # All settings (copy to .env.local)
├── requirements.txt                     # pip deps
├── generate.py                          # Final run script (you use this)
├── emailcert/certgen/                   # Module (7 files, 85% tested)
└── certificates/pdf|png/                # Output (created on run)
```

## Prerequisites

- Python 3.8+
- System: `libcairo2` only if you use SVG templates (`sudo apt-get install libcairo2` on Ubuntu/Debian)

## Installation

```bash
# From Emailcert/ root
pip install -r requirements.txt
# Contains: pillow==12.3.0, pandas==3.0.5, openpyxl==3.1.5, cairosvg==2.9.0, python-dotenv==1.1.0
```

## Configuration

All settings are in **`.env.example`** — copy and edit, no code change for future events.

```bash
cp .env.example .env.local
nano .env.local
```

**What to set (you only need 4 lines for most events):**

| Setting | Where | Example | What it does |
|---------|-------|---------|--------------|
| **Template path** | `CERT_TEMPLATE_PATH` | `emailcert/certgen/src/cert-img.png` | Your PNG from Canva (white background, >800x600) |
| **Output folders** | `CERT_OUTPUT_PDF_DIR` / `CERT_OUTPUT_PNG_DIR` | `certificates/pdf` / `certificates/png` | PDFs separate from PNGs (as you requested) |
| **Team column** | `CERT_COL_TEAM` | `Team Name` | Header for team in your sheet |
| **Name columns** | `CERT_COL_NAMES` | `Leader Name,M1 Name,M2 Name,M3 Name` | Headers for participants (one cert per name, same team). For simple sheet use `name,team` and leave this empty — auto-detected. |
| **Positions** | `CERT_NAME_POS_X=1000` `Y=832`, `CERT_TEAM_POS_X=1000` `Y=921` | Center X=1000 (2000/2), Y 28px/25px above dashes at y=860/946 | If text not on dash after test, tweak ±10 and re-run |

Load in code via `TemplateConfig.from_env()`.

## Quick Start - 3 Commands

As you guessed — you were right:

```bash
cp .env.example .env.local   # 1. Set template, output, columns, positions (if needed)
pip install -r requirements.txt  # 2. Install
python generate.py --test        # 3a. Test: 1 cert (Kavin) → draft_test/
python generate.py               # 3b. Production: 278 certs → certificates/pdf+png/
```

## How to Test (1 Sample, No Sheet) — Easiest

No spreadsheet needed. Generates `Kavin / Sparkverse` with DancingScript to check dash alignment and no black noise.

```bash
python generate.py --test
# Output:
# [1/3] Loading participants... Test mode: 1 sample Kavin / Sparkverse
# [3/3] Generating 1 certificates... 1/1 Kavin -> png/kavin.png + pdf/kavin.pdf Done 1 in 0.5s
ls -lh draft_test/pdf/kavin.pdf draft_test/png/kavin.png
xdg-open draft_test/pdf/kavin.pdf   # check: text centered on dash lines?
xdg-open draft_test/png/kavin.png
# If slightly off, edit .env.local CERT_NAME_POS_Y=832 → 840 and re-run
```

## How to Test With Your Sheet (1 Column) — As You Said "Just PDF and PNG is Enough"

Upload your single-column test sheet to `src/` (e.g. `src/test.csv`):

```csv
name,team
Kavin,Sparkverse
Alice Bob,Tech Hari
```

Any header aliases work: `name`/`Full Name`, `team`/`team_name`/`Team Name`, `department`/`dept`, `year`/`year_of_study`.

```bash
# No flag needed now - auto-detects simple vs wide format
python generate.py --spreadsheet emailcert/certgen/src/test.csv --output draft_test
# Output: draft_test/pdf/kavin.pdf + png/kavin.png (separate dirs)
ls -lh draft_test/pdf/ draft_test/png/
```

## How to Run Production (278 Certs)

Uses your uploaded `src/sparkverse26-registrations-2026-08-31.csv.xlsx` (27 cols, 75 rows, wide-format). No code change - column mapping already in `.env.example`.

```bash
python generate.py
# [1/3] Loading ... 278 participants (wide-format: 75 teams -> 278)
# [3/3] Generating 278 certificates... 50/278 ... 278/278 Done 278 in ~122s
ls certificates/pdf/ | wc -l   # 278 PDFs
ls certificates/png/ | wc -l   # 278 PNGs
xdg-open certificates/pdf/derrick_lance_g.pdf
```

For a different future sheet, just change in `.env.local`:
```ini
CERT_COL_TEAM=Group
CERT_COL_NAMES=Student Name
```

Or use code: `load_with_mapping("future.csv", {"name": "Full Name", "team": "Team Name"})`.

## Spreadsheet Format

**For testing (simple):**
```csv
name,team
John Doe,Team Alpha      # one row = one certificate
```

**For production (Sparkverse wide):**
```
Team Name | Idea Title | Leader Name | Leader Dept | Leader Year | M1 Name | M1 Dept | M1 Year | M2 Name ... | M3 Name ...
AgriNex-AI | Aqua Crop | Derrick Lance. G | CSE | II | Kishor. R | CSE | II | J. Deepak Ram | ...
```
→ Expands to 4 participants per row (`Derrick Lance. G / AgriNex-AI`, `Kishor. R / AgriNex-AI`, ...). Empty `M3` skipped (53/75 have M3).

Rules: `name, team` required (1–100 chars, no `@` or `_`); `department, year, email` optional; no empty `name`/`team`; UTF-8/BOM.

## Template

- **Use PNG from Canva:** Share → Download → PNG, Large size, **white** background (not transparent), >800x600 (your `cert-img.png` is 2000x1414 RGB, 729KB, clean).
- **Place at:** `emailcert/certgen/src/cert-img.png` (or any path via `CERT_TEMPLATE_PATH` or `generate(p, "my.png", config)`). Fallback also checks `events/sparkverse/template.png`.
- **SVG alternative:** If you use SVG, ensure it has `<text id="name">` and `<text id="team">` or it will inject new text at `name_position`/`team_position` (now fixed to flatten white background, no black noise).

**Positions:** Dash lines detected at `y=860` (long, name) and `y=946` (short, team) for 1414 height. Text is `28px`/`25px` above. Current defaults `name(1000,832) team(1000,921)` are centered (`anchor mm`). Tweak `CERT_NAME_POS_X/Y` in `.env.local` if needed (grid helper at `/tmp/template_with_grid.png`).

**Font:** Default `arial.ttf` → `LiberationSans-Regular` → `PIL default`. For your dancing style, set `CERT_FONT_PATH=emailcert/certgen/fonts/DancingScript-Regular.ttf` (already used in `generate.py:31`).

## Output

```
certificates/
├── pdf/   # 278 PDFs, ~270KB each, 300 DPI, ready to email (separate as you requested)
│   ├── kavin.pdf
│   ├── alice_bob.pdf
│   └── ...
└── png/   # 278 PNGs, ~700KB each, preview
    ├── kavin.png
    └── ...
# For testing: draft_test/pdf|png/ (1 or 2 files)
```

PDFs are generated via `png_bytes_to_pdf()` (`PIL.Image.save, dpi=300`, flattened `RGBA`→`RGB` white).

## Python API

If you want to use in code (e.g. web backend) without `generate.py`:

```python
from emailcert.certgen import Participant, TemplateConfig, generate, load_csv
from emailcert.certgen.loader import load_sparkverse, load_with_mapping
from emailcert.certgen.renderer import png_bytes_to_pdf

# Simple
participants = load_csv("participants.csv")  # or load_excel, load_sparkverse("sparkverse.xlsx")

# Custom mapping for future sheet
participants = load_with_mapping("future.csv", {"name": "Full Name", "team": "Group"})

# Or via .env
config = TemplateConfig.from_env()  # reads CERT_*

# Manual
p = Participant(name="Kavin", team="Sparkverse", department="CSE", year="2nd Year")  # dept/year optional
config = TemplateConfig(name_position=(1000,832), team_position=(1000,921), output_dir="certificates/png")
png_bytes, png_path = generate(p, "emailcert/certgen/src/cert-img.png", config)
pdf_bytes = png_bytes_to_pdf(png_bytes)
open(f"certificates/pdf/{p.name}.pdf", "wb").write(pdf_bytes)
```

**Exceptions:** `CertificateError` → `LoaderError` (CSV missing cols), `TemplateNotFoundError`, `TemplateFormatError` (too small), `OverlayError`, `InvalidParticipantError`, `OutputError`.

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `LoaderError: Missing required columns` | Check header spelling case-sensitive. Set `CERT_COL_TEAM`/`CERT_COL_NAMES` in `.env.local` to match your sheet. |
| Text not on dash lines | Edit `.env.local` `CERT_NAME_POS_Y=832` → `840` (±10) and re-run `--test`. |
| Black noise / speckles | Use PNG template (`cert-img.png`), not SVG with embedded image. Ensure `src/template.png` is `RGB` not `L`/`RGBA` (we now convert `L`→`RGB`). |
| Font jagged / not dancing | Ensure `CERT_FONT_PATH=emailcert/certgen/fonts/DancingScript-Regular.ttf` exists; fallback is `LiberationSans`. |
| `Template too small` | PNG must be >800x600 (`cert-img.png` is 2000x1414). |
| Slow (3s per cert) | Use PNG direct (`render_png`, 0.4s) not SVG (`render_svg` via `cairosvg`, 3s). Default now is PNG. |

## Automated Tests

```bash
pytest tests -v --cov=emailcert.certgen  # 85% coverage, 61 tests (includes wide-format 278)
```

## Logging

```python
from emailcert.certgen.logger import setup_logger
logger = setup_logger(__name__, "DEBUG")  # or set CERT_LOG_LEVEL=DEBUG in .env
```

---

**You were right on flow:** `1. .env` → `2. requirements` → `3. generate.py` (with `--test` for one sample, without for production). Testing is now `1 command` (`--test`) vs production `1 command` (no flag), both auto-handle simple and wide sheets.
