#/usr/bin/env python

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

from optparse import OptionParser

###############################################################################
# This script takes as input the output of Mallet's Topical NGrams and returns
# as output a file formatted like the output of Mallet's LDA so that it can be
# easily imported into the database with dataset_import and analysis_import
###############################################################################

verbose = False
doc_mapping = dict()

def main(options):
    mapping_file = open(options.doc_mapping)
    for line in mapping_file:
        doc, path = line.split()
        doc_mapping[doc] = path

    headers, state_tokens = parse_mallet_file(options.input_file)

    new_tokens = convert_to_lda_tokens(state_tokens, options.duplicate_unigrams)

    outfile = open(options.output_file, 'w')
    outfile.write(''.join(headers))
    for token in new_tokens:
        outfile.write(token.output_as_lda_line())


class StateToken(object):
    """
    Class which holds all the information got from a MALLET topic state
    file.
    """

    @classmethod
    def create_from_line(cls, line):
        """
        Create a StateToken object from a Mallet TNG state file line

        Input line should have the following format:
        doc pos typeindex type bigrampossible? topic bigram
        """
        elements = line.split()
        token = cls()
        token.docindex = elements[0]
        token.docpath = doc_mapping[token.docindex]
        token.pos = int(elements[1])
        token.typeindex = int(elements[2])
        token.type = elements[3]
        token.bigrampossible = (int(elements[4]) == 1)
        token.topic = int(elements[5])
        token.bigram = (int(elements[6]) == 1)
        return token

    def __init__(self, token=None):
        if token:
            self.docindex = token.docindex
            self.docpath = token.docpath
            self.pos = token.pos
            self.typeindex = token.typeindex
            self.type = token.type
            self.bigrampossible = token.bigrampossible
            self.topic = token.topic
            self.bigram = token.bigram
        else:
            self.docindex = None
            self.docindex = None
            self.docpath = None
            self.pos = None
            self.typeindex = None
            self.type = None
            self.bigrampossible = None
            self.topic = None
            self.bigram = None

    def output_as_lda_line(self):
        return '%s %s %d %d %s %d\n' % (self.docindex, self.docpath, self.pos,
                self.typeindex, self.type, self.topic)


def parse_mallet_file(state_file):
    """
    Parse a Mallet TNG file and return a list of headers and a list of tokens.
    """
    state_tokens = []
    headers = []

    count = 0

    f = open(state_file, 'r')
    for line in f:
        count += 1
        if count % 5000 == 0:
            print count
        if line[0] == '#':
            headers.append(line)
        elif line:
            line = line.strip()
            state_tokens.append(StateToken.create_from_line(line))

    return headers, state_tokens


def convert_to_lda_tokens(state_tokens, duplicate_unigrams):
    """
    Convert the list of StateTokens into a new list of StateTokens that has the
    n-gram information inside of it.  duplicate_unigrams is a boolean that is
    described in the help information in the OptionParser below.
    """
    new_state_tokens = []

    if duplicate_unigrams:
        num_tokens = len(state_tokens)
        for i, token in enumerate(state_tokens):
            new_state_tokens.append(token)
            if i+1 < num_tokens and state_tokens[i+1].bigram:
                for ngram in extend_ngram(token, i, state_tokens):
                    new_state_tokens.append(ngram)
    else:
        for i, token in enumerate(state_tokens):
            if i == 0:
                cur_token = StateToken(token)
                continue
            if token.bigram == 1:
                cur_token.type += "_" + token.type
                cur_token.topic = token.topic
            else:
                new_state_tokens.append(cur_token)
                cur_token = StateToken(token)

    return new_state_tokens


def extend_ngram(cur_token, i, state_tokens):
    new_token = StateToken(cur_token)
    while i+1 < len(state_tokens) and state_tokens[i+1].bigram:
        new_token = StateToken(new_token)
        new_token.type += "_" + state_tokens[i+1].type
        new_token.topic = state_tokens[i+1].topic
        i += 1
        yield new_token


if __name__ == "__main__":
    parser = OptionParser()
    parser.add_option("-i", "--input-file",
            dest="input_file",
            help="Path to the input file",
            )
    parser.add_option("-m", "--doc-mapping",
            dest="doc_mapping",
            help="Document index to path mapping file (one line per document,"
            " formatted [index] [path])",
            )
    parser.add_option("-o", "--output-file",
            dest="output_file",
            help="Path to the output file",
            )
    parser.add_option("-d", "--duplicate-unigrams",
            dest="duplicate_unigrams",
            action="store_true",
            help="Either we can not count sub-ngrams when they are part of an"
            " ngram, or we can count them.  By default we do not count them."
            " Setting this option changes that behavior.",
            )
	
    options, args = parser.parse_args()
    main(options)


