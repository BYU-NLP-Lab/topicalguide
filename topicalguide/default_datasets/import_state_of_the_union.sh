#! /bin/bash

python tg.py import default_datasets/state_of_the_union --public --public-documents --identifier state_of_the_union --verbose
python tg.py analyze state_of_the_union --verbose --subdocuments --number-of-topics 100 --stopwords stopwords/english_all.txt --remove-singletons --stem-words --bigrams


