"""
Constants for certificate generation module.
"""

# Data constraints
MAX_NAME_LENGTH = 100
MAX_TEAM_LENGTH = 100
MAX_DEPARTMENT_LENGTH = 100
MAX_YEAR_LENGTH = 20
MIN_NAME_LENGTH = 1
MIN_TEAM_LENGTH = 1
MIN_DEPARTMENT_LENGTH = 1
MIN_YEAR_LENGTH = 1
PATTERN_NAME_TEAM = r"^[a-zA-Z0-9\s\-\.\'\(\)\&\/\+\²]+$"
PATTERN_DEPARTMENT = r"^[a-zA-Z0-9\s\-\.\(\)\&\/\+]+$"
PATTERN_YEAR = r"^[a-zA-Z0-9\s\-\/\+]+$"

# Font defaults
DEFAULT_FONT_SIZE_NAME = 60
DEFAULT_FONT_SIZE_TEAM = 40
DEFAULT_FONT_PATH = "arial.ttf"
SUPPORTED_FONTS = ["arial.ttf", "calibri.ttf", "verdana.ttf"]

# Image defaults
DEFAULT_PNG_QUALITY = 95
MIN_TEMPLATE_WIDTH = 800
MIN_TEMPLATE_HEIGHT = 600
SUPPORTED_FORMATS = ["png", "svg"]

# File operations
DEFAULT_OUTPUT_DIR = "certificates"
SUPPORTED_CSV_ENCODINGS = ["utf-8", "utf-8-sig", "latin-1"]

# Logging
DEFAULT_LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Template positioning defaults
# Updated for src/final.svg template 2172x724 (extracted PNG) and 1500x1060 viewBox
# Center X = 1086 (2172/2) or 750 (1500/2) - defaults use 750 for viewBox, will scale
DEFAULT_NAME_POSITION = (1086, 320)
DEFAULT_TEAM_POSITION = (1086, 400)
DEFAULT_DEPARTMENT_POSITION = (1086, 480)
DEFAULT_YEAR_POSITION = (1086, 560)
DEFAULT_TEXT_COLOR = (0, 0, 0)
DEFAULT_CENTER_TEXT = True
DEFAULT_TEMPLATE_FORMAT = "png"

# Font sizes for new fields
DEFAULT_FONT_SIZE_DEPARTMENT = 36
DEFAULT_FONT_SIZE_YEAR = 32

# SVG defaults
DEFAULT_SVG_NAME_ELEMENT_ID = "name"
DEFAULT_SVG_TEAM_ELEMENT_ID = "team"
DEFAULT_SVG_DEPARTMENT_ELEMENT_ID = "department"
DEFAULT_SVG_YEAR_ELEMENT_ID = "year"

# Fallback paths
FALLBACK_FONT_PATHS_LINUX = [
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
]

FALLBACK_FONT_PATHS_WINDOWS = [
    "C:\\Windows\\Fonts\\arial.ttf",
    "arial.ttf",
]

FALLBACK_FONT_PATHS_MACOS = [
    "/Library/Fonts/Arial.ttf",
    "/System/Library/Fonts/Arial.ttf",
    "/System/Library/Fonts/Supplemental/Arial.ttf",
]
