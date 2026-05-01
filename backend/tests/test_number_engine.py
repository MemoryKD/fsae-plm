import pytest
from app.services.number_engine import NumberEngine


def test_generate_basic():
    engine = NumberEngine(prefix="FS", separator="-", digit_count=3)
    result = engine.generate(subsystem_code="SUS", sequence=1)
    assert result == "FS-SUS-001"


def test_generate_padding():
    engine = NumberEngine(prefix="FS", separator="-", digit_count=4)
    result = engine.generate(subsystem_code="BDY", sequence=42)
    assert result == "FS-BDY-0042"


def test_validate_valid():
    engine = NumberEngine(prefix="FS", separator="-", digit_count=3)
    assert engine.validate("FS-SUS-001") is True


def test_validate_invalid():
    engine = NumberEngine(prefix="FS", separator="-", digit_count=3)
    assert engine.validate("XX-SUS-001") is False
    assert engine.validate("FS-SUS-01") is False
    assert engine.validate("random-text") is False
