import os
from typing import Dict, List, Optional

import pandas as pd

from .exceptions import LoaderError
from .logger import setup_logger
from .models import Participant
from .utils import strip_whitespace

logger = setup_logger(__name__)

# --- Column mapping via .env ---
# For future use: set these in .env.local to override default column names without code change
# Example: CERT_COL_TEAM="Team Name" and CERT_COL_NAMES="Leader Name,M1 Name,M2 Name,M3 Name"
def _get_env_column_mapping() -> Dict[str, str]:
    """Read column mapping from environment variables.

    Returns:
        Dict with keys: team_col, name_cols (comma-separated)
        Only returns mappings that are set in env.
    """
    mapping: Dict[str, str] = {}
    # Try to load .env files if dotenv available
    try:
        from dotenv import load_dotenv

        load_dotenv(".env.local")
        load_dotenv(".env")
        load_dotenv(".env.example")
    except ImportError:
        pass

    team_col = os.getenv("CERT_COL_TEAM")
    if team_col:
        mapping["team_col"] = team_col.strip()

    name_cols = os.getenv("CERT_COL_NAMES")
    if name_cols:
        mapping["name_cols"] = name_cols.strip()

    # Also support single name column via CERT_COL_NAME
    name_col = os.getenv("CERT_COL_NAME")
    if name_col and "name_cols" not in mapping:
        mapping["name_cols"] = name_col.strip()

    return mapping

REQUIRED_COLUMNS = ["name", "team"]  # email optional - only name and team required
OPTIONAL_COLUMNS = ["email", "department", "dept", "year"]
ALT_TEAM_COLUMNS = ["team_name", "Team"]  # backward compat
ALT_DEPT_COLUMNS = ["department", "dept", "Department", "Dept", "DEPARTMENT"]
ALT_YEAR_COLUMNS = ["year", "Year", "year_of_study", "Year_of_Study", "study_year", "academic_year", "YEAR"]
# Supported encodings to try in order
ENCODINGS = ["utf-8", "utf-8-sig", "latin-1"]


def _validate_and_create_participants(df: pd.DataFrame, filepath: str) -> List[Participant]:
    """Validate DataFrame and create Participant list.

    Args:
        df: DataFrame with participant data.
        filepath: Source filepath for error messages.

    Returns:
        List of validated Participant objects.

    Raises:
        LoaderError: If validation fails.
    """
    # Normalize column names: strip whitespace, keep exact case check
    df.columns = [str(c).strip() for c in df.columns]

    # Check required columns exist (with alias support for team)
    # Accept either 'team' or 'team_name'
    columns_lower = {c.lower(): c for c in df.columns}
    missing = []
    for col in REQUIRED_COLUMNS:
        if col not in df.columns:
            # Check alias for team
            if col == "team" and ("team_name" in df.columns or "Team" in df.columns):
                continue
            missing.append(col)

    if missing:
        raise LoaderError(
            f"Missing required columns {missing} in {filepath}. "
            f"Found: {list(df.columns)}. Required: {REQUIRED_COLUMNS}"
        )

    # Normalize team column alias to 'team'
    if "team" not in df.columns and "team_name" in df.columns:
        df = df.rename(columns={"team_name": "team"})
    if "team" not in df.columns and "Team" in df.columns:
        df = df.rename(columns={"Team": "team"})

    # Check for null values in required columns only
    for col in REQUIRED_COLUMNS:
        if df[col].isnull().any():
            null_rows = df[df[col].isnull()].index.tolist()
            # Convert to 1-indexed human row numbers (header is row 1)
            human_rows = [r + 2 for r in null_rows]  # +1 for 0-index, +1 for header
            raise LoaderError(
                f"Null values found in column '{col}' at rows {human_rows} in {filepath}"
            )

    # Strip whitespace from string columns
    df = strip_whitespace(df)

    # Check for empty strings after stripping (only required columns)
    for col in REQUIRED_COLUMNS:
        empty_mask = df[col].astype(str).str.strip() == ""
        if empty_mask.any():
            empty_rows = df[empty_mask].index.tolist()
            human_rows = [r + 2 for r in empty_rows]
            raise LoaderError(
                f"Empty values found in column '{col}' at rows {human_rows} in {filepath}"
            )

    # Handle optional columns - email, department, year
    has_email = "email" in df.columns
    # Find department column (case-insensitive)
    dept_col = None
    for col in df.columns:
        if col.lower() in ("department", "dept"):
            dept_col = col
            break
    has_dept = dept_col is not None
    # Find year column
    year_col = None
    for col in df.columns:
        if col.lower() in ("year", "year_of_study", "study_year", "academic_year"):
            year_col = col
            break
    has_year = year_col is not None

    # Also check string 'nan' that may result from NaN conversion after strip
    participants: List[Participant] = []
    for idx, row in df.iterrows():
        human_row = idx + 2  # type: ignore
        try:
            # Handle potential float/int conversion
            name = str(row["name"]).strip()
            team = str(row["team"]).strip()
            email = str(row["email"]).strip() if has_email else ""
            department = str(row[dept_col]).strip() if has_dept else ""
            year = str(row[year_col]).strip() if has_year else ""

            # Skip if values became 'nan' string from float nan (only required fields)
            if name.lower() == "nan" or team.lower() == "nan":
                raise LoaderError(f"Null/NaN values at row {human_row} in {filepath}")
            if has_email and email.lower() == "nan":
                email = ""  # treat nan email as empty (optional)
            if has_dept and department.lower() == "nan":
                department = ""
            if has_year and year.lower() == "nan":
                year = ""
            # Clean year - if numeric float like "2.0" -> "2"
            if has_year and year and year.replace(".", "", 1).isdigit():
                # Remove .0
                try:
                    if "." in year:
                        year = str(int(float(year)))
                except:
                    pass

            p = Participant(name=name, team=team, email=email, department=department, year=year)
            participants.append(p)
        except LoaderError:
            raise
        except Exception as e:
            # Validation error from Participant
            raise LoaderError(f"Invalid participant data at row {human_row} in {filepath}: {e}") from e

    logger.info(f"Loaded {len(participants)} participants from {filepath}")
    return participants


