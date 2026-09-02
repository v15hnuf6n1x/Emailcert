#!/usr/bin/env python3
"""
Final run script for Sparkverse 2K26 certificates (278 participants).
Uses: src/sparkverse26-registrations-2026-08-31.csv.xlsx -> src/cert-img.png (2000x1414) -> certificates/*.pdf
Run: pip install -r requirements.txt && PYTHONPATH=. python generate.py
Or: python generate.py --help
"""
import argparse
import os
import time
from pathlib import Path

# Ensure Emailcert is on path when run as `python generate.py` from Emailcert/
import sys
sys.path.insert(0, str(Path(__file__).parent))

from emailcert.certgen import TemplateConfig
from emailcert.certgen.loader import load_sparkverse
from emailcert.certgen.renderer import png_bytes_to_pdf, save_pdf
from emailcert.certgen.utils import safe_filename

DEFAULT_TEMPLATE = "emailcert/certgen/src/cert-img.png"
DEFAULT_SPREADSHEET = "emailcert/certgen/src/sparkverse26-registrations-2026-08-31.csv.xlsx"
DEFAULT_OUTPUT = "certificates"

def main():
    parser = argparse.ArgumentParser(description="Generate Sparkverse certificates (PNG+PDF)")
    parser.add_argument("--template", default=DEFAULT_TEMPLATE, help="Path to cert-img.png")
    parser.add_argument("--spreadsheet", default=DEFAULT_SPREADSHEET, help="Path to .xlsx/.csv (ignored with --test)")
    parser.add_argument("--output", default=DEFAULT_OUTPUT, help="Base output dir (will create pdf/ and png/ subdirs)")
    parser.add_argument("--font", default="emailcert/certgen/fonts/DancingScript-Regular.ttf", help="Font path")
    parser.add_argument("--test", action="store_true", help="Easy test: generate one sample cert (Kavin/Sparkverse) without spreadsheet, to draft_test/")
    parser.add_argument("--single-column-test", action="store_true", help="(Deprecated) Use --test or just provide simple CSV; auto-detected now")
    args = parser.parse_args()

    # 1. Load - easy test vs auto-detect
    print(f"[1/3] Loading participants...")
    if args.test:
        # Easiest test - no spreadsheet needed, generates Kavin / Sparkverse
        from emailcert.certgen import Participant
        participants = [Participant(name="Kavin", team="Sparkverse")]
        print(f"  Test mode: 1 sample participant Kavin / Sparkverse (no spreadsheet)")
        # Override output for test to draft_test for quick preview
        if args.output == DEFAULT_OUTPUT:
            args.output = "draft_test"
            print(f"  Output auto-switched to {args.output}/ for test")
    elif args.single_column_test:
        # Backward compat: explicit simple mode
        from emailcert.certgen.loader import load_csv, load_excel
        if args.spreadsheet.lower().endswith(".csv"):
            participants = load_csv(args.spreadsheet)
        else:
            participants = load_excel(args.spreadsheet)
        print(f"  Loaded {len(participants)} participants (simple mode: one row = one cert)")
    else:
        # Auto-detect: try simple first (name,team), then wide-format (Team Name + Leader/M1/M2/M3)
        participants = None
        # Try simple CSV/Excel (one row per participant)
        try:
            from emailcert.certgen.loader import load_csv, load_excel
            if args.spreadsheet.lower().endswith(".csv"):
                participants = load_csv(args.spreadsheet)
            else:
                participants = load_excel(args.spreadsheet)
            print(f"  Loaded {len(participants)} participants (auto: simple mode)")
        except Exception as e_simple:
            # Fallback to wide-format sparkverse
            try:
                participants = load_sparkverse(args.spreadsheet)
                print(f"  Loaded {len(participants)} participants (auto: wide-format 75 teams -> {len(participants)}) (e.g. {participants[0].name} / {participants[0].team})")
            except Exception as e_wide:
                print(f"  Failed simple mode: {e_simple}")
                print(f"  Failed wide mode: {e_wide}")
                print(f"  Hint: Check .env.example CERT_COL_TEAM/NAMES or use --test for quick test")
                return
        if len(participants) == 0:
            print("  WARNING: No participants found - check column names in .env.example")
    if not participants:
        print("  No participants to generate - exiting")
        return

    # 2. Config - dash lines for cert-img.png 2000x1414: name at 832, team at 921, center 1000
    # For production, PDFs and PNGs go to separate subdirectories as requested
    pdf_dir = os.path.join(args.output, "pdf")
    png_dir = os.path.join(args.output, "png")
    # Allow override via .env: CERT_OUTPUT_PDF_DIR / CERT_OUTPUT_PNG_DIR
    pdf_dir = os.getenv("CERT_OUTPUT_PDF_DIR", pdf_dir)
    png_dir = os.getenv("CERT_OUTPUT_PNG_DIR", png_dir)

    config_png = TemplateConfig(
        name_position=(1000, 832),
        team_position=(1000, 921),
        font_path=args.font,
        font_size_name=56,
        font_size_team=48,
        output_dir=png_dir,
        text_color=(0, 0, 0),
        center_text=True,
    )
    os.makedirs(pdf_dir, exist_ok=True)
    os.makedirs(png_dir, exist_ok=True)
    print(f"[2/3] Template {args.template}")
    print(f"  PNG -> {png_dir}/  PDF -> {pdf_dir}/")
    print(f"  Positions name{config_png.name_position} team{config_png.team_position} font {args.font}")

    # 3. Generate one-by-one
    print(f"[3/3] Generating {len(participants)} certificates...")
    start = time.time()
    from emailcert.certgen.renderer import generate
    for i, p in enumerate(participants, 1):
        # Generate PNG to png_dir
        png_bytes, png_path = generate(p, args.template, config_png)
        # Convert and save PDF to pdf_dir (separate as requested)
        pdf_bytes = png_bytes_to_pdf(png_bytes)
        pdf_path = os.path.join(pdf_dir, f"{safe_filename(p.name)}.pdf")
        save_pdf(pdf_bytes, pdf_path)
        if i % 50 == 0 or i == len(participants) or i <= 3:
            print(f"  {i}/{len(participants)} {p.name} -> png/{safe_filename(p.name)}.png + pdf/{safe_filename(p.name)}.pdf")

    elapsed = time.time() - start
    print(f"Done {len(participants)} in {elapsed:.1f}s (~{elapsed/len(participants):.2f}s per cert)")
    print(f"Output PNG: {png_dir}/ ({len(os.listdir(png_dir))} files)")
    print(f"Output PDF: {pdf_dir}/ ({len(os.listdir(pdf_dir))} files)")
    print(f"Preview: xdg-open {pdf_dir}/{safe_filename(participants[0].name)}.pdf")

if __name__ == "__main__":
    main()
