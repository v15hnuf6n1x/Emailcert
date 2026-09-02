import os
import tempfile

import pytest
from PIL import Image

from emailcert.certgen.exceptions import OutputError, TemplateNotFoundError
from emailcert.certgen.models import Participant
from emailcert.certgen.utils import (
    ensure_output_dir,
    find_template,
    get_template_format,
    load_font,
    safe_filename,
    strip_whitespace,
    validate_participant,
    validate_template,
)


def test_safe_filename():
    assert safe_filename("John Doe") == "john_doe"
    assert safe_filename("Jane-Smith") == "jane_smith"
    assert safe_filename("José García") == "jose_garcia"
    assert safe_filename("John  Doe!!") == "john_doe"
    assert safe_filename("  __Test__  ") == "test"
    assert safe_filename("!!!") == "certificate"


def test_ensure_output_dir_creates(tmp_path):
    new_dir = str(tmp_path / "new_certs")
    result = ensure_output_dir(new_dir)
    assert os.path.exists(result)
    assert result == new_dir


def test_ensure_output_dir_fallback_on_file():
    with tempfile.NamedTemporaryFile(delete=False) as f:
        fname = f.name
    try:
        result = ensure_output_dir(fname)
        # Should fallback to certificates
        assert result == "certificates"
        assert os.path.exists(result)
    finally:
        os.unlink(fname)
        # cleanup fallback if created
        if os.path.exists("certificates") and not os.listdir("certificates"):
            os.rmdir("certificates")


def test_get_template_format():
    assert get_template_format("template.png") == "png"
    assert get_template_format("template.svg") == "svg"
    assert get_template_format("TEMPLATE.PNG") == "png"
    with pytest.raises(ValueError):
        get_template_format("template.pdf")
    with pytest.raises(ValueError):
        get_template_format("template")


def test_validate_template():
    assert validate_template("tests/fixtures/template.png") is True
    assert validate_template("nonexistent.png") is False
    # directory should be False
    assert validate_template("tests/fixtures") is False


def test_find_template_exact():
    # Should find exact path
    result = find_template("tests/fixtures/template.png")
    assert result == "tests/fixtures/template.png"


def test_find_template_fallback_events():
    os.makedirs("events/sparkverse", exist_ok=True)
    # Create temp file there
    Image.new("RGB", (100, 100), "white").save("events/sparkverse/fallback_utils.png")
    result = find_template("fallback_utils.png")
    assert result == "events/sparkverse/fallback_utils.png"
    os.remove("events/sparkverse/fallback_utils.png")


def test_find_template_not_found():
    with pytest.raises(TemplateNotFoundError):
        find_template("nonexistent_template_12345.png")


def test_find_template_campaign():
    os.makedirs("events/mycampaign", exist_ok=True)
    Image.new("RGB", (100, 100), "white").save("events/mycampaign/campaign_test.png")
    result = find_template("campaign_test.png", campaign_name="mycampaign")
    assert result == "events/mycampaign/campaign_test.png"
    os.remove("events/mycampaign/campaign_test.png")
    os.rmdir("events/mycampaign")


def test_load_font_fallback():
    # nonexistent font should fallback to default, not raise
    font = load_font("nonexistent_font_xyz.ttf", 20)
    assert font is not None
    # Should have getlength or getsize method
    assert hasattr(font, "getlength") or hasattr(font, "getsize")


def test_validate_participant_valid():
    p = Participant("John", "Team", "a@b.com")
    assert validate_participant(p) is True


def test_validate_participant_invalid_type():
    from emailcert.certgen.exceptions import InvalidParticipationError

    with pytest.raises(InvalidParticipationError):
        validate_participant("not a participant")


def test_strip_whitespace():
    import pandas as pd

    df = pd.DataFrame([{"name": "  John  ", "team": "  Alpha  ", "email": " a@b.com "}])
    df = strip_whitespace(df)
    assert df.iloc[0]["name"] == "John"
    assert df.iloc[0]["team"] == "Alpha"
    assert df.iloc[0]["email"] == "a@b.com"