def load_csv(filepath: str, encoding: str = "utf-8") -> List[Participant]:
    """Load participants from CSV file.

    Args:
        filepath: Path to CSV file.
        encoding: File encoding (default utf-8, tries utf-8-sig, latin-1 fallbacks).

    Returns:
        List of Participant objects.

    Raises:
        LoaderError: If file not found, invalid format, missing columns, null values.
    """
    if not os.path.exists(filepath):
        raise LoaderError(f"CSV file not found: {filepath}")

    # Try specified encoding first, then fallbacks
    encodings_to_try = [encoding] + [e for e in ENCODINGS if e != encoding]

    last_error = None
    for enc in encodings_to_try:
        try:
            df = pd.read_csv(filepath, encoding=enc)
            logger.debug(f"CSV loaded with encoding {enc}: {filepath} ({len(df)} rows)")
            return _validate_and_create_participants(df, filepath)
        except LoaderError:
            raise
        except UnicodeDecodeError as e:
            last_error = e
            logger.debug(f"Encoding {enc} failed for {filepath}: {e}")
            continue
        except Exception as e:
            raise LoaderError(f"Failed to load CSV {filepath}: {e}") from e

    raise LoaderError(f"Failed to decode CSV {filepath} with any encoding {encodings_to_try}: {last_error}")


def load_excel(filepath: str, sheet_name=0) -> List[Participant]:
    """Load participants from Excel file.

    Args:
        filepath: Path to Excel file (.xlsx).
        sheet_name: Sheet name or index (default 0 = first sheet).

    Returns:
        List of Participant objects.

    Raises:
        LoaderError: If file not found, invalid format, missing columns, null values.
    """
    if not os.path.exists(filepath):
        raise LoaderError(f"Excel file not found: {filepath}")

    try:
        df = pd.read_excel(filepath, sheet_name=sheet_name, engine="openpyxl")
        logger.debug(f"Excel loaded: {filepath} sheet={sheet_name} ({len(df)} rows)")
        return _validate_and_create_participants(df, filepath)
    except LoaderError:
        raise
    except Exception as e:
        raise LoaderError(f"Failed to load Excel {filepath}: {e}") from e


# --- Wide-format / Sparkverse-specific loader ---

