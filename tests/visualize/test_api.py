"""Tests for the /api endpoint the single-page app is built on."""

import json

import pytest

from tests.conftest import (ANALYSIS_NAME, ANALYSIS_READABLE_NAME,
                            DATASET_NAME, DATASET_READABLE_NAME,
                            DOCUMENT_COUNT, TOPIC_COUNT)


def get_api(client, **params):
    response = client.get('/api', params)
    assert response.status_code == 200
    assert response['Content-Type'] == 'application/json'
    return json.loads(response.content)


def test_api_lists_public_datasets(client, sample_dataset):
    result = get_api(client, datasets='*')

    assert list(result['datasets']) == [DATASET_NAME]


def test_api_hides_private_datasets(client, sample_dataset, private_dataset):
    result = get_api(client, datasets='*')

    assert private_dataset.name not in result['datasets']


def test_api_named_dataset_only(client, sample_dataset, private_dataset):
    """Naming a private dataset explicitly must not reveal it either."""
    result = get_api(client, datasets=private_dataset.name)

    assert result['datasets'] == {}


def test_api_returns_dataset_metadata_and_metrics(client, sample_dataset):
    result = get_api(client, datasets='*', dataset_attr='metadata,metrics')
    dataset = result['datasets'][DATASET_NAME]

    assert dataset['metadata']['readable_name'] == DATASET_READABLE_NAME
    assert dataset['metadata']['description'] == 'A corpus built for the test suite'
    assert dataset['metrics']['Document Count'] == DOCUMENT_COUNT


def test_api_returns_document_and_analysis_counts(client, sample_dataset):
    result = get_api(client, datasets='*',
                     dataset_attr='document_count,analysis_count')
    dataset = result['datasets'][DATASET_NAME]

    assert dataset['document_count'] == DOCUMENT_COUNT
    assert dataset['analysis_count'] == 1


def test_api_returns_analyses(client, sample_dataset):
    """This is the query the datasets view issues on load."""
    result = get_api(client, datasets='*', analyses='*',
                     dataset_attr='metadata', analysis_attr='metadata')
    analyses = result['datasets'][DATASET_NAME]['analyses']

    assert list(analyses) == [ANALYSIS_NAME]
    assert analyses[ANALYSIS_NAME]['metadata']['readable_name'] == ANALYSIS_READABLE_NAME


def test_api_returns_topics(client, sample_dataset):
    result = get_api(client, datasets='*', analyses='*', topics='*',
                     topic_attr='metrics')
    topics = result['datasets'][DATASET_NAME]['analyses'][ANALYSIS_NAME]['topics']

    assert len(topics) == TOPIC_COUNT
    assert sorted(int(number) for number in topics) == list(range(TOPIC_COUNT))


def test_api_topics_are_empty_without_topic_attr(client, sample_dataset):
    """query_topics returns nothing at all unless topic_attr is requested."""
    result = get_api(client, datasets='*', analyses='*', topics='*')
    topics = result['datasets'][DATASET_NAME]['analyses'][ANALYSIS_NAME]['topics']

    assert topics == {}


def test_api_returns_documents(client, sample_dataset):
    """Documents hang off the analysis, not the dataset."""
    result = get_api(client, datasets='*', analyses='*', documents='*')
    analysis = result['datasets'][DATASET_NAME]['analyses'][ANALYSIS_NAME]

    assert sorted(analysis['documents']) == ['doc0.txt', 'doc1.txt', 'doc2.txt']


def test_api_returns_document_metadata(client, sample_dataset):
    result = get_api(client, datasets='*', analyses='*', documents='*',
                     document_attr='metadata')
    documents = result['datasets'][DATASET_NAME]['analyses'][ANALYSIS_NAME]['documents']

    assert documents['doc0.txt']['metadata']['title'] == 'Document 0'


def test_api_rejects_unknown_option(client, sample_dataset):
    """Unknown query keys are refused rather than silently ignored."""
    with pytest.raises(Exception, match='No such value as bogus_option'):
        client.get('/api', {'bogus_option': '*'})


def test_api_requires_get(client, sample_dataset):
    response = client.post('/api', {'datasets': '*'})

    assert response.status_code == 405
