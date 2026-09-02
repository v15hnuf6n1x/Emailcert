# Certificate Generation Module - Final Development Plan

**Project:** emailcert  
**Module:** certgen (certificate generation)  
**Author:** Naresh Kumar S  
**Status:** Ready to Code  
**Version:** 1.0 (Planning)  
**Last Updated:** 2026-09-01

---

## EXECUTIVE SUMMARY

Build a reusable, production-grade Python module to generate personalized certificates by overlaying participant data on design templates (PNG/SVG). The module will be thread-unsafe for concurrent access, implement smart fallback strategies, include comprehensive logging, and strict input validation.

**Key Metrics:**
- 248 certificates in ~2 minutes (one-by-one processing)
- 80%+ test coverage
- Zero type errors (mypy)
- Production logging at every step

---

## 1. PROJECT OVERVIEW

### 1.1 Purpose
Generate personalized certificates from Canva templates (PNG/SVG) by overlaying participant names and teams via Python API.

### 1.2 Core Features
- ✅ Read CSV/Excel with participant data
- ✅ Support PNG templates (PIL overlay)
- ✅ Support SVG templates (XML manipulation)
- ✅ Overlay name + team on template
- ✅ Save to output directory
- ✅ One-by-one processing (memory efficient)
- ✅ Return certificate bytes (email-ready)
- ✅ Comprehensive logging for debugging
- ✅ Input validation with specific rules
- ✅ Smart fallback strategies (font, directory, files)
- ✅ Environment variable configuration
- ✅ Type hints on all functions

### 1.3 Out of Scope
- ❌ Certificate ID field
- ❌ Date/signature fields
- ❌ PDF generation
- ❌ Email sending
- ❌ Certificate tracking
- ❌ Web UI
- ❌ Concurrent processing (not thread-safe)

---

## 2. REQUIREMENTS

### 2.1 Input Requirements

**Template Support:**
- PNG (Canva export) - Default
- SVG (Canva export) - New feature

**Spreadsheet Format:**
- CSV (.csv) - Primary
- Excel (.xlsx) - Secondary
- Required columns: `name`, `team`, `email`
- No null values allowed
- Encoded as UTF-8 or UTF-8-BOM

**Participant Data Rules:**
- Name: 1-100 characters, non-empty, alphanumeric + spaces/hyphens
- Team: 1-100 characters, non-empty, alphanumeric + spaces/hyphens
- Email: Must contain @, non-empty (basic validation)

### 2.2 Template Requirements

**PNG Template:**
- Format: PNG (24-bit RGB or 32-bit RGBA)
- Minimum size: 800x600px
- Recommended: 1920x1080px or larger
- Text overlay positions: User-specified (X, Y coordinates)

**SVG Template:**
- Format: SVG (XML)
- Must contain text elements or editable areas
- User specifies which elements to replace (by ID or class)
- Example: `<text id="name">{{ name }}</text>`

### 2.3 Output Requirements

**Format:** PNG (RGB, 8-bit) for both PNG/SVG input  
**Location:** Configurable output directory  
**Naming:** `{safe_filename}.png`  
**File Permissions:** Must be readable  
**Quality:** 95 DPI (PIL default)

### 2.4 Processing Model

**Mode:** One-by-one (streaming, not batch)  
**Memory:** Minimal (~10MB template cached)  
**Error Handling:** Skip failed, log, continue  
**Return:** Tuple[bytes, str] (PNG bytes + file path)

---

## 3. ARCHITECTURE

### 3.1 Module Structure

```
emailcert/
│
├── modules/
│   └── certgen/                    # Certificate generation module
│       ├── __init__.py             # Public API export
│       ├── models.py               # Data structures (Participant)
│       ├── config.py               # Configuration (TemplateConfig)
│       ├── loader.py               # CSV/Excel loading
│       ├── renderer.py             # PNG overlay logic
│       ├── svg_renderer.py         # SVG manipulation (NEW)
│       ├── utils.py                # Helper functions
│       ├── exceptions.py           # Custom exceptions
│       ├── constants.py            # Magic numbers & defaults
│       └── logger.py               # Logging setup
│
├── events/
│   └── sparkverse/
│       ├── template.png
│       ├── template.svg            # NEW
│       ├── participants.csv
│       └── config.yaml
│
├── certificates/                   # Output folder
├── tests/                          # Unit tests
├── .env.example
├── .env.local
├── pyproject.toml                  # Package metadata
├── requirements.txt
├── requirements-dev.txt            # Dev tools
├── PLAN.md                         # This file
├── CHANGELOG.md                    # Version history
└── README.md

```

