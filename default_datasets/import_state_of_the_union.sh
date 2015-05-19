#! /bin/bash

python tg.py import default_datasets/state_of_the_union --public --public-documents --identifier state_of_the_union --verbose

python tg.py document_metadata_generator state_of_the_union default_datasets/state_of_the_union/metadata_flagger.py --verbose

python tg.py analyze state_of_the_union --verbose --subdocuments --number-of-topics 100 --stopwords stopwords/state_of_the_union_english.txt --remove-singletons --stem-words --bigrams --identifier lda100topics

