from decimal import Decimal
from jsonshift import Mapper


def test_pow_simple():
    spec = {
        "defaults": {
            "value": {
                "$pow": {
                    "value": 2,
                    "by": 3
                }
            }
        }
    }

    out = Mapper().transform(spec, {})
    assert out["value"] == 8.0


def test_pow_with_string_numbers():
    spec = {
        "defaults": {
            "value": {
                "$pow": {
                    "value": "2",
                    "by": "4"
                }
            }
        }
    }

    out = Mapper().transform(spec, {})
    assert out["value"] == 16.0


def test_string_numeric_add():
    spec = {
        "defaults": {
            "value": {
                "$add": {
                    "value": "10.5",
                    "by": "2.5"
                }
            }
        }
    }

    out = Mapper().transform(spec, {})
    assert out["value"] == 13.0


def test_string_numeric_mul():
    spec = {
        "defaults": {
            "value": {
                "$mul": {
                    "value": "3",
                    "by": "4"
                }
            }
        }
    }

    out = Mapper().transform(spec, {})
    assert out["value"] == 12.0


def test_annual_rate_formula():
    spec = {
        "defaults": {
            "annual": {
                "$sub": {
                    "value": {
                        "$pow": {
                            "value": {
                                "$add": {
                                    "value": 1,
                                    "by": 0.04
                                }
                            },
                            "by": 12
                        }
                    },
                    "by": 1
                }
            }
        }
    }

    out = Mapper().transform(spec, {})

    assert round(out["annual"], 6) == round((1.04 ** 12) - 1, 6)


def test_format_number_default_brazil():
    spec = {
        "defaults": {
            "value": {
                "$format": {
                    "value": 10000,
                    "number": {
                        "decimals": 2,
                        "thousand": ".",
                        "decimal": ","
                    }
                }
            }
        }
    }

    out = Mapper().transform(spec, {})
    assert out["value"] == "10.000,00"


def test_format_number_no_decimals():
    spec = {
        "defaults": {
            "value": {
                "$format": {
                    "value": 1500000,
                    "number": {
                        "decimals": 0,
                        "thousand": ".",
                        "decimal": ","
                    }
                }
            }
        }
    }

    out = Mapper().transform(spec, {})
    assert out["value"] == "1.500.000"


def test_format_number_from_string():
    spec = {
        "defaults": {
            "value": {
                "$format": {
                    "value": "1234.5",
                    "number": {
                        "decimals": 2,
                        "thousand": ".",
                        "decimal": ","
                    }
                }
            }
        }
    }

    out = Mapper().transform(spec, {})
    assert out["value"] == "1.234,50"