def load_sparkverse(
    filepath: str,
    sheet_name=0,
    team_col: Optional[str] = None,
    name_cols: Optional[List[str]] = None,
) -> List[Participant]:
    """Load Sparkverse registrations (75 teams, 278 participants) or any wide-format sheet.

    Spreadsheet has one row per team with columns like:
      Team Name | Leader Name | M1 Name | M2 Name | M3 Name
    This function expands each row into 1 Participant per name column (278 total).

    For future sheets with different structures, specify columns via .env:
      CERT_COL_TEAM="Team Name"
      CERT_COL_NAMES="Leader Name,M1 Name,M2 Name,M3 Name"
    Or pass explicitly: load_sparkverse(path, team_col="Team Name", name_cols=["Leader Name", ...])

    Args:
        filepath: Path to .xlsx or .csv file.
        sheet_name: Sheet name/index for Excel (ignored for CSV).
        team_col: Column name for team. If None, reads from CERT_COL_TEAM env or defaults to "Team Name".
        name_cols: List of column names for participant names. If None, reads from CERT_COL_NAMES env or defaults to Leader/M1/M2/M3.

    Returns:
        List of Participant (name, team) - 278 for sparkverse.

    Raises:
        LoaderError: If file not found or columns missing.
    """
    if not os.path.exists(filepath):
        raise LoaderError(f"File not found: {filepath}")

    # Resolve column mapping from .env if not passed
    env_map = _get_env_column_mapping()
    if team_col is None:
        team_col = env_map.get("team_col", "Team Name")
    if name_cols is None:
        env_names = env_map.get("name_cols")
        if env_names:
            name_cols = [c.strip() for c in env_names.split(",") if c.strip()]
        else:
            name_cols = ["Leader Name", "M1 Name", "M2 Name", "M3 Name"]

    # Load dataframe
    try:
        if filepath.lower().endswith(".csv"):
            df = pd.read_csv(filepath)
        else:
            df = pd.read_excel(filepath, sheet_name=sheet_name, engine="openpyxl")
        logger.debug(f"Sparkverse loaded: {filepath} shape {df.shape} team_col={team_col} name_cols={name_cols}")
    except Exception as e:
        raise LoaderError(f"Failed to load file {filepath}: {e}") from e

    # Normalize column names strip
    df.columns = [str(c).strip() for c in df.columns]

    # Validate required columns exist
    missing = []
    if team_col not in df.columns:
        missing.append(team_col)
    for nc in name_cols:
        if nc not in df.columns:
            missing.append(nc)
    if missing:
        raise LoaderError(
            f"Missing required columns {missing} in {filepath}. Found: {list(df.columns)}. "
            f"Tip: Set correct mapping via .env: CERT_COL_TEAM and CERT_COL_NAMES"
        )

    participants: List[Participant] = []
    # dept/year not used per your latest instruction, but keep as empty
    for idx, row in df.iterrows():
        human_row = idx + 2  # 1-indexed with header
        team_val = str(row[team_col]).strip() if pd.notna(row[team_col]) else ""
        if not team_val or team_val.lower() == "nan":
            logger.warning(f"Skipping row {human_row}: empty team {team_col}")
            continue

        for name_col in name_cols:
            name_val = str(row[name_col]).strip() if pd.notna(row[name_col]) else ""
            if not name_val or name_val.lower() == "nan" or name_val == "":
                # M3 may be empty for 22 teams - skip silently
                if name_col == "M3 Name":
                    continue
                logger.debug(f"Skipping empty {name_col} at row {human_row}")
                continue
            try:
                p = Participant(name=name_val, team=team_val)
                participants.append(p)
                logger.debug(f"Added participant: {name_val} / {team_val} from {name_col} row {human_row}")
            except Exception as e:
                raise LoaderError(f"Invalid participant data at row {human_row} col {name_col}: {e}") from e

    logger.info(f"Loaded {len(participants)} participants from {filepath} (wide-format: {len(df)} teams -> {len(participants)} individuals)")
    return participants


def load_with_mapping(
    filepath: str,
    column_mapping: Dict[str, str],
    sheet_name=0,
) -> List[Participant]:
    """Generic loader with explicit column mapping for future sheets.

    Args:
        filepath: Path to file.
        column_mapping: Dict mapping participant fields to spreadsheet columns.
            Example: {"name": "Full Name", "team": "Team Name", "department": "Dept", "year": "Year"}
            Only "name" and "team" are required; department/year/email are optional.
        sheet_name: Sheet name for Excel.

    Returns:
        List of Participant.

    Raises:
        LoaderError: If mapping invalid or file not found.
    """
    if not os.path.exists(filepath):
        raise LoaderError(f"File not found: {filepath}")

    if "name" not in column_mapping or "team" not in column_mapping:
        raise LoaderError("column_mapping must contain at least 'name' and 'team' keys")

    # Load
    try:
        if filepath.lower().endswith(".csv"):
            df = pd.read_csv(filepath)
        else:
            df = pd.read_excel(filepath, sheet_name=sheet_name, engine="openpyxl")
        df.columns = [str(c).strip() for c in df.columns]
        logger.debug(f"Mapping load: {filepath} columns {list(df.columns)} mapping {column_mapping}")
    except Exception as e:
        raise LoaderError(f"Failed to load file {filepath}: {e}") from e

    # Validate mapping columns exist
    for field, col in column_mapping.items():
        if col not in df.columns:
            raise LoaderError(f"Column '{col}' for field '{field}' not found in {filepath}. Found: {list(df.columns)}")

    # Build participants
    participants: List[Participant] = []
    for idx, row in df.iterrows():
        human_row = idx + 2
        try:
            kwargs = {}
            for field, col in column_mapping.items():
                val = str(row[col]).strip() if pd.notna(row[col]) else ""
                if val.lower() == "nan":
                    val = ""
                kwargs[field] = val
            # Require at least name and team non-empty
            if not kwargs.get("name") or not kwargs.get("team"):
                logger.warning(f"Skipping row {human_row}: empty name/team")
                continue
            p = Participant(**kwargs)
            participants.append(p)
        except LoaderError:
            raise
        except Exception as e:
            raise LoaderError(f"Invalid participant at row {human_row}: {e}") from e

    logger.info(f"Loaded {len(participants)} participants via custom mapping from {filepath}")
    return participants
