import os

from emailcert.certgen.config import TemplateConfig


def test_default_config():
    c = TemplateConfig()
    # Updated defaults for src/final.svg template 2172x724 (center 1086)
    assert c.name_position == (1086, 320)
    assert c.team_position == (1086, 400)
    assert c.team_name_position == (1086, 400)
    assert c.department_position == (1086, 480)
    assert c.year_position == (1086, 560)
    assert c.font_path == "arial.ttf"
    assert c.font_size_name == 60
    assert c.font_size_team == 40


def test_legacy_team_name_position_sync():
    c = TemplateConfig(team_name_position=(100, 200))
    assert c.team_position == (100, 200)
    c2 = TemplateConfig(name_position=(10, 10), team_position=(20, 20))
    assert c2.team_name_position == (20, 20)


def test_from_env_defaults(monkeypatch):
    # Clear env
    for key in list(os.environ.keys()):
        if key.startswith("CERT_"):
            monkeypatch.delenv(key, raising=False)
    c = TemplateConfig.from_env()
    assert c.output_dir == "certificates"
    assert c.font_size_name == 60


def test_from_env_overrides(monkeypatch):
    monkeypatch.setenv("CERT_OUTPUT_DIR", "/tmp/test_out")
    monkeypatch.setenv("CERT_FONT_SIZE_NAME", "80")
    monkeypatch.setenv("CERT_TEXT_COLOR_R", "255")
    monkeypatch.setenv("CERT_TEXT_COLOR_G", "100")
    monkeypatch.setenv("CERT_TEXT_COLOR_B", "50")
    monkeypatch.setenv("CERT_CENTER_TEXT", "false")
    c = TemplateConfig.from_env()
    assert c.output_dir == "/tmp/test_out"
    assert c.font_size_name == 80
    assert c.text_color == (255, 100, 50)
    assert c.center_text is False


def test_from_env_positions(monkeypatch):
    monkeypatch.setenv("CERT_NAME_POS_X", "100")
    monkeypatch.setenv("CERT_NAME_POS_Y", "200")
    c = TemplateConfig.from_env()
    assert c.name_position == (100, 200)
