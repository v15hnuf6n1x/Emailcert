import re
from dataclasses import dataclass, field

from .constants import (
    MAX_DEPARTMENT_LENGTH,
    MAX_NAME_LENGTH,
    MAX_TEAM_LENGTH,
    MAX_YEAR_LENGTH,
    PATTERN_DEPARTMENT,
    PATTERN_NAME_TEAM,
    PATTERN_YEAR,
)
from .exceptions import InvalidParticipantError

# Keep legacy name for compatibility
InvalidParticipationError = InvalidParticipantError


@dataclass(init=False)
class Participant:
    """Participant data with strict validation - name and team required, dept/year optional.

    Attributes:
        name: Participant name (1-100 chars, alphanumeric + space/hyphen).
        team: Team name (1-100 chars, alphanumeric + space/hyphen).
        department: Department name (1-100 chars, alphanumeric + space/hyphen/dot).
        year: Year of study (1-20 chars, e.g., '2nd Year', '3', '2024').
        email: Optional participant email, if provided must contain @.
        team_name: Alias for team (backward compat).
        dept: Alias for department.
    """

    name: str
    team: str
    email: str = ""
    department: str = ""
    year: str = ""

    def __init__(
        self,
        name: str,
        team: str = "",
        email: str = "",
        team_name: str = "",
        department: str = "",
        dept: str = "",
        year: str = "",
        **kwargs: str,
    ) -> None:
        # Support aliases
        if team_name and not team:
            team = team_name
        if not team and "team_name" in kwargs:
            team = kwargs["team_name"]
        # Department aliases: department, dept, Department, Dept
        dept_val = department or dept or kwargs.get("department", "") or kwargs.get("dept", "") or kwargs.get("Department", "") or kwargs.get("Dept", "")
        # Year aliases: year, Year, year_of_study, Year_of_Study
        year_val = year or kwargs.get("year", "") or kwargs.get("Year", "") or kwargs.get("year_of_study", "") or kwargs.get("Year_of_Study", "") or kwargs.get("YEAR", "")

        # Strip whitespace early
        self.name = name.strip() if isinstance(name, str) else str(name).strip()
        self.team = team.strip() if isinstance(team, str) else str(team).strip()
        self.email = email.strip() if isinstance(email, str) else str(email).strip()
        self.department = dept_val.strip() if isinstance(dept_val, str) else str(dept_val).strip()
        self.year = year_val.strip() if isinstance(year_val, str) else str(year_val).strip()

        # Support email from kwargs if not provided
        if not self.email and "email" in kwargs:
            val = kwargs["email"]
            self.email = val.strip() if isinstance(val, str) else str(val).strip()

        # Support department/year from alternative column names in kwargs (case-insensitive already handled)
        for k, v in kwargs.items():
            kl = k.lower()
            if kl in ("department", "dept") and not self.department:
                self.department = str(v).strip()
            if kl in ("year", "year_of_study", "study_year", "academic_year") and not self.year:
                self.year = str(v).strip()

        self.__post_init__()

    def __post_init__(self) -> None:
        errors = []

        # Name validation
        if not self.name or not self.name.strip():
            raise InvalidParticipantError("Participant name cannot be empty")
        if not (1 <= len(self.name) <= MAX_NAME_LENGTH):
            raise InvalidParticipantError(
                f"Participant name must be 1-{MAX_NAME_LENGTH} chars, got {len(self.name)}"
            )
        if not re.match(PATTERN_NAME_TEAM, self.name):
            raise InvalidParticipantError(
                "Name must be alphanumeric/space/hyphen only"
            )

        # Team validation (support alias)
        team_val = self.team
        if not team_val or not team_val.strip():
            raise InvalidParticipantError("Team name cannot be empty")
        if not (1 <= len(team_val) <= MAX_TEAM_LENGTH):
            raise InvalidParticipantError(
                f"Team must be 1-{MAX_TEAM_LENGTH} chars, got {len(team_val)}"
            )
        if not re.match(PATTERN_NAME_TEAM, team_val):
            raise InvalidParticipantError(
                "Team must be alphanumeric/space/hyphen only"
            )

        # Department validation - optional
        if self.department and self.department.strip():
            if not (1 <= len(self.department) <= MAX_DEPARTMENT_LENGTH):
                raise InvalidParticipantError(
                    f"Department must be 1-{MAX_DEPARTMENT_LENGTH} chars, got {len(self.department)}"
                )
            if not re.match(PATTERN_DEPARTMENT, self.department):
                raise InvalidParticipantError(
                    "Department must be alphanumeric/space/hyphen/dot only"
                )

        # Year validation - optional
        if self.year and self.year.strip():
            if not (1 <= len(self.year) <= MAX_YEAR_LENGTH):
                raise InvalidParticipantError(
                    f"Year must be 1-{MAX_YEAR_LENGTH} chars, got {len(self.year)}"
                )
            if not re.match(PATTERN_YEAR, self.year):
                raise InvalidParticipantError("Year must be alphanumeric/space/hyphen/slash only")

        # Email validation - optional, only validate if provided
        if self.email and self.email.strip():
            if "@" not in self.email:
                raise InvalidParticipantError("Email must contain @")

    @property
    def team_name(self) -> str:
        """Alias for team to maintain backward compatibility."""
        return self.team

    @team_name.setter
    def team_name(self, value: str) -> None:
        self.team = value

    @property
    def dept(self) -> str:
        """Alias for department."""
        return self.department

    @dept.setter
    def dept(self, value: str) -> None:
        self.department = value
