from __future__ import division, print_function, unicode_literals
import time
from import_tool.tools import VerboseTimer
from visualize.models import *
from visualize.models import MAX_ELEMENTS_FOR_IN_OPERATOR
from django.db import transaction, connections
from django.db.models import Max
from import_tool.metadata.utilities import create_metadata_types, create_metadata

MAX_TOKENS_IN_MEMORY = 500000

def get_all_word_types(database_id):
    """Return a dictionary mapping word_types as unicode strings to the
    corresponding database object.
    database_id -- the dict key specifying the database in django
    """
    return {r.word: r for r in WordType.objects.using(database_id).all()}

def create_analysis(database_id, dataset_db, analysis, meta_types_db):
    """Create the dataset entry and metadata entries.
    database_id -- the dict key specifying the database in django
    dataset_db -- the Dataset django database object
    analysis -- an AbstractAnalysis object
    meta_types_db -- what is returned by the get_all_metadata_types method in the
                     metadata.utilities module
    Return the Analysis django database object created.
    """
    with transaction.atomic(using=database_id):
        analysis_db, created = Analysis.objects.using(database_id).\
                get_or_create(dataset=dataset_db, name=analysis.name)
        
        if created:
            metadata_types = analysis.metadata_types
            create_metadata_types(database_id, metadata_types, meta_types_db)
            create_metadata(database_id, [analysis_db], 
                            AnalysisMetadataValue, 'analysis',
                            metadata_types, 
                            meta_types_db, 
                            [analysis.metadata])
    return analysis_db

def create_word_types(database_id, commit, word_types_db):
    """Create WordType entries in the database.
    database_id -- the dict key specifying the database in django
    commit -- a dictionary mapping the unicode word to a WordType object
              where the WordType object has not yet been inserted into the
              database
    word_types_db -- what is returned by get_all_word_types; this 
                     object is updated with the new words.
    """
    with transaction.atomic(using=database_id):
        requery_list = []
        commit_list = []
        for word, word_rep in commit.iteritems():
            requery_list.append(word)
            commit_list.append(word_rep)
        WordType.objects.using(database_id).bulk_create(commit_list)
    low = 0
    high = MAX_ELEMENTS_FOR_IN_OPERATOR
    while low < len(requery_list):
        reps = WordType.objects.using(database_id).\
            filter(word__in=requery_list[low:high])
        for r in reps:
            word_types_db[r.word] = r
        low = high
        high += MAX_ELEMENTS_FOR_IN_OPERATOR

def create_word_type_entries(database_id, word_types, word_types_db):
    """Create WordType entries for the given word_types and add to
    the dict word_types_db.
    database_id -- the dict key specifying the database in django
    word_types -- list, set, or dict of words to be created
    word_types_db -- dict as returned by get_all_word_types; this
                     will be updated with the newly added words
    """
    word_types_to_commit = {}
    for v in word_types:
        if v not in word_types_db:
            word_types_to_commit[v] = WordType(word=v)
    create_word_types(database_id, word_types_to_commit, word_types_db)

def create_tokens(database_id, analysis_db, word_types_db, tokens, verbose=False):
    """Add token sequences to the database.
    database_id -- the dict key specifying the database in django
    analysis_db -- the Analysis django database object
    word_types_db -- what is returned by get_all_word_types
    tokens -- An iterator over tokens and token-topic assignments; each item is of the form
              (document_index, start_index, token, token_abstraction, topic_number_list)
    verbose -- if True notifications of progress will be output to the console
    """
    def commit_tokens(t):
        WordToken.objects.using(database_id).bulk_create(t)
        del t[:]
    def commit_topic_assignments(t):
        WordTokenTopic.objects.using(database_id).bulk_create(t)
        del t[:]
    
    with transaction.atomic(using=database_id):
        if verbose:
            num_docs = analysis_db.dataset.documents.count()
            timer = VerboseTimer(num_docs)
        
        if WordToken.objects.using(database_id).all().exists():
            token_id = WordToken.objects.using(database_id).all().aggregate(Max('id'))['id__max'] + 1
        else:
            token_id = 0
        
        tokens_to_commit = []
        topic_tokens_to_commit = []
        topics_db = {t.number: t for t in analysis_db.topics.all()}
        documents_db = {d.index: d for d in analysis_db.dataset.documents.all()}
        
        total_tokens = 0
        total_topic_tokens = 0
        token_index = 0
        prev_document_index = None
        for document_index, start_index, token, token_abstraction, topic_number_list in tokens:
            if prev_document_index != document_index:
                prev_document_index = document_index
                token_index = 0
                if verbose: timer.tick()
            
            word_token = WordToken(id=token_id, document_id=documents_db[document_index].id, analysis=analysis_db, 
                word_type_id=word_types_db[token].id, word_type_abstraction=word_types_db[token_abstraction],
                token_index=token_index, start_index=start_index)
            tokens_to_commit.append(word_token)
            
            for topic_number in topic_number_list:
                try:
                    topic_db = topics_db[topic_number]
                except:
                    topic_db = Topic.objects.using(database_id).create(analysis=analysis_db, number=topic_number)
                    topics_db[topic_number] = topic_db
                word_token_topic = WordTokenTopic(token=word_token, topic=topic_db)
                topic_tokens_to_commit.append(word_token_topic)
                total_topic_tokens += 1
            
            if len(tokens_to_commit) > MAX_TOKENS_IN_MEMORY:
                commit_tokens(tokens_to_commit)
                commit_topic_assignments(topic_tokens_to_commit)
            token_index += 1
            token_id += 1
            total_tokens += 1
        
        commit_tokens(tokens_to_commit)
        commit_topic_assignments(topic_tokens_to_commit)
        
        if verbose:
            print('Number of tokens created:', total_tokens)
            print('Number of topic token relationships created:', total_topic_tokens)

