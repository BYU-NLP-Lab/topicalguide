
from nltk.corpus import wordnet as wn
import sys

if __name__ == "__main__":

    wn_words = set()
    for ii in wn.all_synsets('n'):
        for jj in ii.lemmas:
            wn_words.add(jj.name.lower())

    vocab_file = sys.argv[1]
    for ii in open(vocab_file):
        word = ii.split('\t')[1]
        if word in wn_words:
            print(ii.strip())