### 3.2 Component Responsibilities

| Component | Input | Output | Priority |
|-----------|-------|--------|----------|
| **models.py** | — | Participant class | 🔴 CRITICAL |
| **config.py** | — | TemplateConfig class | 🔴 CRITICAL |
| **loader.py** | CSV/Excel path | List[Participant] | 🔴 CRITICAL |
| **renderer.py** | Participant + PNG path | bytes, str | 🔴 CRITICAL |
| **svg_renderer.py** | Participant + SVG path | bytes, str | 🟠 HIGH |
| **utils.py** | Data | Validated data | 🟠 HIGH |
| **exceptions.py** | — | Exception classes | 🟠 HIGH |
| **constants.py** | — | Constants | 🟡 MEDIUM |
| **logger.py** | — | Logger setup | 🟡 MEDIUM |

### 3.3 Data Flow

```
Input Files:
├── participants.csv (name, team, email)
└── template.png OR template.svg

Step 1: LOAD
├── loader.load_csv/load_excel()
├── Validate columns exist
├── Validate no null values
├── Create Participant objects
└── Return: List[Participant]

Step 2: FOR EACH PARTICIPANT
├── Validate participant data (name, team length)
├── Check template exists
├── Route to PNG or SVG renderer
├── Render certificate
├── Save to output_dir
└── Return: (bytes, file_path)

Step 3: FALLBACK ON ERROR (if template not found)
├── Try original path
├── Try relative path
├── Try events/sparkverse/
├── If all fail: Raise TemplateNotFoundError

Step 4: FALLBACK ON FONT MISSING
├── Try arial.ttf (Windows)
├── Try Arial.ttf (macOS)
├── Try /usr/share/fonts/liberation/LiberationSans-Regular.ttf (Linux)
├── Fall back to PIL default font
├── Log warning

Output:
└── certificates/ (PNG files)
    ├── john_doe.png
    ├── jane_smith.png
    └── ...
```

---

## 4. DETAILED SPECIFICATIONS

### 4.1 Data Models

**Participant Dataclass:**
```python
@dataclass
class Participant:
    name: str       # 1-100 chars, alphanumeric + spaces/hyphens
    team: str       # 1-100 chars, alphanumeric + spaces/hyphens
    email: str      # Must contain @
    
    # Validation: __post_init__
    # - name: non-empty, max 100 chars
    # - team: non-empty, max 100 chars
    # - email: non-empty, contains @
```

### 4.2 Configuration

**TemplateConfig Dataclass:**
```python
@dataclass
class TemplateConfig:
    # Text positioning (X, Y from top-left)
    name_position: Tuple[int, int] = (800, 350)
    team_position: Tuple[int, int] = (800, 500)
    
    # Font settings
    font_path: str = "arial.ttf"
    font_size_name: int = 60
    font_size_team: int = 40
    
    # Text appearance
    text_color: Tuple[int, int, int] = (0, 0, 0)  # RGB black
    center_text: bool = True  # mm anchor = middle-middle
    
    # Output settings
    output_dir: str = "certificates"
    template_format: str = "png"  # "png" or "svg"
    quality: int = 95
    
    # SVG-specific
    svg_name_element_id: str = "name"    # Element to replace
    svg_team_element_id: str = "team"    # Element to replace
```

---

## 5. TYPE HINTS & SIGNATURES

### 5.1 Public API Functions