def create_topic_heirarchy(database_id, analysis_db, heirarchy):
    """Assign topics their parents.
    database_id -- the dict key specifying the database in django
    analysis_db -- the Analysis django database object
    heirarchy -- an iterator where each element is of the form (parent_topic_number, topic_number)
    """
    topics = None
    with transaction.atomic(using=database_id):
        for parent_num, topic_num in heirarchy:
            if not topics: topics = {topic.number: topic for topic in analysis_db.topics.all()}
            topic = topics[topic_num]
            topic.parent = parent_num
            topic.save()

def create_stopwords(database_id, analysis_db, word_types_db, stopwords):
    """Add stopword entries to an analysis.
    database_id -- the dict key specifying the database in django
    analysis_db -- the Analysis django database object
    word_types_db -- what is returned by get_all_word_types
    stopwords -- an iterator over unicode strings
    """
    return
    stopwords_in_db = analysis_db.get_stopwords()
    stopwords_to_commit = []
    word_types_to_commit = {}
    # Find stopwords not in database.
    for stopword in stopwords:
        if stopword not in stopwords_in_db:
            stopwords_to_commit.append(stopword)
            if stopword not in word_types_db:
                word_types_to_commit[stopword] = \
                    WordType(word=stopword)
    # Add any new words.
    create_word_types(database_id, word_types_to_commit, word_types_db)
    # Create records.
    for i, s in enumerate(stopwords_to_commit):
        stopwords_to_commit[i] = Stopword(analysis=analysis_db, 
            word_type=word_types_db[s])
    # Add stopwords to database.
    with transaction.atomic(using=database_id):
        Stopword.objects.using(database_id).bulk_create(stopwords_to_commit)

def create_excluded_words(database_id, analysis_db, word_types_db, excluded_words):
    """Add excluded word entries to analysis, same process as create_stopwords.
    database_id -- the dict key specifying the database in django
    analysis_db -- the Analysis django database object
    word_types_db -- what is returned by get_all_word_types
    excluded_words -- an iterator over unicode strings
    """
    return
    excluded_words_in_db = analysis_db.get_excluded_words()
    excluded_words_to_commit = []
    word_types_to_commit = {}
    # Find stopwords not in database.
    for word in excluded_words:
        if word not in excluded_words_in_db:
            excluded_words_to_commit.append(word)
            if word not in word_types_db:
                word_types_to_commit[word] = \
                    WordType(word=word)
    # Add any new words.
    create_word_types(database_id, word_types_to_commit, word_types_db)
    # Create records.
    for i, s in enumerate(stopwords_to_commit):
        excluded_words_to_commit[i] = ExcludeWord(analysis=analysis_db, 
            word_type=word_types_db[s])
    # Add stopwords to database.
    with transaction.atomic(using=database_id):
        ExcludeWord.objects.using(database_id).bulk_create(excluded_words_to_commit)

def create_topic_names(database_id, analysis_db, topic_namers, verbose=False):
    """Create topic name entries for each topic name scheme.
    database_id -- the dict key specifying the database in django
    analysis_db -- the Analysis django database object
    topic_namers -- a list of instances of type AbstractTopicNamer
    verbose -- if True print to the console any additional information
    """
    topics_db = {topic.number: topic for topic in analysis_db.topics.all()}
    for topic_namer in topic_namers:
        name_scheme = topic_namer.name_scheme
        name_scheme_db, created = TopicNameScheme.objects.using(database_id).get_or_create(name=name_scheme)
        if TopicNameScheme.objects.using(database_id).filter(name=name_scheme, names__topic__analysis=analysis_db).count() == 0:
            with transaction.atomic(using=database_id):
                topic_names = topic_namer.name_topics(database_id, analysis_db)
                topic_names_to_commit = []
                for topic_number, topic_name in topic_names.iteritems():
                    topic_names_to_commit.append(TopicName(topic=topics_db[topic_number], name_scheme=name_scheme_db, name=topic_name))
                TopicName.objects.using(database_id).bulk_create(topic_names_to_commit)
        else:
            if verbose: print("Name scheme %s already exists for analysis %s." % (name_scheme, analysis_db.name))
