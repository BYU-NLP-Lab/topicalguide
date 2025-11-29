#!/usr/bin/env python

# The Topical Guide
# Copyright 2010-2011 Brigham Young University
#
# This file is part of the Topical Guide <http://nlp.cs.byu.edu/topic_browser>.
#
# The Topical Guide is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published by the
# Free Software Foundation, either version 3 of the License, or (at your
# option) any later version.
#
# The Topical Guide is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Affero General Public License
# for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with the Topical Guide.  If not, see <http://www.gnu.org/licenses/>.
#
# If you have inquiries regarding any further use of the Topical Guide, please
# contact the Copyright Licensing Office, Brigham Young University, 3760 HBLL,
# Provo, UT 84602, (801) 422-9339 or 422-3821, e-mail copyright@byu.edu.

from collections import defaultdict
from optparse import OptionParser

def main(state_file, base=''):
    words = get_word_list(state_file)
    if base:
        filename = base + '/words.txt'
    else:
        filename = 'words.txt'
    f = open(filename, 'w')
    f.write('\n'.join(words))
    word_index = make_word_dictionary(words)
    assignments = get_topic_word_assignments(state_file, word_index)
    if base:
        filename = base + '/assignments.txt'
    else:
        filename = 'assignments.txt'
    f = open(filename, 'w')
    f.write('\n'.join(assignments))


def get_word_list(state_filename):
    words = set()
    f = open(state_filename)
    for line in f:
        if line[0] == '#': continue
        word = line.split()[4]
        words.add(word)
    words = list(words)
    words.sort()
    return words


def make_word_dictionary(words):
    dictionary = dict()
    for i, word in enumerate(words):
        dictionary[word] = i
    return dictionary


def get_topic_word_assignments(state_filename, word_index):
    assignments = []
    f = open(state_filename)
    prevfilename = None
    counts = dict()
    for line in f:
        if line[0] == '#': continue
        _, filename, __, ___, word, topic = line.split()
        if not prevfilename:
            prevfilename = filename
        if prevfilename and filename != prevfilename:
            assignments.append(prevfilename + ' ' +
                    make_assignment_line(counts, word_index))
            counts = dict()
            prevfilename = filename
        topic = int(topic)
        if word not in counts:
            counts[word] = defaultdict(int)
        counts[word][topic] += 1
    assignments.append(prevfilename + ' ' +
            make_assignment_line(counts, word_index))
    return assignments


def make_assignment_line(counts, word_index):
    words = []
    for word in counts:
        topics = []
        for topic in counts[word]:
            topics.append((counts[word][topic], topic))
        topics.sort()
        topics.reverse()
        words.append((word, topics[0][1]))
    words.sort()
    return ' '.join('%s:%d' % (word_index[w[0]], w[1]) for w in words)


if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option('-s', '--state-file',
            dest='state_file',
            help='The state file (output from mallet, decompressed) to use as'
            ' input, containing topic assignments.  This must have the same'
            ' file order as the corpus file you are planning on using with'
            ' the turbo topics code',
            )
    options, args = parser.parse_args()
    main(options)

# vim: et sw=4 sts=4