```python
# Loader functions
def load_csv(
    filepath: str,
    encoding: str = "utf-8"
) -> List[Participant]:
    """Load participants from CSV file."""

def load_excel(
    filepath: str,
    sheet_name: str = 0
) -> List[Participant]:
    """Load participants from Excel file."""

# Main generator
def generate(
    participant: Participant,
    template_path: str,
    config: Optional[TemplateConfig] = None,
    output_dir: Optional[str] = None
) -> Tuple[bytes, str]:
    """
    Generate certificate.
    
    Returns:
        Tuple[PNG bytes, file path]
    
    Raises:
        TemplateNotFoundError
        OverlayError
        InvalidParticipantError
    """

# Renderers
def render_png(
    participant: Participant,
    template_path: str,
    config: TemplateConfig
) -> Tuple[bytes, str]:
    """Overlay text on PNG template."""

def render_svg(
    participant: Participant,
    template_path: str,
    config: TemplateConfig
) -> Tuple[bytes, str]:
    """Replace text elements in SVG, export as PNG."""

# Utils (for internal use)
def validate_participant(p: Participant) -> bool:
    """Validate name, team, email rules."""

def safe_filename(name: str) -> str:
    """Convert name to valid filename."""

def ensure_output_dir(path: str) -> None:
    """Create directory if missing."""
```

---

## 6. LOGGING STRATEGY

### 6.1 Logging Setup

```python
# logger.py
import logging

def setup_logger(name: str, level: str = "INFO") -> logging.Logger:
    """Configure logger for module."""
    logger = logging.getLogger(name)
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(level)
    return logger
```

### 6.2 Logging Points

**INFO Level (Normal operation):**
```
logger.info(f"Generated certificate for {participant.name}")
logger.info(f"Loaded {len(participants)} participants from {filepath}")
logger.info(f"Saved to {output_path}")
```

**DEBUG Level (Detailed debugging):**
```
logger.debug(f"Template loaded: {template_path}")
logger.debug(f"Font loaded: {font_path}")
logger.debug(f"Position: name={config.name_position}, team={config.team_position}")
logger.debug(f"Overlay completed in {elapsed_time}ms")
```

**WARNING Level (Recoverable issues):**
```
logger.warning(f"Font {font_path} not found, using fallback")
logger.warning(f"Output directory created: {output_dir}")
logger.warning(f"Participant email invalid, may fail at send: {email}")
```

**ERROR Level (Failed operations):**
```
logger.error(f"Template not found: {template_path}")
logger.error(f"Failed to overlay text: {error}")
logger.error(f"Invalid participant data: {participant}")
```

### 6.3 Environment Variable for Log Level

```bash
# .env
CERT_LOG_LEVEL=INFO  # INFO, DEBUG, WARNING, ERROR
```

---

## 7. INPUT VALIDATION RULES

### 7.1 Participant Validation

```python
# Field Rules
PARTICIPANT_RULES = {
    "name": {
        "min_length": 1,
        "max_length": 100,
        "pattern": r"^[a-zA-Z0-9\s\-]+$",  # alphanumeric, space, hyphen
        "required": True,
        "error": "Name must be 1-100 chars, alphanumeric/space/hyphen"
    },
    "team": {
        "min_length": 1,
        "max_length": 100,
        "pattern": r"^[a-zA-Z0-9\s\-]+$",
        "required": True,
        "error": "Team must be 1-100 chars, alphanumeric/space/hyphen"
    },
    "email": {
        "required": True,
        "pattern": r"^.+@.+$",  # Basic: must contain @
        "error": "Email must contain @"
    }
}
```

### 7.2 Template Validation

```python
# PNG Template
- Must exist (FileNotFoundError if not)
- Must be valid PNG (PIL can open it)
- Min size: 800x600px
- Must be RGB or RGBA

# SVG Template
- Must exist
- Must be valid XML
- Must contain elements to replace (IDs specified in config)
```

### 7.3 CSV/Excel Validation

```python
# Before processing
- File must exist
- Must have columns: name, team, email (EXACT case)
- No null values in these columns
- Encoding: UTF-8 or UTF-8-BOM

# Per row
- Apply Participant validation rules
- Raise LoaderError with row number on failure
```

### 7.4 Validation Flow

```python
def validate_participant(p: Participant) -> None:
    """Validate or raise InvalidParticipantError"""
    errors = []
    
    if not (1 <= len(p.name) <= 100):
        errors.append("Name length invalid")
    
    if not re.match(r"^[a-zA-Z0-9\s\-]+$", p.name):
        errors.append("Name has invalid characters")
    
    if not ("@" in p.email):
        errors.append("Email must contain @")
    
    if errors:
        raise InvalidParticipantError(f"Validation failed: {errors}")
```

