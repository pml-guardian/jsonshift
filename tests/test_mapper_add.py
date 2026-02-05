from datetime import date, datetime, timedelta
from jsonshift import Mapper


def test_add_days_to_date():
    spec = {
        "defaults": {
            "due_date": {
                "$add": {
                    "value": {"$now": "date"},
                    "by": {"days": 5}
                }
            }
        }
    }

    out = Mapper().transform(spec, {})
    assert isinstance(out["due_date"], date)


def test_add_minutes_to_datetime():
    spec = {
        "defaults": {
            "expires_at": {
                "$add": {
                    "value": {"$now": "datetime"},
                    "by": {"minutes": 10}
                }
            }
        }
    }

    out = Mapper().transform(spec, {})
    assert isinstance(out["expires_at"], datetime)


def test_add_inside_wildcard_defaults():
    spec = {
        "defaults": {
            "items[*].created_at": {
                "$add": {
                    "value": {"$now": "datetime"},
                    "by": {"seconds": 30}
                }
            }
        }
    }

    out = Mapper().transform(spec, {})
    assert isinstance(out["items"][0]["created_at"], datetime)


def test_add_none_returns_none():
    spec = {
        "defaults": {
            "value": {
                "$add": {
                    "value": None,
                    "by": 10
                }
            }
        }
    }

    out = Mapper().transform(spec, {})
    assert out["value"] is None