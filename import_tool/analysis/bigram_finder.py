# coding=utf-8
from __future__ import division, print_function, unicode_literals

import argparse
import os
import re
import sys
import numpy as np
import scipy.stats as stats
from StringIO import StringIO


class BigramFinder(object):
    """BigramFinder uses likelihood ratios to determine bigrams.
    This BigramFinder is made for the English language.
    """
    
    def __init__(self, stopwords={}):
        """Create a BigramFinder.
        stopwords -- a dictionary where the keys are stopwords
        """
        # instance variables
        self.stopwords = stopwords
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
        self.infrequency_ratio = 12
        self.training = True
    
    def train(self, document_identifier, tokens):
        """Train the bigram finder.
        document_identifier -- a unique identifier
        tokens -- a list of tokens in the order they appear, each item is a
                  tuple of the form (token, character_offset); stopwords included
        Return nothing.
        """
        if len(tokens) < 2: return
        
        self.training = True
        
        for i in xrange(0, len(tokens)-1):
            curr_token, __ = tokens[i]
            next_token, __ = tokens[i+1]
            if curr_token not in self.stopwords:
                self._increment_word_count(curr_token)
                if next_token not in self.stopwords:
                    self._increment_pair_count(curr_token, next_token, document_identifier)
        if next_token not in self.stopwords:
            self._increment_word_count(next_token)
        self.total_word_count += len(tokens)
    
    def _increment_word_count(self, word):
        self.word_count[word] = self.word_count.setdefault(word, 0) + 1
    
    def _increment_pair_count(self, w1, w2, identifier):
        if w1 not in self.pair_count:
            self.pair_count[w1] = {}
            self.pair_count[w1][w2] = []
            self.pair_count[w1][w2].append(1)
            self.pair_count[w1][w2].append({})
            self.pair_count[w1][w2][1][identifier] = True
        elif w2 not in self.pair_count[w1]:
            self.pair_count[w1][w2] = []
            self.pair_count[w1][w2].append(1)
            self.pair_count[w1][w2].append({})
            self.pair_count[w1][w2][1][identifier] = True
        else:
            self.pair_count[w1][w2][0] += 1
            self.pair_count[w1][w2][1][identifier] = True
    
    def print(self):
        """Print to the console the most common found bigrams."""
        if self.training:
            self._enumerate_bigrams()
            self.training = False
        
        if not self.bigrams:
            print("No bigrams.")
            return
        
        for (stat, pair_count, doc_count, w1, w2) in self.bigrams:
            print(unicode(stat)+'\t'+unicode(pair_count)+'\t'+doc_count+'\t'+w1+'\t'+w2)
    
    def combine(self, tokens, text):
        """Train the bigram finder.
        document_identifier -- a unique identifier
        tokens -- a list of tokens in the order they appear, each item is a
                  tuple of the form (token, character_offset); stopwords included
        text -- the text of a document, used to check for a space separating the
                token
        Return a new list of tokens.
        """
        if self.training:
            self._enumerate_bigrams()
            self.training = False
        
        if not self.reference_bigrams:
            return tokens
        
        i = 0
        prev_token, prev_offset = None, None
        just_combined = False # Used to detect bigram chains
        result = []
        while i < (len(tokens) - 1):
            curr_token, curr_offset = tokens[i]
            next_token, next_offset = tokens[i+1]
            # Check for valid tokens
            if curr_token not in self.stopwords and next_token not in self.stopwords:
                end_of_curr_token = curr_offset + len(curr_token)
                # Check for a single space between tokens
                if text[end_of_curr_token] == ' ' and (end_of_curr_token + 1) == next_offset:
                    if just_combined:
                        last = len(result) - 1
                        prev_token, prev_offset = result.pop(last)
                        new_token = prev_token + ' ' + next_token
                        result.append((new_token, prev_offset))
                        new_token = result
                    else:
                        new_token = curr_token + ' ' + next_token
                        result.append((new_token, curr_offset))
                    just_combined = True
                else:
                    if not just_combined:
                        result.append((curr_token, curr_offset))
                    just_combined = False
            else:
                if not just_combined:
                    result.append((curr_token, curr_offset))
                just_combined = False
            i += 1
        return result
    
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
            self.reference_bigrams[(self.bigrams[i][3],self.bigrams[i][4])] = True
    
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
    
    def _record_bigram(self, stat, pair_count, doc_count, w1, w2):
        self.bigrams.append((stat, pair_count, doc_count, w1, w2))
    
    def _analyze_bigram(self, w1, w2):
        ''' bigram contingency table (p. 169 Manning and Shütze)
            w1  ~w1
        w2  a   b
        ~w2 c   d
        '''
        try:
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
        except:
            print(a, b, c, d)
            print(self.pair_count[w1][w2])
            print(self.word_count[w1])
            print(self.word_count[w2])
            print(self.total_word_count)
            raise
