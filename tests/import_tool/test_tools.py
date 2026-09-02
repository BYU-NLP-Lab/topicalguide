'''Test the basic tools'''

from io import StringIO

import pytest

from import_tool import tools


@pytest.fixture
def fake_clock(monkeypatch):
    """Replace time.time() in import_tool.tools with a clock we control.

    Returns a one-element list; assign to element 0 to set the current time.
    """
    now = [0.0]
    monkeypatch.setattr(tools.time, 'time', lambda: now[0])
    return now


def test_timer(fake_clock):
    out = StringIO()
    timer = tools.VerboseTimer(20, minor=2, major=10, target=out)
    for i in range(10):
        fake_clock[0] = (i + 1) * 4.5
        timer.tick()
    assert out.getvalue() == '....: 50% (10 of 20) elapsed: 45 expected rest: 45\n'


def test_timer_multi_step_tick(fake_clock):
    """A single tick() spanning the whole major interval still reports."""
    out = StringIO()
    timer = tools.VerboseTimer(20, minor=2, major=10, target=out)
    fake_clock[0] = 45.0
    timer.tick(10)
    assert out.getvalue() == ': 50% (10 of 20) elapsed: 45 expected rest: 45\n'


def test_timer_derives_intervals_from_total(fake_clock):
    """minor/major default to 1% and 10% of the total."""
    timer = tools.VerboseTimer(1000, target=StringIO())
    assert timer.minor == 10
    assert timer.major == 100


def test_timer_intervals_never_zero(fake_clock):
    """A total too small for the 1%/10% defaults still yields usable steps."""
    timer = tools.VerboseTimer(5, target=StringIO())
    assert timer.minor == 1
    assert timer.major == 1


# vim: et sw=4 sts=4
