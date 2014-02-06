#Stack Overfow build script
import codecs
import os
import re
import json
import sys
from nltk.tokenize import TreebankWordTokenizer
from bs4 import BeautifulSoup
from build import create_dirs_and_open
from topic_modeling import anyjson

def update_config(c):
    c['num_topics'] = 100
    c['dataset_name'] = 'stack_overflow'
    c['dataset_readable_name'] = 'Stack Overflow'
    c['suppress_default_document_metadata_task'] = True

def create_tasks(c):

    def task_extract_data():
        def utd(_tasks, _vals):
            return os.path.exists(os.path.join(c['raw_data_dir'], 'data')) and os.path.exists(os.path.join(c['raw_data_dir'], 'metadata', 'documents.json'))
        data_dir = os.path.join(c['raw_data_dir'], "data")
        dest_dir = c['files_dir']
        task = dict()
        task['targets'] = [dest_dir]
        task['actions'] = [(_extract, [data_dir, dest_dir])]
        task['clean'] = ['rm -rf '+dest_dir]
        return task

    def task_mallet_imported_data():
        task = dict()
        task['targets'] = [c['mallet_imported_data']]

        cmd = '%s import-dir --input %s --output %s --keep-sequence --set-source-by-name --source-name-prefix "file:%s/%s/" ' \
            % (c['mallet'], c['files_dir'], c['mallet_imported_data'], os.getcwd(), c['files_dir'])

        cmd += ' --extra-stopwords %s' % os.path.join(c['raw_data_dir'], 'stopwords.txt')

        task['actions'] = [cmd]
        task['file_dep'] = [c['mallet_input']]
        task['clean'] = ["rm -f " + c['mallet_imported_data']]
        return task

def _extract(data_dir, result_dir):
    print('getting stack overflow data! woot woot')
    metadata = {}
    counter = 0
    user_dirs = os.walk(data_dir).next()[1]
    progress_counter = 0
    for user in user_dirs:
        if user == '.':
            continue
        counter, question_metadata = _clean_questions_and_answers(os.path.join(data_dir, user), 'questions', result_dir, counter)
        counter, answer_metadata = _clean_questions_and_answers(os.path.join(data_dir, user), 'answers', result_dir, counter)
        metadata.update(question_metadata)
        metadata.update(answer_metadata)
        progress_counter += 1
        print('Done with extracting stuff for user %d of %d' % (progress_counter, len(user_dirs)))
    sys.stderr.write("DONE WITH SOME STUFFFFFFFFF!")
    _write_out_metadata(metadata, result_dir)

def _get_metadata_for_document(document):
    """Given a dictionary, will pull the relevant metadata out of it and return it as a dictionary."""
    data = {
        'author_name': document['owner']['display_name'],
        'user_id': document['owner']['user_id'],
        'title': document['title'],
        'timestamp': document['last_activity_date']
     }
    if 'answer_id' in document.keys():
        data['question_or_answer'] = 'answer'
        data['id'] = document['answer_id']
    else:
        data['question_or_answer'] = 'question'
        data['id'] = document['question_id']
    return data

def _write_out_metadata(metadata, output_dir):
    formatted_data = {
        'types': {
            'author_name': 'text',
            'user_id': 'int',
            'title': 'text',
            'question_or_answer': 'text',
            'id': 'int',
            'timestamp': 'int'
        },
        'data': metadata
    }
    w = create_dirs_and_open(os.path.join(output_dir, '..', 'metadata', 'documents.json'))
    w.write(json.dumps(formatted_data))
    w.close()

def _clean_questions_and_answers(base_dir, q_or_a, output_dir, counter):
    num_files_cleaned = 1
    metadata = {}
    with open(os.path.join(base_dir, 'raw', '%s.json' % q_or_a)) as f:
        raw = f.read()
    dat = json.loads(raw)
    for item in dat:
        metadata['%s.txt' % counter] = _get_metadata_for_document(item)
        soup = BeautifulSoup(item['body'])
        w = create_dirs_and_open(os.path.join(output_dir, '%s.txt' % str(counter)))
        w.write(soup.get_text())
        w.close()
        counter += 1

    return counter, metadata

