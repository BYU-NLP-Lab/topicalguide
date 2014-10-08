# coding: utf-8

import argparse
import os
import re
import sys
import numpy as np
import scipy.stats as stats
from StringIO import StringIO


class SimpleBigramFinder(object):
    '''SimpleBigramFinder uses likelihood ratios to determine bigrams.'''
    
    def __init__(self, stopwords={}, token_regex='\w+'):
        """Create a SimpleBigramFinder.
        * stopwords is a dictionary where the keys are stopwords
        * token_regex is the regular expression used to find word tokens
        """
        # instance variables
        self.stopwords = stopwords
        self.token_regex_pattern = re.compile(token_regex, re.UNICODE)
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
        self.infrequency_ratio = 10
    
    def train(self, text_iterator):
        """Train the bigram finder.
        text_iterator - An iterator that returns a tuple (identifier, text), 
                        where identifier is a unique string and text is the text to be processed.
        Return nothing.
        """
        self.word_count = {}
        self.total_word_count = 0
        self.pair_count = {}
        for identifier, text in text_iterator:
            self._analyze_text(identifier, text)
        self._enumerate_bigrams()
    
    def print_bigrams(self):
        if not self.bigrams:
            print "No bigrams."
            return
        for (stat, pair_count, doc_count, w1, w2) in self.bigrams:
            print str(stat)+'\t'+str(pair_count)+'\t'+doc_count+'\t'+w1+'\t'+w2
    
    def combine_bigrams(self, text):
        if not self.reference_bigrams:
            print 'No bigrams to combine.'
            return text
        # convert the text to an array of tokens
        tokens = []
        previous_index = 0
        for match in self.token_regex_pattern.finditer(text):
            word_type = match.group()
            current_index = match.start()
            end_index = current_index + len(word_type)
            if current_index > previous_index:
                tokens.append((text[previous_index: current_index], False))
            tokens.append((word_type, True))
            previous_index = end_index
        if previous_index < len(text):
            tokens.append((text[previous_index:], False))
        
        # find and replace bigrams
        result = StringIO()
        is_searching = False
        token_count = len(tokens)
        word1_index = 0
        interword_index = 0
        word2_index = 0
        while word1_index + 2 < token_count:
            w1_token = tokens[word1_index]
            result.write(w1_token[0])
            if w1_token[1] and w1_token[0] not in self.stopwords:
                # fork and look for word 2
                interword_index = word1_index + 1
                interword_token = tokens[interword_index]
                # make sure we have a valid intermediate token
                if interword_token[1]: # TODO check for white space only?
                    word1_index += 1
                else:
                    word2_index = word1_index + 2
                    w2_token = tokens[word2_index]
                    # check that the second token is a valid word
                    if w2_token[1] and w2_token[0] not in self.stopwords:
                        # finally we check if the bigram exists
                        if (w1_token[0].lower(), w2_token[0].lower()) in self.reference_bigrams:
                            result.write('_')
                        else:
                            result.write(interword_token[0])
                        word1_index += 2
                    else:
                        word1_index += 1
            else:
                # continue looking
                word1_index += 1
        # clean up remaining tokens
        while word1_index < token_count:
            result.write(tokens[word1_index][0])
            word1_index += 1
        rv = result.getvalue()
        result.close()
        return rv
    
    def _analyze_text(self, identifier, text):
        if self._is_text_garbage(text):
            return
        curWord = ''
        nextWord = ''
        for w in self._generate_next_word(text):
            if w in self.stopwords:
                curWord = ''
                nextWord = ''
                continue
            if not curWord:
                curWord = w
            elif not nextWord:
                nextWord = w
                self._increment_pair_count(curWord, nextWord, identifier)
                curWord = nextWord
                nextWord = ''
            if curWord:
                self._increment_word_count(curWord)
    
    def _is_text_garbage(self, text):
        counts = {}
        for line in text.splitlines():
            for match in self.token_regex_pattern.finditer(line):
                word = match.group()
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
        for i in xrange(0,len(self.bigrams)):
            self.reference_bigrams[(self.bigrams[i][3],self.bigrams[i][4])] = \
                    True
    
    def _next_word_char(self, pos, tlength, text):
        i = pos
        while i < tlength:
            if self.token_regex_pattern.match(text[i]):
                break
            i += 1
        return i

    def _next_not_word_char(self, pos, tlength, text):
        i = pos
        while i < tlength:
            if not self.token_regex_pattern.match(text[i]):
                break
            i += 1
        return i
    
    def _generate_next_word(self, text):
        '''Note that there is no metadata check'''
        for line in text.splitlines():
            for match in self.token_regex_pattern.finditer(line):
                w = match.group()
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