---

## 8. ENVIRONMENT VARIABLES

### 8.1 Configuration via Environment

```bash
# .env.example

# Certificate settings
CERT_OUTPUT_DIR=certificates
CERT_TEMPLATE_FORMAT=png              # png or svg
CERT_FONT_PATH=arial.ttf
CERT_FONT_SIZE_NAME=60
CERT_FONT_SIZE_TEAM=40
CERT_TEXT_COLOR_R=0
CERT_TEXT_COLOR_G=0
CERT_TEXT_COLOR_B=0
CERT_QUALITY=95

# SVG settings
CERT_SVG_NAME_ELEMENT_ID=name
CERT_SVG_TEAM_ELEMENT_ID=team

# Logging
CERT_LOG_LEVEL=INFO                   # INFO, DEBUG, WARNING, ERROR

# Fallback paths
CERT_FALLBACK_FONT_PATHS=/usr/share/fonts/liberation/LiberationSans-Regular.ttf
```

### 8.2 Loading Environment Variables

```python
import os
from dotenv import load_dotenv

load_dotenv(".env.local")  # Local overrides

output_dir = os.getenv("CERT_OUTPUT_DIR", "certificates")
log_level = os.getenv("CERT_LOG_LEVEL", "INFO")
font_path = os.getenv("CERT_FONT_PATH", "arial.ttf")
```

---

## 9. THREAD SAFETY EXPLANATION 🔴

### 9.1 Is Module Thread-Safe?

**Answer: NO, NOT thread-safe for concurrent certificate generation**

### 9.2 Why Not Thread-Safe?

**Reason 1: PIL Image Objects**
```python
# PIL Images are NOT thread-safe
img = Image.open("template.png")  # Shared state
draw = ImageDraw.Draw(img)         # This modifies img

# If 2 threads use same img object → corruption
# Solution: Each thread must load its own template copy
```

**Reason 2: File I/O**
```python
# File system has limit on concurrent writes
# If threads write to same output_dir simultaneously → potential issues
# Solution: Use thread-safe queue or separate threads with different output dirs
```

**Reason 3: Shared Mutable State**
```python
# If config object is shared and modified → race condition
# Solution: Each call gets its own TemplateConfig object
```

### 9.3 What Happens If You Use Multiple Threads?

```python
# WRONG - Will cause issues:
from concurrent.futures import ThreadPoolExecutor

executor = ThreadPoolExecutor(max_workers=4)
for p in participants:
    executor.submit(generate, p, "template.png")
    # ERROR: PIL Image corruption, file write conflicts
```

**Result:** Corrupted images, file errors, crashes

### 9.4 How to Process Concurrently

**Option 1: Use Process Pool (SAFE)**
```python
from multiprocessing import Pool

with Pool(4) as pool:
    results = pool.starmap(generate, 
        [(p, "template.png") for p in participants])
    # SAFE: Each process has its own Python interpreter
```

**Option 2: Use AsyncIO (with thread pool for I/O only)**
```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

# Process 1 thread at a time, async wait for I/O
async def process_async(participants):
    executor = ThreadPoolExecutor(max_workers=1)
    loop = asyncio.get_event_loop()
    for p in participants:
        await loop.run_in_executor(executor, generate, p, "template.png")
```

**Option 3: Sequential Processing (SAFEST)**
```python
# One certificate at a time (original design)
for p in participants:
    cert_bytes, path = generate(p, "template.png")
    # ~2 min for 248 certs (acceptable)
```

### 9.5 Documentation

**Add to PLAN.md:**
```
THREAD SAFETY: NOT THREAD-SAFE

This module is NOT safe for concurrent use.

DO NOT use:
- ThreadPoolExecutor
- Threading with shared config
- AsyncIO with multiple threads

DO use:
- multiprocessing.Pool (process pool)
- Sequential processing (for loop)
- One generate() call at a time per thread

If you need concurrent processing:
1. Use ProcessPoolExecutor instead of ThreadPoolExecutor
2. Or: Process sequentially (2 min for 248 certs is acceptable)
```

---

## 10. FALLBACK STRATEGIES EXPLANATION 🔴

