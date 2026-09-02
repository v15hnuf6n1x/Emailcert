import io
import os
import time
from typing import Optional, Tuple

from PIL import Image, ImageDraw

from .config import TemplateConfig
from .constants import MIN_TEMPLATE_HEIGHT, MIN_TEMPLATE_WIDTH
from .exceptions import OverlayError, TemplateFormatError, TemplateNotFoundError
from .logger import setup_logger
from .models import Participant
from .utils import ensure_output_dir, find_template, load_font, safe_filename

logger = setup_logger(__name__)

# --- PDF Helpers ---

def png_bytes_to_pdf(png_bytes: bytes) -> bytes:
    """Convert PNG bytes to PDF bytes via Pillow.

    Used after certificate generation to produce email-ready PDF.
    Handles RGBA/L modes by flattening onto white background.

    Args:
        png_bytes: PNG image bytes.

    Returns:
        PDF bytes.
    """
    img = Image.open(io.BytesIO(png_bytes))
    if img.mode in ("RGBA", "LA"):
        bg = Image.new("RGB", img.size, (255, 255, 255))
        # Use alpha as mask if exists
        if img.mode == "RGBA":
            bg.paste(img, mask=img.split()[3])
        else:
            # LA mode
            bg.paste(img.convert("RGBA"), mask=Image.open(io.BytesIO(png_bytes)).split()[1] if len(img.split()) > 1 else None)
        img = bg
    elif img.mode != "RGB":
        img = img.convert("RGB")
    buf = io.BytesIO()
    # PIL PDF save: resolution 100-150 is fine for certificate
    img.save(buf, format="PDF", resolution=100.0)
    return buf.getvalue()


def save_pdf(pdf_bytes: bytes, output_path: str) -> str:
    """Save PDF bytes to file, ensuring directory exists.

    Args:
        pdf_bytes: PDF content.
        output_path: Destination file path (should end with .pdf).

    Returns:
        Output path.
    """
    dir_name = os.path.dirname(output_path)
    if dir_name:
        ensure_output_dir(dir_name)
    with open(output_path, "wb") as f:
        f.write(pdf_bytes)
    logger.info(f"Saved PDF: {output_path} ({len(pdf_bytes)} bytes)")
    return output_path


def _validate_png_template(template_path: str) -> None:
    """Validate PNG template meets requirements.

    Args:
        template_path: Path to PNG file.

    Raises:
        TemplateFormatError: If invalid.
        TemplateNotFoundError: If not found.
    """
    if not os.path.exists(template_path):
        raise TemplateNotFoundError(f"Template not found: {template_path}")

    try:
        with Image.open(template_path) as img:
            # Check format
            if img.format not in ("PNG", None):
                # Allow PNG even if format detection is None for some files
                # Check extension fallback
                if not template_path.lower().endswith(".png"):
                    raise TemplateFormatError(f"Template must be PNG, got {img.format}: {template_path}")

            # Check mode
            if img.mode not in ("RGB", "RGBA"):
                logger.warning(f"Template mode {img.mode} not RGB/RGBA, will convert: {template_path}")

            # Check size
            width, height = img.size
            if width < MIN_TEMPLATE_WIDTH or height < MIN_TEMPLATE_HEIGHT:
                raise TemplateFormatError(
                    f"Template too small: {width}x{height}, minimum {MIN_TEMPLATE_WIDTH}x{MIN_TEMPLATE_HEIGHT}: {template_path}"
                )

            logger.debug(f"Template validated: {template_path} {width}x{height} mode={img.mode}")
    except TemplateFormatError:
        raise
    except TemplateNotFoundError:
        raise
    except Exception as e:
        raise TemplateFormatError(f"Invalid or corrupted PNG template {template_path}: {e}") from e


