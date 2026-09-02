import os
import re
import sys
import unicodedata
from typing import Tuple

from PIL import ImageFont

from .constants import (
    DEFAULT_OUTPUT_DIR,
    FALLBACK_FONT_PATHS_LINUX,
    FALLBACK_FONT_PATHS_MACOS,
    FALLBACK_FONT_PATHS_WINDOWS,
)
from .exceptions import OutputError
from .logger import setup_logger

logger = setup_logger(__name__)


def safe_filename(name: str) -> str:
    """Convert name to safe filename.

    Examples:
        "John Doe" -> "john_doe"
        "Jane-Smith" -> "jane_smith"
        "Jose Garcia" -> "jose_garcia"
        "John  Doe!!" -> "john_doe"

    Args:
        name: Original name string.

    Returns:
        Safe lowercase filename without extension.
    """
    # Normalize unicode (e.g., Jose -> Jose)
    normalized = unicodedata.normalize("NFKD", name)
    ascii_str = normalized.encode("ascii", "ignore").decode("ascii")
    # Lowercase and replace non-alphanumeric with underscore
    safe = re.sub(r"[^a-zA-Z0-9]+", "_", ascii_str.lower())
    # Collapse multiple underscores and strip leading/trailing
    safe = re.sub(r"_+", "_", safe).strip("_")
    # Fallback if empty
    if not safe:
        safe = "certificate"
    return safe


def ensure_output_dir(path: str) -> str:
    """Create output directory if missing, with fallback.

    Args:
        path: Desired output directory path.

    Returns:
        Actual directory path used (may be fallback).

    Raises:
        OutputError: If no directory can be created.
    """
    try:
        os.makedirs(path, exist_ok=True)
        logger.info(f"Output directory ready: {path}")
        return path
    except PermissionError as e:
        logger.warning(f"No permission for {path}: {e}, using fallback")
    except Exception as e:
        logger.warning(f"Cannot create {path}: {e}, using fallback")

    # Fallback to default directory in current dir
    fallback_dir = DEFAULT_OUTPUT_DIR
    try:
        os.makedirs(fallback_dir, exist_ok=True)
        logger.warning(f"Using fallback directory: {fallback_dir}")
        return fallback_dir
    except Exception as e:
        logger.error(f"Cannot create fallback directory {fallback_dir}: {e}")
        raise OutputError(f"Cannot create output directory {path} or fallback {fallback_dir}: {e}") from e


def get_template_format(template_path: str) -> str:
    """Return 'png' or 'svg' based on file extension.

    Args:
        template_path: Path to template file.

    Returns:
        Lowercase extension without dot: 'png' or 'svg'.

    Raises:
        ValueError: If extension is not supported.
    """
    ext = os.path.splitext(template_path)[1].lower().lstrip(".")
    if ext not in ("png", "svg"):
        raise ValueError(f"Unsupported template format: {ext}, expected png or svg")
    return ext


def validate_template(template_path: str) -> bool:
    """Check if template exists and is valid path.

    Args:
        template_path: Path to check.

    Returns:
        True if exists.
    """
    return os.path.exists(template_path) and os.path.isfile(template_path)


def find_template(template_path: str, campaign_name: str = None) -> str:
    """Find template with fallback strategies.

    Fallback hierarchy:
        1. Exact path (user provided)
        2. Current directory (./basename)
        3. events/{campaign}/basename
        4. events/sparkverse/basename (default)

    Args:
        template_path: User-provided template path.
        campaign_name: Optional campaign name for fallback.

    Returns:
        Resolved template path.

    Raises:
        TemplateNotFoundError: If not found in any location.
    """
    from .exceptions import TemplateNotFoundError

    # Step 1: Try exact path
    if os.path.exists(template_path):
        logger.info(f"Template found: {template_path}")
        return template_path

    logger.debug(f"Template not at {template_path}, trying fallbacks...")

    basename = os.path.basename(template_path)

    # Step 2: Try current directory
    cur_path = os.path.join(".", basename)
    if os.path.exists(cur_path):
        logger.info(f"Template found in current dir: {cur_path}")
        return cur_path

    # Step 3: Try events/campaign/ folder
    if campaign_name:
        fallback_path = os.path.join("events", campaign_name, basename)
        if os.path.exists(fallback_path):
            logger.info(f"Template found in events/{campaign_name}: {fallback_path}")
            return fallback_path

    # Step 4: Try events/sparkverse/ (default)
    default_fallback = os.path.join("events", "sparkverse", basename)
    if os.path.exists(default_fallback):
        logger.info(f"Template found at default: {default_fallback}")
        return default_fallback

    # Step 5: All failed
    logger.error(f"Template not found: {template_path}")
    raise TemplateNotFoundError(
        f"Template {template_path} not found in any expected location "
        f"(tried: {template_path}, {cur_path}, events/sparkverse/{basename})"
    )


def load_font(font_path: str, size: int):
    """Load font with smart platform-specific fallbacks.

    Fallback hierarchy:
        1. User's font_path
        2. OS-specific paths (Windows/macOS/Linux)
        3. PIL default font

    Args:
        font_path: Desired font path.
        size: Font size.

    Returns:
        PIL ImageFont instance.
    """
    paths = [font_path]

    # Add platform-specific paths
    if sys.platform == "win32":
        paths.extend(FALLBACK_FONT_PATHS_WINDOWS)
    elif sys.platform == "darwin":  # macOS
        paths.extend(FALLBACK_FONT_PATHS_MACOS)
    else:  # Linux
        paths.extend(FALLBACK_FONT_PATHS_LINUX)
        # Also add fallback without absolute path as last truetype attempt
        paths.append("arial.ttf")

    # De-duplicate while preserving order
    seen = set()
    unique_paths = []
    for p in paths:
        if p not in seen:
            unique_paths.append(p)
            seen.add(p)

    for p in unique_paths:
        try:
            logger.debug(f"Trying font: {p} size {size}")
            font = ImageFont.truetype(p, size)
            logger.debug(f"Font loaded: {p}")
            return font
        except (OSError, IOError) as e:
            logger.debug(f"Font not found: {p} ({e})")
            continue

    # Fall back to PIL default
    logger.warning(f"No TrueType fonts found for {font_path} size {size}, using PIL default font")
    return ImageFont.load_default()


def validate_participant(participant) -> bool:
    """Validate participant data, raise on error.

    Args:
        participant: Participant object to validate.

    Returns:
        True if valid.

    Raises:
        InvalidParticipationError: If validation fails.
    """
    from .models import Participant as ParticipantModel

    if not isinstance(participant, ParticipantModel):
        from .exceptions import InvalidParticipationError

        raise InvalidParticipationError(f"Invalid participant type: {type(participant)}")

    # Trigger __post_init__ validation
    participant.__post_init__()
    return True


def strip_whitespace(df):
    """Remove leading/trailing spaces from all string columns in DataFrame.

    Args:
        df: pandas DataFrame.

    Returns:
        DataFrame with stripped string values.
    """
    # Only process object (string) columns
    for col in df.select_dtypes(include=["object"]).columns:
        df[col] = df[col].astype(str).str.strip()
        # Convert string "nan" back to proper handling? Keep as is, loader will handle
    return df
