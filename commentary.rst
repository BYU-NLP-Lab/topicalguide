
Performance:
    - postgresql
        - 1:49 for analysis import
        -  :13 for dataset import
        -  :14 document pairwise topic analysis
        - 50 SECONDS for chord diagram reload
    - mysql
        -  :16 for dataset import
        - 2:10 for analysis import


Backend Running Sequence:

-- extract_data
-- mallet_input
-- dataset_import
-- mallet_imported_data
-- mallet_output_gz
-- mallet_output
-- analysis_import
-- metadata_import:word_tokens
-- metadata_import:word_types
-- metadata_import:datasets
-- metadata_import:documents
-- metadata_import:analysis
-- metadata_import:topics
-- name_schemes:Top3
-- dataset_metrics:counts
-- analysis_metrics:entropy
-- topic_metrics:word_entropy
-- topic_metrics:token_count
-- topic_metrics:type_count
-- topic_metrics:document_entropy
-- pairwise_topic_metrics:document_correlation
-- pairwise_topic_metrics:word_correlation
-- document_metrics:topic_entropy
-- document_metrics:token_count
-- document_metrics:type_count
-- pairwise_document_metrics:topic_correlation
.  hash_java
-- compile_java
-- graphs:Top3


Here we have a list of the issues
+++++++++++++++++++++++++++++++++++

Front Page
----------

1.1 the graph doesn't happen
    file: visualize/dataset_views/py

    function: DatasetView/get_context_data

    Basically we are disabling this. If we try to enable it, there's an error
    about a lack of Dataset.attribute_set

Analysis / Topics Page
----------------------

2.1 add filter by: attribute
    file: visualize/topics/filters.py :145

    When you select it from the dropdown, we get a 500. Again, Dataset.attribute_set

2.2.1  add filter by: Metric, select metric "Word Entropy"
    file: visualize/topics/ajax.py :189

    Our session seems not to have been correctly populated... I don't know
    where that should have happened.

2.2.2 add filter: metric:number of tokens fails
    file: visualize/topivs/filters.py :246

    TopicMetric has no attribute topicmetricvalues

2.3 add filter by Word
    file: visualize/topics/filters

    Dataset has no attribute word_set

Similar Topics Subpage
''''''''''''''''''''''

2.4.1 clicking on a topic link takes you to a broken {base}/topic_num
    the ajax request populates it correctly, but the stock html doesn't


Extra Information
'''''''''''''''''

2.5.1 Top documents - file name and % are missing

2.5.2 Top Values for attribute - broken

Analysis/Documents
------------------

3.1 Add filter by Topic
    file: --/filters.py :122

    Filter has no attribute name

3.1.2 Dataset no attribute_set

3.1.3 Metrics broken too

Analysis/Words
--------------

4.1 plots look a little off

    
Things to refactor
++++++++++++++++++

r2.1 from visualize/topics/ajax.py:new_topic_filter is returning HTML!!!


An Annotated Commentary on the State of Things [e.g. backend.py]
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

So here I will generally explain what in the world we are trying to do with
this file.

0. if this is evoked from command line, not through doit, run doit on the
   current file, using the arguments::

        -f [this file name] --db [.dbs/build_name.db]

First, a custom script is imported which pollutes the local namespace... yeah I
thought it was a bad idea too.

1. set some config options...
2. define some task_* functions, which get automajically collected by our
   friend doit.
3. in the case of state_of_the_union, the only task\_ we define is
   task_extract_data
4. define some helper functions which, though they pollute the local namespace,
   don't appear to get used.

Ok! we're done with that custom script. Now back to our backend.py

5. Call initialize_config if it was defined by the script
6. make sure database_name has been set
7. set a bunch of default config items (so, don't override config items from
   the script)
8. setup the database (mysql or sqlite)


Empty Chairs at Empty Tables
----------------------------

- analysis_favorite
- datasetfavorite
- documentfavorite
- topicfavorite
- topicviewfavorite
- documentviewfavorite

- analysis_stopwords
- markupfile
- topicsgroup
- topicgrouptopic

- analysis_metainfo/value
- topicmetainfo/value
- wordtokenmetainfo/value
- wordtokenmetric/value
- wordtypemetainfo/value
- wordtypemetric/value

To Execute Everything Stepwise, do:

- extract_data
- mallet
- dataset_import
- analysis_import
- metrics
- graphs


Now we get to the task definitions!

IMPORT THINGS

    task_document_metadata

    - make a json file 'metadata.documents' with all of the filenames in files.dir

    task_metadata_import --> depends "analysis_import" and "dataset_import"
    [these rely on functions from import_scripts.metadata]

    - for each datasets, documents, word_types, word_tokens

    - define a task, with an action, a clean, and a checker - to see if it's been
        done already :: all dependent on 'dataset_import'

    - for each analysis, topics

    - define a task [action, clean, uptodate] dependent on analysis_import

MALLET

    task_mallet_input --> depends "extract data"

    - this takes all of the files and puts them into a single file...why?

    task_mallet_imported_data

    - run 'mallet import-dir'

    task_mallet_output_gz

    - run 'mallet train-topics' (produces gzipped data)

    task_mallet_output

    - takes the mallet output and gunzips it

    task_mallet

    - an aggregator for mallet_import, mallet_imported_data, mallet_output_gz,
    mallet_output


task_dataset_import :: depends -> task_document_metadata

- run import_dataset (from import_scripts.dataset_import)

task_analysis_import

- run import_analysis (depends on dataset_import)

task_name_schemes

- generate tasks for each of the name schemes in the 'name_schemes' config vbl

  - this just calls 'name_all_topics' from the name scheme class

METRICS

    task_dataset_metrics

    - for each metric in metric_scripts.datasets.metrics generate a task

    task_analysis_metrics

    - for each metric in metric_scripts.analysis.metrics generate a task

    task_topic_metrics

    - for each metric in c['topic_metrics'] generate a task

    task_pairwise_topic_metrics

    - for each metric in c['pairwise_topic_metrics'] generate a task

    task_document_metrics

    - generate tasks for metric_scripts.documents.metrics

    task_pairwise_document_metrics

    - generate tasks for c['pairwise_document_metrics']

    task_metrics

    - aggregator for many

JAVA STUFF

    task_hash_java

    - make an md5 of the md5s of all the files in the java_base directory?

    task_compile_java

    - run ant -lib lib on 'java_base'

    task_graphs

    - generate task for each c['name_schemes'], using the jar c['graph_builder_class']

