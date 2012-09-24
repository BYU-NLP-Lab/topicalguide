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

Now we get to the task definitions!

IMPORT THINGS

    task_document_metadata

    - make a json file 'metadata.documents' with all of the filenames in files.dir

    task_metadata_import [these rely on functions from import_scripts.metadata]

    - for each datasets, documents, word_types, word_tokens

    - define a task, with an action, a clean, and a checker - to see if it's been
        done already :: all dependent on 'dataset_import'

    - for each analysis, topics

    - define a task [action, clean, uptodate] dependent on analysis_import

MALLET

    task_mallet_input

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

JAVA STUFF

    task_hash_java

    - make an md5 of the md5s of all the files in the java_base directory?

    task_compile_java

    - run ant -lib lib on 'java_base'

    task_graphs

    - generate task for each c['name_schemes'], using the jar c['graph_builder_class']

