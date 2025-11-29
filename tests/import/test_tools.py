'''Test the basic tools'''

from topic_modeling import tools
from io import StringIO
import datetime

import pytest

def test_timer():
    out = StringIO()
    timer = tools.TimeLongThing(20, minor=2, major=10, target=out)
    s = datetime.datetime(2010, 1, 1)
    timer.start(s)
    for i in range(10):
        timer.inc(newtime=s + datetime.timedelta(seconds=i*5))
    assert out.getvalue() == '. . . .: 50% (10 of 20) elapsed: 45s expected rest: 45s\n'

@pytest.mark.xfail
def test_skip():
    out = StringIO()
    timer = tools.TimeLongThing(20, minor=2, major=10, target=out)
    s = datetime.datetime(2010, 1, 1)
    timer.start(s)
    timer.inc(10, newtime=s + datetime.timedelta(seconds=45))
    assert out.getvalue() == '. . . .: 50% (10 of 20) elapsed: 45s expected rest: 45s\n'


# vim: et sw=4 sts=4
