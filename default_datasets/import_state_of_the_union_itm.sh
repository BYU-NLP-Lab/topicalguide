#! /bin/bash

python tg.py import default_datasets/state_of_the_union --public --public-documents --identifier sotu --verbose

python tg.py document_metadata_generator state_of_the_union default_datasets/state_of_the_union/metadata_flagger.py --verbose

python tg.py analyze sotu --analysis-tool MalletITM --verbose --subdocuments --number-of-topics 100 --stopwords stopwords/state_of_the_union_english.txt --remove-singletons --stem-words --bigrams --identifier itmstuff

