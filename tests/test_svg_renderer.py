import os
import tempfile

import pytest
from PIL import Image

from emailcert.certgen import Participant, TemplateConfig
from emailcert.certgen.exceptions import TemplateFormatError
from emailcert.certgen.svg_renderer import render_svg
from emailcert.certgen.renderer import generate


@pytest.fixture
def participant():
    return Participant(name="Alice Wonder", team="Team Beta", email="alice@example.com")


@pytest.fixture
def config(tmp_path):
    return TemplateConfig(
        output_dir=str(tmp_path / "output"),
        svg_name_element_id="name",
        svg_team_element_id="team",
    )


@pytest.fixture
def svg_template(tmp_path):
    content = '''<svg width="1920" height="1080" xmlns="http://www.w3.org/2000/svg">
    <rect width="1920" height="1080" fill="white"/>
    <text id="name" x="960" y="350" font-size="60" text-anchor="middle" font-family="Arial">Placeholder</text>
    <text id="team" x="960" y="500" font-size="40" text-anchor="middle" font-family="Arial">Team</text>
</svg>'''
    path = str(tmp_path / "template.svg")
    with open(path, "w") as f:
        f.write(content)
    return path


@pytest.fixture
def svg_tspan_template(tmp_path):
    content = '''<svg width="1920" height="1080" xmlns="http://www.w3.org/2000/svg">
    <rect width="1920" height="1080" fill="white"/>
    <text id="name" x="960" y="350" font-size="60" text-anchor="middle"><tspan>Old</tspan></text>
    <text id="team" x="960" y="500" font-size="40" text-anchor="middle"><tspan>Old Team</tspan></text>
</svg>'''
    path = str(tmp_path / "template_tspan.svg")
    with open(path, "w") as f:
        f.write(content)
    return path


def test_render_svg_success(svg_template, participant, config):
    png_bytes, path = render_svg(participant, svg_template, config)
    assert len(png_bytes) > 0
    assert os.path.exists(path)
    im = Image.open(path)
    assert im.size == (1920, 1080)


def test_render_svg_tspan(svg_tspan_template, participant, config):
    png_bytes, path = render_svg(participant, svg_tspan_template, config)
    assert os.path.exists(path)
    assert len(png_bytes) > 0


def test_render_svg_via_generate(svg_template, participant, config):
    b, path = generate(participant, svg_template, config)
    assert os.path.exists(path)


def test_render_svg_missing_elements(participant, config, tmp_path):
    # Now renders via injection - template with no name/team ids should inject new elements
    bad = '''<svg width="1920" height="1080" xmlns="http://www.w3.org/2000/svg"><text id="other">Other</text></svg>'''
    path = str(tmp_path / "bad.svg")
    with open(path, "w") as f:
        f.write(bad)
    # Should now succeed via injection (for src/final.svg style embedded PNG templates)
    png_bytes, out = render_svg(participant, path, config)
    assert os.path.exists(out)
    assert len(png_bytes) > 0


def test_render_svg_invalid_xml(participant, config, tmp_path):
    path = str(tmp_path / "invalid.svg")
    with open(path, "w") as f:
        f.write("<svg><unclosed>")
    with pytest.raises(TemplateFormatError, match="Invalid SVG"):
        render_svg(participant, path, config)


def test_render_svg_not_found(participant, config):
    with pytest.raises(Exception):
        render_svg(participant, "nonexistent.svg", config)


def test_render_svg_no_namespace(svg_template, participant, tmp_path):
    # SVG without namespace should still work via fallback iter
    content = '''<svg width="800" height="600">
    <rect width="800" height="600" fill="white"/>
    <text id="name" x="400" y="200" font-size="40" text-anchor="middle">N</text>
    <text id="team" x="400" y="300" font-size="30" text-anchor="middle">T</text>
</svg>'''
    path = str(tmp_path / "no_ns.svg")
    with open(path, "w") as f:
        f.write(content)
    config = TemplateConfig(output_dir=str(tmp_path / "out"), svg_name_element_id="name", svg_team_element_id="team")
    png_bytes, out = render_svg(participant, path, config)
    assert os.path.exists(out)
