
This readme describes how to use WordNet, the lexical ontology, as the prior instead of a hand-constructed topic prior.

There are two options for how to use WordNet.  The first is to use WordNet to generate constraints (a tree of depth two), and the second is to use the entire hyponym tree of WordNet (a tree of depth seventeen).

For more information about WordNet, see:
http://wordnet.princeton.edu/

For both of these approaches, we use the interface provided by nltk.

http://nltk.org

After you've installed nltk, you also need to install the WordNet corpus (corpora/wordnet) and brown corpus (corpora/brown) to estimate the hyperparameters.

======================================
 WordNet to Generate Constraints
======================================

This script creates a set of positive correlations based on synsets in WordNet:

python scripts/extract_constraints_wordnet.py --vocab $INPUTDIR/$DATANAME.voc --output $INPUTDIR/$DATANAME.cons --num_cons -1

The number of constraints is based on the num_cons flag; If it is set to be -1, it will extract all the correlations from wordnet for your data.

======================================
 Use All of WordNet
======================================

In addition to nltk, this approach also requires you to install a protocol buffer compiler and the protocol buffer python libraries.

(1) compile the python protocol buffer
protoc --proto_path=scripts/python_lib --python_out=scripts/python_lib scripts/python_lib/wordnet_file.proto

(this places the output in the current directory; if you do not want the output to live here, it must be accessible from your $PYTHONPATH)

(2) filter out the words that are not contained in the wordnet

python scripts/filter_vocab.py input/synthetic.voc > input/synthetic.filter.voc

(We need every words in the vocab appear in the tree, but wordnet might not contain every words from your vocab, so filter out the words that are not contained in the wordnet from your vocab)

(3) create the WordNet protocol buffer:
python scripts/ontology_writer.py --vocab=input/synthetic.filter.voc --output_tree=input/synthetic.all.wn --output_hyper=input/synthetic.hyper

(of course, use the vocabulary file that corresponds to your data. and Don't forget that the generated tree file name is synthetic.all.wn, use this name in the command for topic models.)

(4) At this point, you should be able to use the output (the default will be called "input/wn" for the tree and "input/wn.lookup" for the hyperparameters) as the --tree and --tree-hyperparameters arguments to the main program, Vectors2TreeTopics.

You can also generate your own arbitrary trees by encoding it as a protocol buffer.

======================================
Concrete example using denews
======================================

Get the data:
./scripts/get_de_news.sh

Make the mallet file:
bin/mallet import-dir --input de_news_raw --output input/denews-topic-input.mallet --keep-sequence

Make the vocab:
java -cp class:lib/* cc.mallet.topics.tui.GenerateVocab --input \
input/denews-topic-input.mallet --tfidf-thresh 1 --freq-thresh 1 --word-length 2 \
--tfidf-rank true --vocab input/denews.voc

Filter the vocab to remove things not in WordNet:
python scripts/filter_vocab.py input/denews.voc > input/denews.filter.voc

Generate wordnet:
python scripts/ontology_writer.py --vocab=input/denews.voc \
--output_tree=input/denews.all.wn --output_hyper=input/denews.hyper

Train model:
mkdir de_news_model

java -cp class:lib/* cc.mallet.topics.tui.Vectors2TreeTopics --input input/denews-topic-input.mallet --output-dir de_news_model --tree input/denews.all.wn --tree-hyperparameters input/denews.hyper --vocab input/denews.filter.voc --alpha 0.5 --output-interval 1 --num-topics 5 --num-iterations 10 --random-seed 0