### 10.1 Font Loading Fallback

**Problem:** User's system might not have arial.ttf

**Fallback Chain:**
```python
def load_font(font_name: str, size: int) -> ImageFont.FreeTypeFont:
    """Load font with smart fallbacks."""
    
    # Step 1: Try exact path from config
    paths = [
        font_name,  # User's font_path
    ]
    
    # Step 2: Add platform-specific paths
    if sys.platform == "win32":
        paths.extend([
            "C:\\Windows\\Fonts\\arial.ttf",
            "arial.ttf",
        ])
    elif sys.platform == "darwin":  # macOS
        paths.extend([
            "/Library/Fonts/Arial.ttf",
            "/System/Library/Fonts/Arial.ttf",
        ])
    else:  # Linux
        paths.extend([
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "arial.ttf",
        ])
    
    # Step 3: Try each path
    for font_path in paths:
        try:
            logger.debug(f"Trying font: {font_path}")
            return ImageFont.truetype(font_path, size)
        except (OSError, IOError):
            logger.debug(f"Font not found: {font_path}")
            continue
    
    # Step 4: Fall back to PIL default
    logger.warning("No TrueType fonts found, using PIL default font")
    return ImageFont.load_default()
```

**Fallback Hierarchy:**
```
1. arial.ttf (user config)          ← Try first
2. Windows: C:\Windows\Fonts\       ← Windows specific
3. macOS: /Library/Fonts/           ← macOS specific
4. Linux: /usr/share/fonts/         ← Linux specific
5. PIL default font                 ← Last resort
```

### 10.2 Template Path Fallback

**Problem:** User might provide wrong path

**Fallback Chain:**
```python
def find_template(template_path: str, campaign_name: str = None) -> str:
    """Find template with fallbacks."""
    
    # Step 1: Try exact path
    if os.path.exists(template_path):
        logger.info(f"Template found: {template_path}")
        return template_path
    
    logger.debug(f"Template not at {template_path}, trying fallbacks...")
    
    # Step 2: Try current directory
    if os.path.exists(f"./{template_path}"):
        return f"./{template_path}"
    
    # Step 3: Try events/campaign/ folder
    if campaign_name:
        fallback_path = f"events/{campaign_name}/{os.path.basename(template_path)}"
        if os.path.exists(fallback_path):
            logger.info(f"Template found in events: {fallback_path}")
            return fallback_path
    
    # Step 4: Try events/sparkverse/ (default)
    default_fallback = f"events/sparkverse/{os.path.basename(template_path)}"
    if os.path.exists(default_fallback):
        logger.info(f"Template found at default: {default_fallback}")
        return default_fallback
    
    # Step 5: All failed
    logger.error(f"Template not found: {template_path}")
    raise TemplateNotFoundError(
        f"Template {template_path} not found in any expected location"
    )
```

**Fallback Hierarchy:**
```
1. Exact path (user provided)           ← Try first
2. Current directory (./)               ← Local
3. events/{campaign}/                   ← Campaign folder
4. events/sparkverse/                   ← Default
5. Raise error                          ← No more options
```

### 10.3 Output Directory Fallback

**Problem:** Output directory might not exist

**Strategy:**
```python
def ensure_output_dir(output_dir: str) -> None:
    """Create output directory, with fallbacks."""
    
    try:
        # Step 1: Try to create as specified
        os.makedirs(output_dir, exist_ok=True)
        logger.info(f"Output directory ready: {output_dir}")
        return
    except PermissionError:
        logger.warning(f"No permission for {output_dir}, using fallback")
    except Exception as e:
        logger.warning(f"Cannot create {output_dir}: {e}, using fallback")
    
    # Step 2: Fall back to current directory
    fallback_dir = "certificates"
    try:
        os.makedirs(fallback_dir, exist_ok=True)
        logger.warning(f"Using fallback directory: {fallback_dir}")
        return fallback_dir
    except Exception as e:
        logger.error(f"Cannot create fallback directory: {e}")
        raise
```

**Fallback Hierarchy:**
```
1. User-specified directory             ← Try first
2. "certificates/" (current dir)        ← Fallback
3. Raise error                          ← Both failed
```

### 10.4 Complete Fallback Example

