"""Tests for the /bertopic-viz/ endpoint.

This route was at 9% coverage, and measuring that is what surfaced the access
control gap below: unlike /api it did not filter on public/visible, so it
served private datasets and its error messages let their names be enumerated.
"""

import json

import pytest

from visualize.models import Analysis, Dataset

from tests.conftest import ANALYSIS_NAME, DATASET_NAME


def get_viz(client, dataset, analysis, viz_type='topics'):
    return client.get('/bertopic-viz/%s/%s/%s/' % (dataset, analysis, viz_type))


@pytest.fixture
def private_bertopic(db):
    """A private dataset carrying a BERTopic-named analysis."""
    dataset = Dataset.objects.create(name='secret_corpus',
                                     dataset_dir='/tmp/does-not-exist',
                                     public=False, visible=False)
    Analysis.objects.create(name='bertopic10', dataset=dataset)
    return dataset


def test_private_dataset_is_not_served(client, private_bertopic):
    """The regression test for the access control gap.

    Before the fix this returned 404 "BERTopic model file not found" -- it had
    already got past both lookups, and would have rendered the visualization
    had the model file been present.
    """
    response = get_viz(client, 'secret_corpus', 'bertopic10')

    assert response.status_code == 404
    assert 'model file' not in response.content.decode().lower()


def normalised(response, *names):
    """The response body with the caller's own input removed.

    The error echoes back the name that was asked for, which tells the caller
    nothing it did not already know. What must not differ is everything else.
    """
    body = response.content.decode()
    for name in names:
        body = body.replace(name, '<requested>')
    return response.status_code, body


def test_private_dataset_is_indistinguishable_from_a_missing_one(client,
                                                                 private_bertopic):
    """Responses must not reveal that a private dataset exists."""
    private = get_viz(client, 'secret_corpus', 'bertopic10')
    missing = get_viz(client, 'no_such_corpus', 'bertopic10')

    assert normalised(private, 'secret_corpus') == \
        normalised(missing, 'no_such_corpus')


def test_private_analysis_name_is_not_confirmed(client, private_bertopic):
    """Nor may they reveal which analyses a private dataset holds."""
    Analysis.objects.create(name='lda5topics', dataset=private_bertopic)

    real = get_viz(client, 'secret_corpus', 'lda5topics')
    fake = get_viz(client, 'secret_corpus', 'no_such_analysis')

    assert normalised(real, 'lda5topics') == \
        normalised(fake, 'no_such_analysis')


def test_missing_dataset_is_rejected(client, db):
    response = get_viz(client, 'no_such_corpus', 'bertopic10')

    assert response.status_code == 404
    assert 'error' in json.loads(response.content)


def test_non_bertopic_analysis_is_rejected(client, sample_dataset):
    """The sample analysis is LDA, so it must not be treated as BERTopic."""
    response = get_viz(client, DATASET_NAME, ANALYSIS_NAME)

    assert response.status_code == 400
    assert 'not a BERTopic analysis' in json.loads(response.content)['error']


def test_missing_model_file_is_reported(client, sample_dataset):
    """A public BERTopic analysis with no pickle on disk is a clean 404."""
    Analysis.objects.create(name='bertopic10', dataset=sample_dataset)

    response = get_viz(client, DATASET_NAME, 'bertopic10')

    assert response.status_code == 404
    assert 'error' in json.loads(response.content)
