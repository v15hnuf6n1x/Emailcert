import pytest

from emailcert.certgen.exceptions import InvalidParticipationError, InvalidParticipantError
from emailcert.certgen.models import Participant


def test_valid_participant():
    p = Participant(name="John Doe", team="Team Alpha", email="john@example.com")
    assert p.name == "John Doe"
    assert p.team == "Team Alpha"
    assert p.email == "john@example.com"
    assert p.team_name == "Team Alpha"  # alias


def test_valid_with_team_name_alias():
    p = Participant(name="Jane Smith", team_name="Team Beta", email="jane@example.com")
    assert p.team == "Team Beta"
    assert p.team_name == "Team Beta"


def test_valid_with_spaces_and_hyphens():
    p = Participant(name="Anne-Marie", team="Team 1", email="a@b.com")
    assert p.name == "Anne-Marie"


def test_invalid_empty_name():
    with pytest.raises(InvalidParticipationError):
        Participant(name="", team="Team", email="a@b.com")
    with pytest.raises(InvalidParticipationError):
        Participant(name="   ", team="Team", email="a@b.com")


def test_invalid_name_too_long():
    with pytest.raises(InvalidParticipationError):
        Participant(name="A" * 101, team="Team", email="a@b.com")


def test_invalid_name_bad_chars():
    with pytest.raises(InvalidParticipationError):
        Participant(name="John@Doe", team="Team", email="a@b.com")
    with pytest.raises(InvalidParticipationError):
        Participant(name="John_Doe", team="Team", email="a@b.com")


def test_invalid_empty_team():
    with pytest.raises(InvalidParticipationError):
        Participant(name="John", team="", email="a@b.com")


def test_invalid_team_too_long():
    with pytest.raises(InvalidParticipationError):
        Participant(name="John", team="A" * 101, email="a@b.com")


def test_invalid_email_missing_at():
    with pytest.raises(InvalidParticipationError):
        Participant(name="John", team="Team", email="invalid")


def test_valid_without_email():
    # Email is optional now
    p = Participant(name="John", team="Team", email="")
    assert p.email == ""
    p2 = Participant(name="John", team="Team")
    assert p2.email == ""
    p3 = Participant(name="John", team="Team", email="valid@example.com")
    assert p3.email == "valid@example.com"


def test_team_name_setter():
    p = Participant(name="John", team="Alpha", email="a@b.com")
    p.team_name = "Beta"
    assert p.team == "Beta"


def test_invalid_participant_error_alias():
    # Both exception names should work
    assert issubclass(InvalidParticipantError, InvalidParticipationError)
    with pytest.raises(InvalidParticipantError):
        Participant(name="", team="Team", email="a@b.com")


def test_whitespace_stripping():
    p = Participant(name="  John Doe  ", team="  Team Alpha  ", email="  john@example.com  ")
    assert p.name == "John Doe"
    assert p.team == "Team Alpha"
    assert p.email == "john@example.com"