```python
# User calls:
generate(participant, "template.png", output_dir="/custom/path")

# Fallback execution:

# 1. FIND TEMPLATE
   ✗ /custom/path/template.png (absolute path)
   ✗ ./template.png (current dir)
   ✗ events/sparkverse/template.png (campaign default)
   ✓ Raises TemplateNotFoundError

# 2. LOAD FONT
   ✗ arial.ttf (Windows font dir)
   ✗ /Library/Fonts/Arial.ttf (macOS)
   ✓ /usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf (Linux)

# 3. CREATE OUTPUT DIR
   ✗ /custom/path/ (permission denied)
   ✓ certificates/ (current directory)
```

---

## 11. UTILITIES FUNCTIONS

### 11.1 What Goes in utils.py

```python
def validate_participant(name: str, team: str, email: str) -> None:
    """Validate participant data, raise on error."""

def safe_filename(name: str) -> str:
    """Convert name to safe filename."""
    # "John Doe" → "john_doe"
    # "Jane-Smith" → "jane_smith"
    # "José García" → "jose_garcia"

def ensure_output_dir(path: str) -> str:
    """Create directory if missing, return path."""

def validate_template(template_path: str) -> bool:
    """Check if template exists and is valid."""

def get_template_format(template_path: str) -> str:
    """Return 'png' or 'svg' based on extension."""

def strip_whitespace(df: DataFrame) -> DataFrame:
    """Remove leading/trailing spaces from CSV data."""
```

---

## 12. CONSTANTS

### 12.1 Define in constants.py or config.py

```python
# Data constraints
MAX_NAME_LENGTH = 100
MAX_TEAM_LENGTH = 100
MIN_NAME_LENGTH = 1
MIN_TEAM_LENGTH = 1

# Font defaults
DEFAULT_FONT_SIZE_NAME = 60
DEFAULT_FONT_SIZE_TEAM = 40
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
```

---

## 13. SVG SUPPORT SPECIFICATION

### 13.1 SVG Template Format

```xml
<!-- template.svg - Canva export -->
<svg width="1920" height="1080">
    <rect width="1920" height="1080" fill="white"/>
    
    <!-- Name field (will be replaced) -->
    <text id="name" x="960" y="350" font-size="60" text-anchor="middle">
        {{ name }}
    </text>
    
    <!-- Team field (will be replaced) -->
    <text id="team" x="960" y="500" font-size="40" text-anchor="middle">
        {{ team }}
    </text>
</svg>
```

### 13.2 SVG Rendering Process

```python
def render_svg(
    participant: Participant,
    template_path: str,
    config: TemplateConfig
) -> Tuple[bytes, str]:
    """
    1. Load SVG XML
    2. Find elements by ID
    3. Replace text content
    4. Convert SVG → PNG (using PIL or librsvg)
    5. Save PNG to output dir
    6. Return (PNG bytes, path)
    """
    
    # Step 1: Parse SVG
    tree = ET.parse(template_path)
    root = tree.getroot()
    
    # Step 2: Replace text elements by ID
    name_elem = root.find(f".//{{{SVG_NS}}}text[@id='{config.svg_name_element_id}']")
    if name_elem is not None:
        name_elem.text = participant.name
    
    team_elem = root.find(f".//{{{SVG_NS}}}text[@id='{config.svg_team_element_id}']")
    if team_elem is not None:
        team_elem.text = participant.team
    
    # Step 3: Convert SVG to PNG bytes
    svg_bytes = ET.tostring(root)
    png_bytes = convert_svg_to_png(svg_bytes)  # Using PIL or librsvg
    
    # Step 4: Save and return
    output_path = os.path.join(config.output_dir, f"{safe_filename(participant.name)}.png")
    with open(output_path, 'wb') as f:
        f.write(png_bytes)
    
    return png_bytes, output_path
```

### 13.3 SVG vs PNG Trade-offs

| Feature | PNG Overlay | SVG Replace |
|---------|------------|------------|
| Complexity | Simple | Medium |
| Text Quality | Pixel-perfect | Scalable vector |
| File Size | Larger | Smaller |
| Font Fallback | Needed | Built-in SVG |
| Edit Template | Easy | Requires XML knowledge |
| Performance | ~200ms | ~300ms |

