from __future__ import division, print_function, unicode_literals
import sys
import time


class VerboseTimer(object):
    """A class to output helpful "% done" messages for long iterative
    processes."""

    def __init__(self, total, minor=0, major=0, target=sys.stdout, maxwait=None):
        """Arguments:
            total:   the total number of things to process.
            minor:   the minor step - once every x, a '.' will be printed
            major:   the major step - once every y, the time stats will be
                     printed
            target:  a file-like place to output
            maxwait: (None to disable) or a timediff - the max amout of time
                     to wait before outputting (adjusts the minor
                     automatically
        """
        self.total = total
        self.done = 0
        if minor < 1:
            minor = int(total*0.01)
        if minor == 0:
            minor = 1
        if major < 1:
            major = int(total*0.1)
        if major == 0:
            major = 1
        self.minor = minor
        self.major = major
        self.target = target
        
        self.starttime = time.time()
    
    def tick(self, num=1):
        """Increment the counter by num (default 1)."""
        self.done += num
        if self.done % self.major == 0:
            self.target.write(self.format_major())
            self.target.flush()
        elif self.done % self.minor == 0:
            self.target.write('.')
            self.target.flush()

    def format_major(self):
        """Generate the output string for a major interval."""
        percent = self.done * 100 // self.total
        pdone = ': %d%% (%d of %d)' % (percent, self.done, self.total)
        now = time.time()
        elapsed = now - self.starttime
        left = (self.total - self.done) * (elapsed / self.done)
        ptime = 'elapsed: %d expected rest: %d' % (int(elapsed), int(left))
        return '%s %s\n' % (pdone, ptime)
