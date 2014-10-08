# coding: utf-8

import argparse
import os
import re
import sys
import numpy as np
import scipy.stats as stats
from StringIO import StringIO

'''SimpleBigramFinder uses likelihood ratios to determine bigrams'''
class SimpleBigramFinder(object):

    ''' * stop_file should be a path to a document containing stop words, one
    per line
        * corpus should be a directory where the corpus is kept; it will be
    searched recursively; the documents therein should contain only word content
        * token_regex is the regular expression used to find words
    '''
    def __init__(self, stop_file, corpus, token_regex='\w+'):
        # instance variables
        self.stopwords = {}
        self.corpus_dir = corpus
        self.interword_pattern = re.compile('[^'+token_regex+']', re.UNICODE)
        self.word_count = {}
        self.total_word_count = 0
        self.pair_count = {}
        self.bigrams = []
        # if a document's total vocabulary count to word count ratio is higher
        # than repeat_ratio, don't use the document as information for
        # recognizing bigrams
        self.repeat_ratio = 4
        # number of bigrams to remember during bigram creation
        self.bigram_limit = 500
        self.reference_bigrams = {}
        # need more than doc_count_threshold number of documents containing a
        # given word pair in order to count it as a bigram
        self.doc_count_threshold = 5
        # if the total number of word pair instances to total number of
        # documents containing the word pair ratio is higher than
        # infrequency_ratio, do not count the word pair as a bigram
        self.infrequency_ratio = 4

        # instance initialization
        self._register_stopwords(stop_file)

    def _register_stopwords(self, stop_file):
        self.stopwords = {}
        if not stop_file:
            return
        with open(stop_file, 'r') as ifh:
            for line in ifh:
                self.stopwords[line.strip().lower()] = True

    def run_bigram_finder(self):
        self.find_bigrams()
        self.print_bigrams()

    def print_bigrams(self):
        if not self.bigrams:
            print "No bigrams:  did you forget to call find_bigrams()?"
            return
        for (stat, pair_count, doc_count, w1, w2) in self.bigrams:
            print str(stat)+'\t'+str(pair_count)+'\t'+doc_count+'\t'+w1+'\t'+w2

    def _next_word_char(self, pos, tlength, text):
        i = pos
        while i < tlength:
            if not self.interword_pattern.match(text[i]):
                break
            i += 1
        return i

    def _next_not_word_char(self, pos, tlength, text):
        i = pos
        while i < tlength:
            if self.interword_pattern.match(text[i]):
                break
            i += 1
        return i

    def combine_bigrams(self, text):
        if not self.reference_bigrams:
            print 'No bigrams to combine'
            return
        result = StringIO()
        tlength = len(text)
        start_word1 = self._next_word_char(0, tlength, text)
        # end is actually the position immediately after the end of the word
        end_word1 = self._next_not_word_char(start_word1, tlength, text)
        result.write(text[0:start_word1])
        while start_word1 < tlength:
            start_word2 = self._next_word_char(end_word1, tlength, text)
            end_word2 = self._next_not_word_char(start_word2, tlength, text)
            w1 = text[start_word1:end_word1]
            interword = text[end_word1:start_word2]
            if start_word2 >= tlength:
                result.write(w1)
                result.write(interword)
                break
            elif (w1.lower(),text[start_word2:end_word2].lower()) in self.reference_bigrams:
                result.write(w1)
                result.write('_')
                ''' Doing things this way allows a chain of bigrams to all get
                strung together.  I think that this is the behavior we want.
                However, it'll be a pain getting newlines to work out nicely, if
                the bigram goes over lines. '''
            else:
                result.write(w1)
                result.write(interword)
            start_word1 = start_word2
            end_word1 = end_word2
        rv = result.getvalue()
        result.close()
        return rv

    def find_bigrams(self):
        self.word_count = {}
        self.total_word_count = 0
        self.pair_count = {}
        for root, dirs, files in os.walk(self.corpus_dir):
            for f in files:
                self._analyze_file(os.path.join(root, f))
        self._enumerate_bigrams()

    def _analyze_file(self, file_path):
        if self._file_is_garbage(file_path):
            return
        curWord = ''
        nextWord = ''
        for w in self._generate_next_word(file_path):
            if w in self.stopwords:
                curWord = ''
                nextWord = ''
                continue
            if not curWord:
                curWord = w
            elif not nextWord:
                nextWord = w
                self._increment_pair_count(curWord, nextWord, file_path)
                curWord = nextWord
                nextWord = ''
            if curWord:
                self._increment_word_count(curWord)

    def _file_is_garbage(self, file_path):
        counts = {}
        with open(file_path, 'r') as ifh:
            for line in ifh:
                for word in self.interword_pattern.split(line):
                    if not word:
                        continue
                    w = word.lower().strip()
                    if w not in counts:
                        counts[w] = 1
                    else:
                        counts[w] += 1
        total = 0
        for w in counts:
            total += counts[w]
        if total == 0:
            return False
        if float(total)/len(counts) > self.repeat_ratio:
            return True
        return False

    def _generate_next_word(self, file_path):
        '''Note that there is no metadata check'''
        with open(file_path, 'r') as ifh:
            while True:
                line = ifh.next()
                for w in self.interword_pattern.split(line):
                    if not w:
                        continue
                    self.total_word_count += 1
                    yield w.lower().strip()

    def _increment_word_count(self, word):
        if word in self.word_count:
            self.word_count[word] += 1
        else:
            self.word_count[word] = 1

    def _increment_pair_count(self, w1, w2, file_path):
        if w1 not in self.pair_count:
            self.pair_count[w1] = {}
            self.pair_count[w1][w2] = []
            self.pair_count[w1][w2].append(1)
            self.pair_count[w1][w2].append({})
            self.pair_count[w1][w2][1][file_path] = True
        elif w2 not in self.pair_count[w1]:
            self.pair_count[w1][w2] = []
            self.pair_count[w1][w2].append(1)
            self.pair_count[w1][w2].append({})
            self.pair_count[w1][w2][1][file_path] = True
        else:
            self.pair_count[w1][w2][0] += 1
            self.pair_count[w1][w2][1][file_path] = True

    def _enumerate_bigrams(self):
        self.bigrams = []
        self.reference_bigrams = {}
        for w1 in self.pair_count:
            for w2 in self.pair_count[w1]:
                doc_count = len(self.pair_count[w1][w2][1])
                if doc_count < self.doc_count_threshold:
                    continue
                word_pair_count = self.pair_count[w1][w2][0]
                if float(word_pair_count)/doc_count > self.infrequency_ratio:
                    continue
                stat = self._analyze_bigram(w1, w2)
                self._record_bigram(stat, word_pair_count,
                    str(doc_count), w1, w2)
        self.bigrams.sort()
        self.bigrams.reverse()
        for i in xrange(0,self.bigram_limit):
            self.reference_bigrams[(self.bigrams[i][3],self.bigrams[i][4])] = \
                    True

    def _record_bigram(self, stat, pair_count, doc_count, w1, w2):
        self.bigrams.append((stat, pair_count, doc_count, w1, w2))

    def _analyze_bigram(self, w1, w2):
        ''' bigram contingency table (p. 169 Manning and Shütze)
            w1  ~w1
        w2  a   b
        ~w2 c   d
        '''
        a = self.pair_count[w1][w2][0]
        b = self.word_count[w2] - a
        c = self.word_count[w1] - a
        d = self.total_word_count - a
        obs = np.array([[a,b],
                        [c,d]])
        g, p, dof, expctd = stats.chi2_contingency(obs,
                lambda_='log-likelihood')
        return g    # based on the source code, the -2 has already been
                    # multiplied in


if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog='SimpleBigramFinder',
            description='A program that uses likelihood ratios across a '
            'corpus to determine whether two neighboring words are a '
            'bigram', add_help=True)
    parser.add_argument('-s', '--stop', type=str, action='store',
            help='Specify a file which contains stopwords; each stopword '
            'should occupy its own line in the file.', default='')
    parser.add_argument('corpus', type=str, action='store', help='Specify '
            'the directory where the corpus is found.  SimpleBigramFinder '
            'will search the directory recursively for documents.')
    args = parser.parse_args()

    sbf = SimpleBigramFinder(args.stop, args.corpus)
    sbf.run_bigram_finder()
