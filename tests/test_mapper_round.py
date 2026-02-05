from jsonshift import Mapper


def test_round_simple():
    spec = {
        "defaults": {
            "value": {
                "$round": {
                    "value": 3.14159,
                    "ndigits": 2
                }
            }
        }
    }

    out = Mapper().transform(spec, {})
    assert out["value"] == 3.14


def test_round_after_multiply():
    spec = {
        "defaults": {
            "value": {
                "$round": {
                    "value": {
                        "$mul": {
                            "value": 0.920066,
                            "by": 100
                        }
                    },
                    "ndigits": 2
                }
            }
        }
    }

    out = Mapper().transform(spec, {})
    assert out["value"] == 92.01