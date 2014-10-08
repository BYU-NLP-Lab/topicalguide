#! /bin/bash

python topicalguide.py import default_datasets/state_of_the_union --stopwords stopwords/en.txt --identifier state_of_the_union --bigrams
python topicalguide.py analyze state_of_the_union --subdocuments --number-of-topics 100


