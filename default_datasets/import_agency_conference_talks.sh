#! /bin/bash

python topicalguide.py import default_datasets/agency_conference_talks --stopwords stopwords/en.txt --identifier agency --bigrams
python topicalguide.py analyze agency --subdocuments --number-of-topics 20

