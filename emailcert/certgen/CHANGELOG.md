# Changelog - certgen

All notable changes to the `emailcert.certgen` module.

## [0.1.0] - 2026-09-02

### Added
- Core module: `models.py` `Participant` dataclass with strict validation (name/team 1-100 chars, pattern `^[a-zA-Z0-9\s\-]+$`, email contains @) + `team_name` alias for backward compatibility
- Configuration: `config.py` `TemplateConfig` with defaults (name_position `(800,350)`, team_position `(800,500)`, font sizes 60/40) + `team_name_position` alias + `from_env()` loading `CERT_*` vars
- Exceptions: `exceptions.py` hierarchy `CertificateError` -> `LoaderError`, `TemplateNotFoundError`, `TemplateFormatError`, `OverlayError`, `InvalidParticipantError`/`InvalidParticipationError` alias, `OutputError` (fixed `OutputError(Certificate)` bug)
- Constants: `constants.py` magic numbers and defaults + fallback font paths per OS
- Logger: `logger.py` `setup_logger(name, level)` with `CERT_LOG_LEVEL` env, deduplication, `LOG_FORMAT`
- Utils: `utils.py` `safe_filename`, `ensure_output_dir` with fallback, `get_template_format`, `validate_template`, `find_template` (4-level fallback), `load_font` (OS fallback -> PIL default), `validate_participant`, `strip_whitespace`
- Loader: `loader.py` `load_csv` (encoding fallback utf-8/utf-8-sig/latin-1) + `load_excel` (openpyxl) with strict column/null/empty checks, row-number errors, `team_name` alias
- Renderer: `renderer.py` `render_png` (PIL overlay, RGBA->RGB, `anchor="mm"` centering, size 800x600 check) + `generate` router (png/svg dispatch, output_dir override, re-validation)
- SVG: `svg_renderer.py` `render_svg` (ET parse, namespace handling, tspan clearing, cairosvg conversion, element id `name`/`team` replacement)
- Public API: `__init__.py` exports `generate`, `render_png`, `render_svg`, `load_csv`, `load_excel`, `Participant`, `TemplateConfig`, all exceptions, `setup_logger`; `__version__="0.1.0"`
- Env: `.env.example` + `example.env` with all `CERT_*` variables (output, template, font, color, SVG ids, log level, fallback paths)
- Tests: `tests/` 59 tests, 85% coverage (fixtures: template.png/svg, CSVs, XLSX), `test_models` `test_loader` `test_utils` `test_config` `test_renderer` `test_svg_renderer`
- Docs: `emailcert/certgen/README.md` with quickstart, SVG format, env vars, API, fallbacks; `plan.md` aligned

### Fixed
- `models.py` added missing `email` field and regex validation
- `config.py` fixed syntax error (`name_position:` without type)
- `exceptions.py` corrected `OutputError(CertificateError)` inheritance

### Technical
- Dependencies: pillow 12.3.0, pandas 3.0.5, openpyxl 3.1.5, cairosvg 2.9.0 (requires libcairo2)
- Python 3.12, type hints throughout, thread-unsafe by design (use ProcessPool)

### Known Out of Scope
- No PDF generation, email sending, certificate ID/date, tracking, web UI, concurrent processing (see plan.md:43)
