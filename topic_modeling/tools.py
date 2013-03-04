#!/usr/bin/env python
import datetime
import sys
import os
import logging
import logging.config
import json

class BackendError(Exception):
    '''A signal that the backend import messed up'''

def setup_logging():
    '''load the configuration file.'''
    basedir = os.path.dirname(__file__)
    text = open(os.path.join(basedir, 'logging.conf')).read()
    config = json.loads(text)
    logging.config.dictConfig(config)

def pseconds(seconds):
    '''Format some number of seconds prettily:
        less than a minute: 00s
        less than an hour:  00:00s
        over an hour:       00:00:00s
    '''
    if seconds < 60:
        return '%ds' % (int(seconds),)
    if seconds < 60*60:
        return '%d:%ds' % (seconds//60, int(seconds % 60))
    return '%d:%d:%ds' % (seconds // 60 // 60, seconds // 60 % 60, int(seconds % 60))

class TimeLongThing:
    '''A class to output helpful "% done" messages for long iterative
    processes'''

    def __init__(self, total, minor=50, major=1000, target=sys.stderr, maxwait=None):
        '''Arguments:
            total:   the total number of things to process.
            minor:   the minor step - once every x, a '.' will be printed
            major:   the major step - once every y, the time stats will be
                     printed
            target:  a file-like place to output
            maxwait: (None to disable) or a timediff - the max amout of time
                     to wait before outputting (adjusts the minor
                     automatically
        '''

        self.total = total
        self.done = 0
        if minor < 1:
            minor = int(minor * total)
        if major < 1:
            major = int(major * total)
        self.minor = minor
        self.major = major
        self.target = target
        self.maxwait = maxwait
        self.start()

    def start(self, starttime=None):
        '''Initialize the time counters'''
        if starttime is None:
            starttime = datetime.datetime.now()
        self.starttime = starttime
        self.lasttime = self.starttime
        self.lastreporttime = self.starttime

    def inc(self, num=1, output=True, newtime=None):
        '''Increment the counter by num (default 1).

        Pass output=False to suppress the output and
        maxwait consideration
        '''
        self.done += num
        if not output:
            return
        if newtime is None:
            newtime = datetime.datetime.now()
        if self.done % self.major == 0:
            self.target.write(self.format_major(newtime))
        elif self.done % self.minor == 0:
            print >> self.target, '.',
            self.lastreporttime = newtime
            self.target.flush()
        elif self.maxwait and (newtime - self.lastreporttime) > self.maxwait:
            self.minor = self.done % self.minor
            print >> self.target, '[taking a long time. minor interval now %d]' % self.minor
            self.lastreporttime = newtime
            self.target.flush()

    def format_major(self, newtime=None):
        '''Generate the output string for a major interval.

        newtime defaults to datetime.datetime.now()
        '''
        if newtime is None:
            newtime = datetime.datetime.now()
        percent = self.done * 100 // self.total
        pdone = ': %d%% (%d of %d)' % (percent, self.done, self.total)
        timediff = newtime - self.lasttime
        elapsed = (newtime - self.starttime).total_seconds()
        left = (self.total - self.done) * (elapsed / self.done)
        ptime = 'elapsed: %s expected rest: %s' % (pseconds(elapsed), pseconds(left))
        return '%s %s\n' % (pdone, ptime)


# vim: et sw=4 sts=4
