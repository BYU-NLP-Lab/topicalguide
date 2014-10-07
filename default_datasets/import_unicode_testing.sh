#! /bin/bash

python topicalguide.py import default_datasets/unicode_testing --keep-singletons --stopwords stopwords/en.txt --identifier unicode_testing --bigrams

python topicalguide.py analyze unicode_testing --subdocuments --number-of-topics 10

