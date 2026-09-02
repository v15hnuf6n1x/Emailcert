import os
import tempfile
import csv

import pytest

from emailcert.certgen.exceptions import LoaderError
from emailcert.certgen.loader import load_csv, load_excel


def test_load_csv_valid():
    participants = load_csv("tests/fixtures/participants.csv")
    assert len(participants) == 2
    assert participants[0].name == "John Doe"
    assert participants[1].team == "Team Beta"


def test_load_csv_alias_team_name():
    participants = load_csv("tests/fixtures/participants_alias.csv")
    assert len(participants) == 1
    assert participants[0].team == "Team Gamma"


def test_load_csv_bom():
    # UTF-8-BOM with unicode name
    participants = load_csv("tests/fixtures/bom.csv")
    assert len(participants) == 1
    # bom.csv contains José García -> normalized but stored as provided
    assert "Jose" in participants[0].name or "José" in participants[0].name


def test_load_csv_missing_column():
    with pytest.raises(LoaderError, match="Missing required columns"):
        load_csv("tests/fixtures/bad_missing.csv")


def test_load_csv_null_values():
    with pytest.raises(LoaderError, match="Null values|Empty values"):
        load_csv("tests/fixtures/bad_null.csv")


def test_load_csv_not_found():
    with pytest.raises(LoaderError, match="not found"):
        load_csv("nonexistent.csv")


def test_load_csv_empty_string_after_strip():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, newline="") as f:
        w = csv.writer(f)
        w.writerow(["name", "team", "email"])
        w.writerow(["   ", "Team", "a@b.com"])
        fname = f.name
    try:
        with pytest.raises(LoaderError, match="Empty values"):
            load_csv(fname)
    finally:
        os.unlink(fname)


def test_load_csv_invalid_participant_row():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, newline="") as f:
        w = csv.writer(f)
        w.writerow(["name", "team", "email"])
        w.writerow(["John@Invalid", "Team", "a@b.com"])
        fname = f.name
    try:
        with pytest.raises(LoaderError, match="Invalid participant"):
            load_csv(fname)
    finally:
        os.unlink(fname)


def test_load_excel_valid():
    participants = load_excel("tests/fixtures/participants.xlsx")
    assert len(participants) == 1
    assert participants[0].name == "Alice"


def test_load_excel_not_found():
    with pytest.raises(LoaderError, match="not found"):
        load_excel("nonexistent.xlsx")


def test_load_excel_missing_column():
    import pandas as pd

    with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as f:
        fname = f.name
    pd.DataFrame([{"name": "John", "email": "a@b.com"}]).to_excel(fname, index=False)
    try:
        with pytest.raises(LoaderError, match="Missing required columns"):
            load_excel(fname)
    finally:
        os.unlink(fname)


def test_load_csv_without_email():
    # Email is optional - CSV with only name,team should work
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, newline="") as f:
        w = csv.writer(f)
        w.writerow(["name", "team"])
        w.writerow(["John Doe", "Team Alpha"])
        fname = f.name
    try:
        participants = load_csv(fname)
        assert len(participants) == 1
        assert participants[0].name == "John Doe"
        assert participants[0].email == ""
    finally:
        os.unlink(fname)


def test_load_csv_whitespace_stripping():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, newline="") as f:
        w = csv.writer(f)
        w.writerow(["name", "team", "email"])
        w.writerow(["  John Doe  ", "  Team Alpha  ", "  john@example.com  "])
        fname = f.name
    try:
        participants = load_csv(fname)
        assert participants[0].name == "John Doe"
        assert participants[0].team == "Team Alpha"
        assert participants[0].email == "john@example.com"
    finally:
        os.unlink(fname)
