from jsonshift import Mapper
from datetime import date, datetime, time


def test_now_datetime():
    spec = {
        "defaults": {
            "meta.created_at": {"$now": "datetime"}
        }
    }

    out = Mapper().transform(spec, {})
    assert isinstance(out["meta"]["created_at"], datetime)


def test_now_date():
    spec = {
        "defaults": {
            "meta.created_date": {"$now": "date"}
        }
    }

    out = Mapper().transform(spec, {})
    assert isinstance(out["meta"]["created_date"], date)


def test_now_time():
    spec = {
        "defaults": {
            "meta.created_time": {"$now": "time"}
        }
    }

    out = Mapper().transform(spec, {})
    assert isinstance(out["meta"]["created_time"], time)


def test_now_inside_wildcard_defaults():
    spec = {
        "defaults": {
            "items[*].created_at": {"$now": "datetime"}
        }
    }

    out = Mapper().transform(spec, {})
    assert isinstance(out["items"][0]["created_at"], datetime)