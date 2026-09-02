import os
from dataclasses import dataclass
from typing import Tuple

from .constants import (
    DEFAULT_CENTER_TEXT,
    DEFAULT_DEPARTMENT_POSITION,
    DEFAULT_FONT_PATH,
    DEFAULT_FONT_SIZE_DEPARTMENT,
    DEFAULT_FONT_SIZE_NAME,
    DEFAULT_FONT_SIZE_TEAM,
    DEFAULT_FONT_SIZE_YEAR,
    DEFAULT_NAME_POSITION,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_PNG_QUALITY,
    DEFAULT_SVG_DEPARTMENT_ELEMENT_ID,
    DEFAULT_SVG_NAME_ELEMENT_ID,
    DEFAULT_SVG_TEAM_ELEMENT_ID,
    DEFAULT_SVG_YEAR_ELEMENT_ID,
    DEFAULT_TEAM_POSITION,
    DEFAULT_TEMPLATE_FORMAT,
    DEFAULT_TEXT_COLOR,
    DEFAULT_YEAR_POSITION,
)


@dataclass
class TemplateConfig:
    """Configuration for certificate template rendering with 4 fields."""

    # Text positioning (X, Y from top-left) - for dash lines on certificate
    name_position: Tuple[int, int] = DEFAULT_NAME_POSITION
    team_position: Tuple[int, int] = DEFAULT_TEAM_POSITION
    # Legacy alias support
    team_name_position: Tuple[int, int] = DEFAULT_TEAM_POSITION
    department_position: Tuple[int, int] = DEFAULT_DEPARTMENT_POSITION
    year_position: Tuple[int, int] = DEFAULT_YEAR_POSITION
    # Aliases for convenience
    dept_position: Tuple[int, int] = DEFAULT_DEPARTMENT_POSITION

    # Font settings - per field
    font_path: str = DEFAULT_FONT_PATH
    font_size_name: int = DEFAULT_FONT_SIZE_NAME
    font_size_team: int = DEFAULT_FONT_SIZE_TEAM
    font_size_department: int = DEFAULT_FONT_SIZE_DEPARTMENT
    font_size_year: int = DEFAULT_FONT_SIZE_YEAR
    # Aliases
    font_size_dept: int = DEFAULT_FONT_SIZE_DEPARTMENT

    # Text appearance
    text_color: Tuple[int, int, int] = DEFAULT_TEXT_COLOR  # RGB black
    center_text: bool = DEFAULT_CENTER_TEXT  # mm anchor = middle-middle

    # Output settings
    output_dir: str = DEFAULT_OUTPUT_DIR
    template_format: str = DEFAULT_TEMPLATE_FORMAT  # "png" or "svg"
    quality: int = DEFAULT_PNG_QUALITY

    # SVG-specific element IDs
    svg_name_element_id: str = DEFAULT_SVG_NAME_ELEMENT_ID  # Element to replace
    svg_team_element_id: str = DEFAULT_SVG_TEAM_ELEMENT_ID  # Element to replace
    svg_department_element_id: str = DEFAULT_SVG_DEPARTMENT_ELEMENT_ID
    svg_year_element_id: str = DEFAULT_SVG_YEAR_ELEMENT_ID
    # Aliases
    svg_dept_element_id: str = DEFAULT_SVG_DEPARTMENT_ELEMENT_ID

    def __post_init__(self) -> None:
        # Sync team_position and team_name_position (bidirectional alias)
        if self.team_name_position != DEFAULT_TEAM_POSITION and self.team_position == DEFAULT_TEAM_POSITION:
            self.team_position = self.team_name_position
        elif self.team_position != self.team_name_position:
            self.team_name_position = self.team_position
        # Sync department aliases
        if self.dept_position != DEFAULT_DEPARTMENT_POSITION and self.department_position == DEFAULT_DEPARTMENT_POSITION:
            self.department_position = self.dept_position
        elif self.department_position != self.dept_position:
            self.dept_position = self.department_position
        if self.font_size_dept != DEFAULT_FONT_SIZE_DEPARTMENT and self.font_size_department == DEFAULT_FONT_SIZE_DEPARTMENT:
            self.font_size_department = self.font_size_dept
        elif self.font_size_department != self.font_size_dept:
            self.font_size_dept = self.font_size_department
        if self.svg_dept_element_id != DEFAULT_SVG_DEPARTMENT_ELEMENT_ID and self.svg_department_element_id == DEFAULT_SVG_DEPARTMENT_ELEMENT_ID:
            self.svg_department_element_id = self.svg_dept_element_id
        elif self.svg_department_element_id != self.svg_dept_element_id:
            self.svg_dept_element_id = self.svg_department_element_id

    @classmethod
    def from_env(cls) -> "TemplateConfig":
        """Create config from environment variables with defaults."""
        # Load .env.local if exists (optional)
        try:
            from dotenv import load_dotenv

            load_dotenv(".env.local")
            load_dotenv(".env")
        except ImportError:
            pass

        def getenv_int(key: str, default: int) -> int:
            val = os.getenv(key)
            if val is None:
                return default
            try:
                return int(val)
            except ValueError:
                return default

        # Text positioning - individual coords if provided
        name_x = getenv_int("CERT_NAME_POS_X", DEFAULT_NAME_POSITION[0])
        name_y = getenv_int("CERT_NAME_POS_Y", DEFAULT_NAME_POSITION[1])
        team_x = getenv_int("CERT_TEAM_POS_X", DEFAULT_TEAM_POSITION[0])
        team_y = getenv_int("CERT_TEAM_POS_Y", DEFAULT_TEAM_POSITION[1])
        dept_x = getenv_int("CERT_DEPT_POS_X", DEFAULT_DEPARTMENT_POSITION[0])
        dept_y = getenv_int("CERT_DEPT_POS_Y", DEFAULT_DEPARTMENT_POSITION[1])
        year_x = getenv_int("CERT_YEAR_POS_X", DEFAULT_YEAR_POSITION[0])
        year_y = getenv_int("CERT_YEAR_POS_Y", DEFAULT_YEAR_POSITION[1])

        # Colors
        r = getenv_int("CERT_TEXT_COLOR_R", DEFAULT_TEXT_COLOR[0])
        g = getenv_int("CERT_TEXT_COLOR_G", DEFAULT_TEXT_COLOR[1])
        b = getenv_int("CERT_TEXT_COLOR_B", DEFAULT_TEXT_COLOR[2])

        return cls(
            name_position=(name_x, name_y),
            team_position=(team_x, team_y),
            team_name_position=(team_x, team_y),
            department_position=(dept_x, dept_y),
            year_position=(year_x, year_y),
            dept_position=(dept_x, dept_y),
            font_path=os.getenv("CERT_FONT_PATH", DEFAULT_FONT_PATH),
            font_size_name=getenv_int("CERT_FONT_SIZE_NAME", DEFAULT_FONT_SIZE_NAME),
            font_size_team=getenv_int("CERT_FONT_SIZE_TEAM", DEFAULT_FONT_SIZE_TEAM),
            font_size_department=getenv_int("CERT_DEPT_FONT_SIZE", DEFAULT_FONT_SIZE_DEPARTMENT),
            font_size_year=getenv_int("CERT_YEAR_FONT_SIZE", DEFAULT_FONT_SIZE_YEAR),
            font_size_dept=getenv_int("CERT_DEPT_FONT_SIZE", DEFAULT_FONT_SIZE_DEPARTMENT),
            text_color=(r, g, b),
            center_text=os.getenv("CERT_CENTER_TEXT", str(DEFAULT_CENTER_TEXT)).lower() in ("true", "1", "yes"),
            output_dir=os.getenv("CERT_OUTPUT_DIR", DEFAULT_OUTPUT_DIR),
            template_format=os.getenv("CERT_TEMPLATE_FORMAT", DEFAULT_TEMPLATE_FORMAT),
            quality=getenv_int("CERT_QUALITY", DEFAULT_PNG_QUALITY),
            svg_name_element_id=os.getenv("CERT_SVG_NAME_ELEMENT_ID", DEFAULT_SVG_NAME_ELEMENT_ID),
            svg_team_element_id=os.getenv("CERT_SVG_TEAM_ELEMENT_ID", DEFAULT_SVG_TEAM_ELEMENT_ID),
            svg_department_element_id=os.getenv("CERT_SVG_DEPT_ELEMENT_ID", DEFAULT_SVG_DEPARTMENT_ELEMENT_ID),
            svg_year_element_id=os.getenv("CERT_SVG_YEAR_ELEMENT_ID", DEFAULT_SVG_YEAR_ELEMENT_ID),
            svg_dept_element_id=os.getenv("CERT_SVG_DEPT_ELEMENT_ID", DEFAULT_SVG_DEPARTMENT_ELEMENT_ID),
        )
