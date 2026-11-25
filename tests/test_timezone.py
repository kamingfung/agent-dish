"""Days are cut at local midnight, not UTC midnight. Each test sets the time zone for itself."""

import datetime
import time

import pytest

from agent_dish.cli import parse_since
from agent_dish.themes import colony_names, day_start, local_day

pytestmark = pytest.mark.skipif(not hasattr(time, "tzset"), reason="needs time.tzset (not on Windows)")


@pytest.fixture
def tz(monkeypatch):
    def use(name):
        monkeypatch.setenv("TZ", name)
        time.tzset()

    yield use
    monkeypatch.undo()
    time.tzset()


def utc(y, mo, d, h=0, mi=0):
    return datetime.datetime(y, mo, d, h, mi, tzinfo=datetime.timezone.utc).timestamp()


def test_parse_since_is_local_midnight(tz):
    tz("UTC")
    assert parse_since("2026-10-01") == 1_790_812_800
    tz("America/New_York")  # EDT, UTC-4 in October
    assert parse_since("2026-10-01") == 1_790_812_800 + 4 * 3600
    tz("Asia/Tokyo")  # UTC+9
    assert parse_since("2026-10-01") == 1_790_812_800 - 9 * 3600


def test_late_evening_belongs_to_the_day_you_lived_it(tz):
    t = utc(2026, 1, 15, 3, 30)  # 22:30 on Jan 14 in New York, 12:30 on Jan 15 in Tokyo
    tz("America/New_York")
    ny = local_day(t)
    tz("Asia/Tokyo")
    tokyo = local_day(t)
    tz("UTC")
    assert local_day(t) == tokyo and ny == tokyo - 1


def test_day_start_inverts_local_day_even_across_a_clock_change(tz):
    tz("America/New_York")
    t = utc(2026, 3, 8, 12)  # the day the clocks go forward: that day has 23 hours
    d = local_day(t)
    assert day_start(d) <= t < day_start(d + 1)
    assert day_start(d + 1) - day_start(d) == 23 * 3600
    assert local_day(day_start(d)) == d and local_day(day_start(d + 1) - 1) == d


def test_colony_titles_change_on_local_days(tz):
    tz("Asia/Tokyo")
    names = colony_names({}, {"s1": "alpha report"}, 100, 101)
    assert names["alpha report"][0][0] == day_start(100)
