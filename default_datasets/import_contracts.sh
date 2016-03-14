#! /bin/bash

python tg.py import default_datasets/contract_dataset --public \
--public-documents --identifier legal_contracts --verbose
python tg.py analyze legal_contracts --verbose --subdocuments --number-of-topics 100 --stopwords stopwords/english_all.txt --remove-singletons --stem-words --bigrams


