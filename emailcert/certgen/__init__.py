"""
Certificate generation module - public API export.
"""

from .config import TemplateConfig
from .constants import (
    DEFAULT_FONT_SIZE_NAME,
    DEFAULT_FONT_SIZE_TEAM,
    DEFAULT_OUTPUT_DIR,
    MAX_NAME_LENGTH,
    MAX_TEAM_LENGTH,
    MIN_TEMPLATE_HEIGHT,
    MIN_TEMPLATE_WIDTH,
)
from .exceptions import (
    CertificateError,
    InvalidParticipantError,
    InvalidParticipationError,
    LoaderError,
    OutputError,
    OverlayError,
    TemplateFormatError,
    TemplateNotFoundError,
)
from .loader import load_csv, load_excel, load_sparkverse, load_with_mapping
from .logger import setup_logger
from .models import Participant
from .renderer import generate, png_bytes_to_pdf, render_png, save_pdf

try:
    from .svg_renderer import render_svg  # type: ignore
except ImportError:
    render_svg = None  # type: ignore

__version__ = "0.1.0"
__author__ = "Naresh Kumar S"
__all__ = [
    "generate",
    "render_png",
    "render_svg",
    "png_bytes_to_pdf",
    "save_pdf",
    "load_csv",
    "load_excel",
    "load_sparkverse",
    "load_with_mapping",
    "Participant",
    "TemplateConfig",
    "CertificateError",
    "LoaderError",
    "TemplateNotFoundError",
    "TemplateFormatError",
    "OverlayError",
    "InvalidParticipantError",
    "InvalidParticipationError",
    "OutputError",
    "setup_logger",
]
