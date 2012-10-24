#!/usr/bin/env python
import datetime
import sys

def pseconds(seconds):
    if seconds < 60:
        return '%ds' % (int(seconds),)
    if seconds < 60*60:
        return '%d:%ds' % (seconds//60, int(seconds % 60))
    return '%d:%d:%ds' % (seconds // 60 // 60, seconds // 60 % 60, int(seconds % 60))

class TimeLongThing:
    '''A class to output helpful "% done" messages
    for long imports of things'''

    def __init__(self, total, minor=50, major=1000, target=sys.stderr, maxwait=None):
        '''Arguments:
            total: the total number of things to process.
            minor: the minor step - once every x, a '.' will be printed
            major: the major step - once every y, the time stats will be
                printed
            target: a file-like place to output
            maxwait: (None to disable) or a timediff - the max amout of time
                to wait before outputting
        '''
        self.total = total
        self.done = 0
        self.minor = minor
        self.major = major
        self.target = target
        self.start()

    def start(self):
        self.starttime = datetime.datetime.now()
        self.lasttime = self.starttime
        self.lastreporttime = self.starttime

    def inc(self, num=1, output=True):
        self.done += num
        if not output:
            return
        newtime = datetime.datetime.now()
        if self.done % self.major == 0:
            percent = self.done * 100 // self.total
            pdone = ': %d%% (%d of %d)' % (percent, self.done, self.total)
            timediff = newtime - self.lasttime
            elapsed = (newtime - self.starttime).total_seconds()
            left = (self.total - self.done) * (elapsed / self.done)
            ptime = 'elapsed: %s expected rest: %s' % (pseconds(elapsed), pseconds(left))
            print >> self.target, pdone, ptime
        elif self.done % self.minor == 0:
            print>>self.target, '.',
            self.lastreporttime = newtime
            self.target.flush()
        elif self.maxwait and (newtime - self.lastreporttime) > self.maxwait:
            self.minor = self.done % self.minor
            print>>self.target, '[taking a long time. minor interval now %d]' % self.minor
            self.lastreporttime = newtime
            self.target.flush()


# vim: et sw=4 sts=4
