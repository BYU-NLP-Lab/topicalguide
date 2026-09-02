"""Fixtures shared by the API and browser tests.

These build a small dataset directly through the ORM rather than running the
import/analysis pipeline, so the tests stay fast and deterministic and do not
need Mallet or a corpus on disk.
"""

import pytest

from visualize.models import (Analysis, AnalysisMetadataValue,
                              AnalysisMetricValue, Dataset,
                              DatasetMetadataValue, DatasetMetricValue,
                              Document, DocumentMetadataValue, MetadataType,
                              Metric, Topic, TopicMetricValue, TopicName,
                              TopicNameScheme, TopicPairwiseMetricValue,
                              WordToken, WordType, WordTokenTopic)

DATASET_NAME = 'test_corpus'
DATASET_READABLE_NAME = 'Test Corpus'
ANALYSIS_NAME = 'lda5topics'
ANALYSIS_READABLE_NAME = 'LDA 5 Topics'
TOPIC_COUNT = 5
DOCUMENT_COUNT = 3
# The scheme the app selects by default; the real pipeline builds it with
# import_tool.analysis.name_schemes.top_n.TopNTopicNamer.
NAME_SCHEME = 'Top3'
# Each topic gets its own vocabulary so top-word assertions are unambiguous.
# Words are listed most frequent first, and the fixture gives them strictly
# decreasing token counts, so the generated Top3 name is deterministic.
TOPIC_WORDS = [
    ['alpha', 'beta', 'gamma'],
    ['delta', 'epsilon', 'zeta'],
    ['eta', 'theta', 'iota'],
    ['kappa', 'lambda', 'mu'],
    ['nu', 'xi', 'omicron'],
]
TOPIC_NAMES = [' '.join(words) for words in TOPIC_WORDS]
# The topics-over-time view only offers metadata whose name looks time-related
# ('year', 'date', 'decade', 'month', 'timestamp', 'time') and defaults to
# 'year', so the documents carry one.
FIRST_YEAR = 2001
DOCUMENT_YEARS = [FIRST_YEAR + index for index in range(DOCUMENT_COUNT)]
# The pairwise topic metric the chord diagram draws its chords from.
PAIRWISE_METRIC = 'Document Correlation'


def set_metadata(model_class, owner_field, owner, name, value, datatype='text'):
    metadata_type, __ = MetadataType.objects.get_or_create(name=name,
                                                           datatype=datatype)
    metadata_value = model_class(metadata_type=metadata_type,
                                 **{owner_field: owner})
    metadata_value.set(value, datatype)
    metadata_value.save()
    return metadata_value


def set_metric(model_class, owner_field, owner, name, value):
    metric, __ = Metric.objects.get_or_create(name=name)
    return model_class.objects.create(metric=metric, value=value,
                                      **{owner_field: owner})


def document_text(index):
    return 'Body of document %d.' % index


@pytest.fixture
def dataset_dir(tmp_path_factory):
    """A real directory of documents so Document.get_content() can read them."""
    root = tmp_path_factory.mktemp('dataset')
    documents = root / 'documents'
    documents.mkdir()
    for index in range(DOCUMENT_COUNT):
        (documents / ('doc%d.txt' % index)).write_text(document_text(index))
    return root


@pytest.fixture
def sample_dataset(db, dataset_dir):
    """A public dataset with one analysis, five topics and three documents."""
    dataset = Dataset.objects.create(name=DATASET_NAME,
                                     dataset_dir=str(dataset_dir),
                                     public=True, visible=True,
                                     public_documents=True)
    set_metadata(DatasetMetadataValue, 'dataset', dataset,
                 'readable_name', DATASET_READABLE_NAME)
    set_metadata(DatasetMetadataValue, 'dataset', dataset,
                 'description', 'A corpus built for the test suite')
    set_metric(DatasetMetricValue, 'dataset', dataset,
               'Document Count', DOCUMENT_COUNT)

    analysis = Analysis.objects.create(name=ANALYSIS_NAME, dataset=dataset)
    set_metadata(AnalysisMetadataValue, 'analysis', analysis,
                 'readable_name', ANALYSIS_READABLE_NAME)

    topics = [Topic.objects.create(analysis=analysis, number=number)
              for number in range(TOPIC_COUNT)]

    documents = []
    for index in range(DOCUMENT_COUNT):
        document = Document.objects.create(dataset=dataset, index=index,
                                           filename='doc%d.txt' % index,
                                           source='', length=100)
        set_metadata(DocumentMetadataValue, 'document', document,
                     'title', 'Document %d' % index)
        set_metadata(DocumentMetadataValue, 'document', document,
                     'year', DOCUMENT_YEARS[index], datatype='int')
        documents.append(document)

    # Give every topic tokens in every document so top-word and document
    # queries both return something for each topic. Word i of a topic gets
    # (len(words) - i) tokens per document, so the top-word ordering -- and
    # therefore the Top3 name -- is strictly determined.
    token_id = 0
    for topic_number, words in enumerate(TOPIC_WORDS):
        topic_tokens = 0
        for word_index, word in enumerate(words):
            word_type, __ = WordType.objects.get_or_create(word=word)
            repeats = len(words) - word_index
            for document in documents:
                for __ in range(repeats):
                    token = WordToken.objects.create(
                        id=token_id, analysis=analysis, document=document,
                        word_type=word_type, word_type_abstraction=word_type,
                        token_index=token_id, start_index=token_id)
                    WordTokenTopic.objects.create(token=token,
                                                  topic=topics[topic_number])
                    token_id += 1
                    topic_tokens += 1
        # The topics view needs this to compute "% of Corpus".
        set_metric(TopicMetricValue, 'topic', topics[topic_number],
                   'Token Count', topic_tokens)
    set_metric(AnalysisMetricValue, 'analysis', analysis,
               'Token Count', token_id)

    name_scheme = TopicNameScheme.objects.create(name=NAME_SCHEME)
    for topic, name in zip(topics, TOPIC_NAMES):
        TopicName.objects.create(topic=topic, name_scheme=name_scheme,
                                 name=name)

    # The chord diagram draws one chord per topic pair from a pairwise metric,
    # and needs a full matrix -- it reads topics[j].pairwise[metric] as a row.
    # Correlation is 1 on the diagonal and falls off with the gap between
    # topic numbers, so the drawn chords differ from each other visibly.
    pairwise_metric, __ = Metric.objects.get_or_create(name=PAIRWISE_METRIC)
    for origin in topics:
        for ending in topics:
            gap = abs(origin.number - ending.number)
            TopicPairwiseMetricValue.objects.create(
                metric=pairwise_metric, origin_topic=origin,
                ending_topic=ending,
                value=round(1.0 - gap / float(TOPIC_COUNT), 4))

    return dataset


@pytest.fixture
def private_dataset(db):
    """A dataset the API must never expose."""
    return Dataset.objects.create(name='private_corpus', dataset_dir='/tmp/none',
                                  public=False, visible=False)
