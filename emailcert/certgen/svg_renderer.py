import io
import os
import time
import xml.etree.ElementTree as ET
from typing import Tuple

from .config import TemplateConfig
from .exceptions import OverlayError, TemplateFormatError, TemplateNotFoundError
from .logger import setup_logger
from .models import Participant
from .utils import ensure_output_dir, find_template, safe_filename

logger = setup_logger(__name__)

SVG_NS = "http://www.w3.org/2000/svg"


def _parse_svg(template_path: str) -> ET.ElementTree:
    """Parse SVG file and return ElementTree.

    Args:
        template_path: Path to SVG file.

    Returns:
        Parsed ElementTree.

    Raises:
        TemplateFormatError: If invalid XML.
    """
    try:
        tree = ET.parse(template_path)
        logger.debug(f"SVG parsed: {template_path}")
        return tree
    except ET.ParseError as e:
        raise TemplateFormatError(f"Invalid SVG XML {template_path}: {e}") from e
    except Exception as e:
        raise TemplateFormatError(f"Failed to parse SVG {template_path}: {e}") from e


def _find_element_by_id(root: ET.Element, element_id: str) -> ET.Element | None:
    """Find element by id, handling namespaces.

    SVG may use default namespace, so we try multiple queries.

    Args:
        root: Root element.
        element_id: ID to search.

    Returns:
        Element if found, else None.
    """
    # Try with namespace
    # Search for any element with attribute id=element_id
    # Use XPath with namespace handling

    # 1. Try with SVG namespace
    elem = root.find(f".//{{{SVG_NS}}}*[@id='{element_id}']")
    if elem is not None:
        return elem

    # 2. Try without namespace (some SVGs don't use ns)
    elem = root.find(f".//*[@id='{element_id}']")
    if elem is not None:
        return elem

    # 3. Manual iteration fallback (handles any namespace prefix)
    for e in root.iter():
        if e.get("id") == element_id:
            return e

    return None


def _replace_text_content(elem: ET.Element, new_text: str) -> None:
    """Replace text content of SVG element.

    Handles both simple text and tspan children.

    Args:
        elem: Element to modify.
        new_text: New text value.
    """
    # Remove tspan children if present
    tspans = [child for child in elem if child.tag.endswith("tspan") or child.tag == "tspan"]
    for tspan in tspans:
        elem.remove(tspan)

    # Also handle namespaced tspan
    ns_tspan = f"{{{SVG_NS}}}tspan"
    tspans_ns = [child for child in elem if child.tag == ns_tspan]
    for tspan in tspans_ns:
        elem.remove(tspan)

    # Set text (also clear tail/text of children)
    elem.text = new_text
    # Ensure element has no leftover children text
    for child in elem:
        child.tail = None


def _get_svg_namespace(root: ET.Element) -> str:
    """Detect SVG namespace from root tag."""
    if root.tag.startswith("{"):
        return root.tag[1:].split("}")[0]
    return ""


def _create_text_element(
    root: ET.Element,
    element_id: str,
    x: int,
    y: int,
    text: str,
    font_size: int,
    fill: str = "black",
) -> ET.Element:
    """Create and append a new SVG text element for overlay.

    Used when template (like src/final.svg with embedded PNG) has no editable text elements.
    Creates text centered at x,y similar to PNG's center_text anchor.

    Args:
        root: SVG root element.
        element_id: ID for new element.
        x: X coordinate.
        y: Y coordinate.
        text: Text content.
        font_size: Font size.
        fill: Fill color.

    Returns:
        Created element.
    """
    ns = _get_svg_namespace(root)
    # Create element with namespace if needed, otherwise plain
    if ns:
        elem = ET.Element(f"{{{ns}}}text")
    else:
        elem = ET.Element("text")
    elem.set("id", element_id)
    elem.set("x", str(x))
    elem.set("y", str(y))
    elem.set("font-size", str(font_size))
    elem.set("font-family", "Arial, sans-serif")
    elem.set("text-anchor", "middle")
    elem.set("dominant-baseline", "middle")
    elem.set("fill", fill)
    elem.text = text
    # Try to handle color from config - convert tuple to hex if needed
    root.append(elem)
    logger.debug(f"Injected new SVG text element id={element_id} at ({x},{y}) size {font_size}: {text}")
    return elem


def _ensure_text(root: ET.Element, element_id: str, x: int, y: int, text: str, font_size: int, fill_tuple=None) -> ET.Element:
    """Find or create text element, then set its content."""
    elem = _find_element_by_id(root, element_id)
    if elem is not None:
        _replace_text_content(elem, text)
        # Update position/size to match config (in case template had different)
        elem.set("x", str(x))
        elem.set("y", str(y))
        elem.set("font-size", str(font_size))
        elem.set("text-anchor", "middle")
        return elem
    else:
        # Create new element - convert fill_tuple to hex if provided
        fill = "black"
        if fill_tuple and len(fill_tuple) == 3:
            fill = f"rgb({fill_tuple[0]},{fill_tuple[1]},{fill_tuple[2]})"
        return _create_text_element(root, element_id, x, y, text, font_size, fill)