def render_png(
    participant: Participant,
    template_path: str,
    config: TemplateConfig,
) -> Tuple[bytes, str]:
    """Overlay text on PNG template.

    Args:
        participant: Participant data.
        template_path: Path to PNG template.
        config: Rendering configuration.

    Returns:
        Tuple of (PNG bytes, file path).

    Raises:
        TemplateNotFoundError: If template not found.
        TemplateFormatError: If template invalid.
        OverlayError: If overlay fails.
        OutputError: If cannot write output.
    """
    start = time.time()

    # Resolve template with fallbacks
    resolved_path = find_template(template_path)

    # Validate
    _validate_png_template(resolved_path)

    # Ensure output directory
    output_dir = ensure_output_dir(config.output_dir)

    # Load fonts with fallback - per field
    try:
        font_name = load_font(config.font_path, config.font_size_name)
        font_team = load_font(config.font_path, config.font_size_team)
        font_dept = load_font(config.font_path, getattr(config, "font_size_department", config.font_size_team))
        font_year = load_font(config.font_path, getattr(config, "font_size_year", config.font_size_team))
    except Exception as e:
        raise OverlayError(f"Failed to load fonts: {e}") from e

    # Open template and overlay
    try:
        img = Image.open(resolved_path).convert("RGBA")
        draw = ImageDraw.Draw(img)

        # Prepare drawing options
        fill = config.text_color

        # Use anchor="mm" for center middle if requested (PIL >=8.0)
        # Anchor mm means middle-middle centered at position
        anchor = "mm" if config.center_text else None

        # Draw name (required)
        if anchor:
            draw.text(config.name_position, participant.name, fill=fill, font=font_name, anchor=anchor)
        else:
            draw.text(config.name_position, participant.name, fill=fill, font=font_name)

        # Draw team
        if anchor:
            draw.text(config.team_position, participant.team, fill=fill, font=font_team, anchor=anchor)
        else:
            draw.text(config.team_position, participant.team, fill=fill, font=font_team)

        # Draw department (optional - only if provided)
        dept_text = getattr(participant, "department", "") or getattr(participant, "dept", "")
        if dept_text and dept_text.strip():
            dept_pos = getattr(config, "department_position", getattr(config, "dept_position", (800, 600)))
            if anchor:
                draw.text(dept_pos, dept_text, fill=fill, font=font_dept, anchor=anchor)
            else:
                draw.text(dept_pos, dept_text, fill=fill, font=font_dept)

        # Draw year (optional)
        year_text = getattr(participant, "year", "")
        if year_text and str(year_text).strip():
            year_pos = getattr(config, "year_position", (800, 700))
            # Convert year to string
            year_str = str(year_text).strip()
            if anchor:
                draw.text(year_pos, year_str, fill=fill, font=font_year, anchor=anchor)
            else:
                draw.text(year_pos, year_str, fill=fill, font=font_year)

        logger.debug(
            f"Overlay completed for {participant.name} at {config.name_position}/{config.team_position}"
            f"/{getattr(config, 'department_position', 'N/A')}/{getattr(config, 'year_position', 'N/A')}"
        )

        # Convert to RGB for PNG save (remove alpha if needed)
        # Keep RGBA if template was RGBA? Spec says output PNG RGB 8-bit
        # Convert to RGB for consistency
        if img.mode == "RGBA":
            # Create white background for transparency
            background = Image.new("RGB", img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[3])  # Use alpha channel as mask
            img = background
        else:
            img = img.convert("RGB")

        # Save to bytes and file
        buf = io.BytesIO()
        img.save(buf, format="PNG", quality=config.quality if hasattr(config, "quality") else 95)
        png_bytes = buf.getvalue()

        # Determine output path
        filename = f"{safe_filename(participant.name)}.png"
        output_path = os.path.join(output_dir, filename)

        with open(output_path, "wb") as f:
            f.write(png_bytes)

        elapsed = (time.time() - start) * 1000
        logger.info(f"Generated certificate for {participant.name} -> {output_path} ({elapsed:.0f}ms)")
        logger.debug(f"Overlay completed in {elapsed:.0f}ms for {participant.name}")

        return png_bytes, output_path

    except (TemplateNotFoundError, TemplateFormatError):
        raise
    except Exception as e:
        logger.error(f"Failed to overlay text for {participant.name}: {e}")
        raise OverlayError(f"Failed to overlay text for {participant.name}: {e}") from e


def generate(
    participant: Participant,
    template_path: str,
    config: Optional[TemplateConfig] = None,
    output_dir: Optional[str] = None,
) -> Tuple[bytes, str]:
    """Generate certificate for a participant.

    Main entry point. Routes to PNG or SVG renderer based on template extension.

    Args:
        participant: Participant data.
        template_path: Path to template (PNG or SVG).
        config: Optional TemplateConfig (creates default if None).
        output_dir: Optional output directory override (overrides config.output_dir).

    Returns:
        Tuple of (PNG bytes, file path).

    Raises:
        TemplateNotFoundError
        OverlayError
        InvalidParticipantError
        TemplateFormatError
    """
    from .exceptions import InvalidParticipationError

    # Validate participant (triggers __post_init__ validation)
    if not isinstance(participant, Participant):
        raise InvalidParticipationError(f"Invalid participant type: {type(participant)}")
    # Re-validate by checking fields (in case object bypassed __post_init__)
    # This will raise if invalid
    participant.__post_init__()  # type: ignore

    if config is None:
        config = TemplateConfig()

    # Override output_dir if provided
    if output_dir is not None:
        # Create a copy with overridden output_dir
        import dataclasses

        config = dataclasses.replace(config, output_dir=output_dir)

    # Detect format
    ext = os.path.splitext(template_path)[1].lower().lstrip(".")
    if not ext:
        # Try to resolve via find_template first to get extension
        try:
            resolved = find_template(template_path)
            ext = os.path.splitext(resolved)[1].lower().lstrip(".")
        except TemplateNotFoundError:
            raise

    if ext == "svg":
        # Lazy import SVG renderer to avoid hard dependency on cairosvg if not used
        try:
            from .svg_renderer import render_svg

            return render_svg(participant, template_path, config)
        except ImportError as e:
            # If svg_renderer not available or cairosvg missing, raise
            logger.error(f"SVG rendering requires cairosvg: {e}")
            raise TemplateFormatError(f"SVG support not available (missing cairosvg): {e}") from e
    elif ext == "png":
        return render_png(participant, template_path, config)
    else:
        # Fallback to PNG renderer if no extension or unknown but file is PNG
        # Try PNG anyway
        logger.warning(f"Unknown template extension '{ext}', trying PNG renderer")
        return render_png(participant, template_path, config)