---

## 14. PACKAGE METADATA

### 14.1 pyproject.toml

```toml
[build-system]
requires = ["setuptools>=45", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "emailcert-certgen"
version = "0.1.0"
description = "Personalized certificate generator from Canva templates"
readme = "README.md"
authors = [{name = "Naresh Kumar S", email = "nareshkumarnkrs@gmail.com"}]
license = {text = "MIT"}
requires-python = ">=3.8"
dependencies = [
    "pillow>=10.0.0",
    "pandas>=2.0.0",
    "openpyxl>=3.1.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-cov>=4.1.0",
    "black>=23.9.0",
    "flake8>=6.0.0",
    "mypy>=1.5.0",
]
svg = [
    "cairosvg>=2.7.0",  # For SVG to PNG conversion
]

[project.urls]
Repository = "https://github.com/nareshkumarnkrs/emailcert"
```

### 14.2 version Control

```python
# __init__.py
__version__ = "0.1.0"
__author__ = "Naresh Kumar S"
__all__ = [
    "generate",
    "load_csv",
    "load_excel",
    "Participant",
    "TemplateConfig",
    "CertificateError",
]
```

---

## 15. CODE QUALITY TOOLS

### 15.1 Development Dependencies

```txt
# requirements-dev.txt
-r requirements.txt

# Testing
pytest==7.4.0
pytest-cov==4.1.0
pytest-xdist==3.3.0

# Code formatting
black==23.9.0

# Linting
flake8==6.0.0
flake8-docstrings==1.7.0

# Type checking
mypy==1.5.0

# Pre-commit hooks
pre-commit==3.3.0
```

### 15.2 Code Quality Targets

| Tool | Target | Rationale |
|------|--------|-----------|
| Black | 100% formatted | No manual style decisions |
| Flake8 | 0 errors | Clean code |
| Mypy | 0 errors | Type safety |
| Pytest | 80%+ coverage | Bug prevention |
| Docstrings | 100% coverage | Self-documenting |

### 15.3 Pre-commit Configuration

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.9.0
    hooks:
      - id: black

  - repo: https://github.com/PyCQA/flake8
    rev: 6.0.0
    hooks:
      - id: flake8

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.5.0
    hooks:
      - id: mypy
```

---

## 16. CUSTOM EXCEPTIONS

### 16.1 Exception Hierarchy

```python
class CertificateError(Exception):
    """Base exception"""

class LoaderError(CertificateError):
    """CSV/Excel loading failure"""
    # file not found, invalid format, missing columns, null values

class TemplateNotFoundError(CertificateError):
    """Template PNG/SVG file not found"""

class TemplateFormatError(CertificateError):
    """Template is invalid (not PNG/SVG, corrupted)"""

class OverlayError(CertificateError):
    """Text overlay on image failed"""
    # font error, image format error, coordinate error

class InvalidParticipantError(CertificateError):
    """Participant data validation failed"""
    # invalid name, invalid email, invalid team

class OutputError(CertificateError):
    """Cannot write output file"""
    # permission denied, disk full, path invalid
```

---

## 17. IMPLEMENTATION PHASES

### Phase 1: Core Module (Level 🔴 CRITICAL - 45 min)

**Files to code:**
- [ ] models.py (Participant dataclass, validation)
- [ ] config.py (TemplateConfig dataclass)
- [ ] exceptions.py (7 custom exceptions)
- [ ] logger.py (Logging setup)
- [ ] constants.py (Magic numbers)
- [ ] loader.py (load_csv, load_excel)
- [ ] renderer.py (PNG overlay)

**Deliverable:** Core module works for PNG templates

### Phase 2: SVG Support (Level 🟠 HIGH - 20 min)

**Files to code:**
- [ ] svg_renderer.py (SVG element replacement, convert to PNG)
- [ ] Update __init__.py to route PNG/SVG to correct renderer

**Deliverable:** Module supports both PNG and SVG templates

### Phase 3: Utilities & Validation (Level 🟠 HIGH - 15 min)

**Files to code:**
- [ ] utils.py (safe_filename, validate_*, ensure_*)
- [ ] Update loader.py with strict validation
- [ ] Update renderer.py with fallback strategies

**Deliverable:** Input validation + font/path fallbacks working

### Phase 4: Testing (Level 🟡 MEDIUM - 30 min)

**Files to create:**
- [ ] tests/test_models.py
- [ ] tests/test_loader.py
- [ ] tests/test_renderer.py
- [ ] tests/fixtures/ (sample template.png, sample.csv)
- [ ] pytest configuration

**Deliverable:** 80%+ test coverage

### Phase 5: Documentation (Level 🟢 LOW - 15 min)

**Files to create:**
- [ ] docstrings on all functions
- [ ] README.md with examples
- [ ] CHANGELOG.md
- [ ] Update .env.example

**Deliverable:** Fully documented module

---

## 18. PRIORITY & COMPLEXITY LEVELS

### 18.1 Feature Levels

```
🔴 CRITICAL (Must have)
├─ PNG template support
├─ CSV/Excel loading
├─ Text overlay
├─ Type hints
├─ Input validation
├─ Error handling
└─ Logging

