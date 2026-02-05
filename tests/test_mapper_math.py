import pytest
from jsonshift import Mapper


def test_math_add():
    spec = {
        "defaults": {
            "value": {
                "$add": {
                    "value": 10,
                    "by": 5
                }
            }
        }
    }

    out = Mapper().transform(spec, {})
    assert out["value"] == 15


def test_math_sub():
    spec = {
        "defaults": {
            "value": {
                "$sub": {
                    "value": 10,
                    "by": 3
                }
            }
        }
    }

    out = Mapper().transform(spec, {})
    assert out["value"] == 7


def test_math_mul():
    spec = {
        "defaults": {
            "value": {
                "$mul": {
                    "value": 4,
                    "by": 2.5
                }
            }
        }
    }

    out = Mapper().transform(spec, {})
    assert out["value"] == 10.0


def test_math_div():
    spec = {
        "defaults": {
            "value": {
                "$div": {
                    "value": 10,
                    "by": 2
                }
            }
        }
    }

    out = Mapper().transform(spec, {})
    assert out["value"] == 5


def test_division_by_zero_raises():
    spec = {
        "defaults": {
            "value": {
                "$div": {
                    "value": 10,
                    "by": 0
                }
            }
        }
    }

    with pytest.raises(ValueError):
        Mapper().transform(spec, {})