def render_svg(
    participant: Participant,
    template_path: str,
    config: TemplateConfig,
) -> Tuple[bytes, str]:
    """Replace text elements in SVG, export as PNG.

    Args:
        participant: Participant data.
        template_path: Path to SVG template.
        config: Rendering configuration with svg_name/team_element_id.

    Returns:
        Tuple of (PNG bytes, file path).

    Raises:
        TemplateNotFoundError: If template not found.
        TemplateFormatError: If SVG invalid or cairosvg missing.
        OverlayError: If conversion fails.
    """
    start = time.time()

    # Resolve template with fallbacks
    resolved_path = find_template(template_path)

    if not os.path.exists(resolved_path):
        raise TemplateNotFoundError(f"SVG template not found: {resolved_path}")

    if not resolved_path.lower().endswith(".svg"):
        logger.warning(f"Template {resolved_path} does not have .svg extension, trying anyway")

    # Parse SVG
    tree = _parse_svg(resolved_path)
    root = tree.getroot()

    # Validate root is svg
    if not root.tag.endswith("svg"):
        logger.warning(f"Root tag is not svg: {root.tag}, attempting to continue")

    # Handle all 4 fields: name, team, department, year
    # For src/final.svg which has embedded PNG and no text ids, we inject new elements
    # instead of requiring pre-existing ids.

    # Name - required, always inject/replace
    _ensure_text(
        root,
        config.svg_name_element_id,
        config.name_position[0],
        config.name_position[1],
        participant.name,
        getattr(config, "font_size_name", 60),
        getattr(config, "text_color", (0, 0, 0)),
    )

    # Team - required
    _ensure_text(
        root,
        config.svg_team_element_id,
        config.team_position[0],
        config.team_position[1],
        participant.team,
        getattr(config, "font_size_team", 40),
        getattr(config, "text_color", (0, 0, 0)),
    )

    # Department - optional, only if provided
    dept_text = getattr(participant, "department", "") or getattr(participant, "dept", "")
    if dept_text and dept_text.strip():
        dept_pos = getattr(config, "department_position", getattr(config, "dept_position", (800, 600)))
        _ensure_text(
            root,
            getattr(config, "svg_department_element_id", getattr(config, "svg_dept_element_id", "department")),
            dept_pos[0],
            dept_pos[1],
            dept_text,
            getattr(config, "font_size_department", getattr(config, "font_size_dept", 36)),
            getattr(config, "text_color", (0, 0, 0)),
        )
    else:
        # Remove department element if exists but no data (to avoid placeholder)
        dept_elem = _find_element_by_id(root, getattr(config, "svg_department_element_id", "department"))
        if dept_elem is not None:
            _replace_text_content(dept_elem, "")

    # Year - optional
    year_text = getattr(participant, "year", "")
    if year_text and str(year_text).strip():
        year_pos = getattr(config, "year_position", (800, 700))
        _ensure_text(
            root,
            getattr(config, "svg_year_element_id", "year"),
            year_pos[0],
            year_pos[1],
            str(year_text).strip(),
            getattr(config, "font_size_year", 32),
            getattr(config, "text_color", (0, 0, 0)),
        )
    else:
        year_elem = _find_element_by_id(root, getattr(config, "svg_year_element_id", "year"))
        if year_elem is not None:
            _replace_text_content(year_elem, "")

    # Convert SVG to PNG bytes
    try:
        # Serialize modified SVG to bytes
        svg_bytes = ET.tostring(root, encoding="utf-8", xml_declaration=True)

        logger.debug(f"Converting SVG to PNG ({len(svg_bytes)} bytes)")

        # Use cairosvg to convert
        try:
            import cairosvg
        except ImportError as e:
            raise TemplateFormatError(f"SVG support requires cairosvg (pip install cairosvg): {e}") from e

        png_bytes = cairosvg.svg2png(bytestring=svg_bytes)

        logger.debug(f"SVG converted to PNG: {len(png_bytes)} bytes")

    except TemplateFormatError:
        raise
    except Exception as e:
        logger.error(f"Failed to convert SVG to PNG for {participant.name}: {e}")
        raise OverlayError(f"SVG to PNG conversion failed for {participant.name}: {e}") from e

    # Save to output dir
    try:
        output_dir = ensure_output_dir(config.output_dir)
        filename = f"{safe_filename(participant.name)}.png"
        output_path = os.path.join(output_dir, filename)

        with open(output_path, "wb") as f:
            f.write(png_bytes)

        elapsed = (time.time() - start) * 1000
        logger.info(f"Generated SVG certificate for {participant.name} -> {output_path} ({elapsed:.0f}ms)")
        logger.debug(f"SVG overlay completed in {elapsed:.0f}ms for {participant.name}")

        return png_bytes, output_path

    except Exception as e:
        logger.error(f"Failed to save PNG for {participant.name}: {e}")
        from .exceptions import OutputError

        raise OutputError(f"Failed to save certificate for {participant.name}: {e}") from e