🟠 HIGH (Should have)
├─ SVG template support
├─ Font fallback strategy
├─ Path fallback strategy
├─ Custom exceptions
└─ Environment variables

🟡 MEDIUM (Nice to have)
├─ Code quality tools
├─ pyproject.toml
├─ Pre-commit hooks
└─ Performance optimization

🟢 LOW (Future)
├─ Batch processing UI
├─ API endpoint
├─ Database integration
└─ Certificate archival
```

### 18.2 Code Complexity by Component

| Component | Complexity | Effort | Risk |
|-----------|-----------|--------|------|
| models.py | Low | 5 min | Low |
| loader.py | Low | 10 min | Low |
| renderer.py (PNG) | Medium | 15 min | Medium |
| renderer.py (fallbacks) | Medium | 10 min | Medium |
| svg_renderer.py | High | 20 min | High |
| utils.py | Low | 10 min | Low |
| exceptions.py | Low | 5 min | Low |
| logger.py | Low | 5 min | Low |
| tests | High | 30 min | Medium |
| **TOTAL** | **Medium** | **110 min** | **Medium** |

---

## 19. ASSUMPTIONS

- ✓ Users provide valid Canva PNG/SVG exports
- ✓ Spreadsheet has columns: name, team, email (exact case)
- ✓ System has write access to output directory
- ✓ PIL can be installed on target system
- ✓ One-by-one processing is acceptable (2 min for 248 certs)
- ✓ No certificate versioning needed

---

## 20. CONSTRAINTS

- ✗ NOT thread-safe (use ProcessPool or sequential)
- ✗ PNG output only (even from SVG templates)
- ✗ Single template per campaign
- ✗ No concurrent processing
- ✗ Requires Python 3.8+

---

## 21. SUCCESS CRITERIA

- ✅ Generate 248 certificates in < 3 minutes
- ✅ 80%+ test coverage
- ✅ 0 type errors (mypy)
- ✅ 0 flake8 errors
- ✅ All functions documented
- ✅ PNG template support works
- ✅ SVG template support works
- ✅ Font fallback strategy implemented
- ✅ Path fallback strategy implemented
- ✅ Logging at every step
- ✅ Input validation rules enforced

---

## 22. TIMELINE

| Phase | Duration | Status |
|-------|----------|--------|
| Planning (PLAN.md) | 1 day | ✅ Done |
| Phase 1 - Core | 45 min | ⏳ Next |
| Phase 2 - SVG | 20 min | ⏳ After core |
| Phase 3 - Utils | 15 min | ⏳ After SVG |
| Phase 4 - Tests | 30 min | ⏳ After utils |
| Phase 5 - Docs | 15 min | ⏳ Final |
| **TOTAL** | **~2.5 hours** | ⏳ |

---

## 23. NEXT STEPS

1. ✅ Review PLAN.md (this document)
2. ⏳ Create folder structure
3. ⏳ Code Phase 1 (Core module)
4. ⏳ Test locally
5. ⏳ Add SVG support
6. ⏳ Add fallback strategies
7. ⏳ Write tests
8. ⏳ Document

---

**Status:** READY TO CODE  
**Approved:** Self  
**Last Modified:** 2026-09-01
