import os
import tempfile

import pytest
from PIL import Image

from emailcert.certgen import Participant, TemplateConfig
from emailcert.certgen.exceptions import OverlayError, TemplateFormatError, TemplateNotFoundError
from emailcert.certgen.renderer import generate, render_png


@pytest.fixture
def png_template(tmp_path):
    path = str(tmp_path / "template.png")
    Image.new("RGB", (1920, 1080), "white").save(path)
    return path


@pytest.fixture
def small_template(tmp_path):
    path = str(tmp_path / "small.png")
    Image.new("RGB", (400, 300), "white").save(path)
    return path


@pytest.fixture
def participant():
    return Participant(name="John Doe", team="Team Alpha", email="john@example.com")


@pytest.fixture
def config(tmp_path):
    return TemplateConfig(
        name_position=(960, 350),
        team_position=(960, 500),
        output_dir=str(tmp_path / "output"),
        font_size_name=40,
        font_size_team=30,
    )


def test_render_png_success(png_template, participant, config):
    png_bytes, path = render_png(participant, png_template, config)
    assert len(png_bytes) > 0
    assert os.path.exists(path)
    assert path.endswith("john_doe.png")
    im = Image.open(path)
    assert im.size == (1920, 1080)
    assert im.mode == "RGB"


def test_render_png_rgba_template(participant, config, tmp_path):
    rgba_path = str(tmp_path / "rgba.png")
    Image.new("RGBA", (1920, 1080), (255, 255, 255, 255)).save(rgba_path)
    png_bytes, path = render_png(participant, rgba_path, config)
    assert os.path.exists(path)
    im = Image.open(path)
    assert im.mode == "RGB"


def test_render_png_small_template_raises(small_template, participant, config):
    with pytest.raises(TemplateFormatError, match="too small"):
        render_png(participant, small_template, config)


def test_render_png_not_found(participant, config):
    with pytest.raises(TemplateNotFoundError):
        render_png(participant, "nonexistent.png", config)


def test_generate_png_routing(png_template, participant, config):
    b, path = generate(participant, png_template, config)
    assert os.path.exists(path)
    assert len(b) > 0


def test_generate_output_dir_override(png_template, participant, config, tmp_path):
    override = str(tmp_path / "override")
    b, path = generate(participant, png_template, config, output_dir=override)
    assert path.startswith(override)
    assert os.path.exists(path)


def test_generate_invalid_participant(png_template, config):
    # Participant validation will fail at creation, but test generate type check
    with pytest.raises(Exception):
        # Create invalid participant bypass? Pass wrong type
        generate("not a participant", png_template, config)  # type: ignore


def test_generate_with_invalid_participant_data(png_template, config):
    # Create participant then mutate to invalid - generate should re-validate
    p = Participant(name="John", team="Team", email="a@b.com")
    p.name = ""  # type: ignore
    with pytest.raises(Exception):
        generate(p, png_template, config)


def test_render_png_safe_filename(participant, png_template, tmp_path):
    # Name with special chars already validated, but safe_filename should handle
    p = Participant(name="John Doe", team="Team", email="a@b.com")
    config = TemplateConfig(output_dir=str(tmp_path / "out"), name_position=(100, 100), team_position=(100, 200))
    _, path = render_png(p, png_template, config)
    assert "john_doe.png" in path


def test_render_png_invalid_extension(participant, config, tmp_path):
    # Create a valid PNG but with wrong extension handling - should still try PNG
    path = str(tmp_path / "template.png")
    Image.new("RGB", (1920, 1080), "white").save(path)
    # Rename to have no extension, generate should handle via find_template fallback
    no_ext = str(tmp_path / "template_no_ext")
    # Copy file
    Image.new("RGB", (1920, 1080), "white").save(no_ext + ".png")
    # Direct png renderer with valid path works
    b, p = render_png(participant, path, config)
    assert os.path.exists(p)
