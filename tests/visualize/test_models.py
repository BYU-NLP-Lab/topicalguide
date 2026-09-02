"""Tests for the model-level metadata accessors.

`MetadataValue` stores a value in one of five typed columns and reports it back
through `value()` and `type()`. The interesting cases are the falsy ones: a
count of 0, a `False` flag or an empty string are real values, and used to read
back as `None` because the accessors picked the populated column by truthiness
(TASKS.md 1.1).
"""

import pytest

from tests.conftest import set_metadata

from visualize.models import (Dataset, DatasetMetadataValue, Document,
                              DocumentMetadataValue)


# (datatype, stored value, what value() should return). Each row is a falsy
# value in its own type, plus one ordinary value of that type as a control.
FALSY_VALUES = [
    ('int', 0, 0),
    ('int', 42, 42),
    ('float', 0.0, 0.0),
    ('float', 2.5, 2.5),
    ('bool', False, False),
    ('bool', True, True),
    ('text', '', ''),
    ('text', 'a value', 'a value'),
]


@pytest.fixture
def dataset(db):
    return Dataset.objects.create(name='metadata_corpus', visible=True)


@pytest.mark.parametrize('datatype, stored, expected', FALSY_VALUES)
def test_value_round_trips_falsy_values(dataset, datatype, stored, expected):
    metadata = set_metadata(DatasetMetadataValue, 'dataset', dataset,
                            'a_field', stored, datatype=datatype)

    assert metadata.value() == expected
    assert type(metadata.value()) is type(expected)


@pytest.mark.parametrize('datatype, stored, expected', FALSY_VALUES)
def test_type_reports_the_datatype_of_falsy_values(dataset, datatype, stored,
                                                   expected):
    metadata = set_metadata(DatasetMetadataValue, 'dataset', dataset,
                            'a_field', stored, datatype=datatype)

    assert metadata.type() == datatype


@pytest.mark.parametrize('datatype, stored, expected', FALSY_VALUES)
def test_value_survives_a_round_trip_through_the_database(dataset, datatype,
                                                          stored, expected):
    set_metadata(DatasetMetadataValue, 'dataset', dataset, 'a_field', stored,
                 datatype=datatype)

    reloaded = DatasetMetadataValue.objects.get(dataset=dataset,
                                                metadata_type__name='a_field')

    assert reloaded.value() == expected
    assert reloaded.type() == datatype


def test_datetime_values_report_as_strings(dataset):
    # Offset-aware, because settings.USE_TZ is on and a naive datetime would
    # only warn here while being stored as UTC anyway.
    metadata = set_metadata(DatasetMetadataValue, 'dataset', dataset, 'when',
                            '2001-02-03T00:00:00+00:00', datatype='datetime')

    assert metadata.type() == 'datetime'
    assert metadata.value() == str(metadata.datetime_value)
    assert metadata.value().startswith('2001-02-03')


def test_an_empty_value_reports_no_value_and_no_type(dataset):
    metadata = DatasetMetadataValue(dataset=dataset)

    assert metadata.value() is None
    assert metadata.type() is None


def test_two_populated_columns_are_rejected(dataset):
    metadata = DatasetMetadataValue(dataset=dataset)
    metadata.set(0, 'int')
    metadata.set('', 'text')

    with pytest.raises(Exception, match='more than one type'):
        metadata.value()
    with pytest.raises(Exception, match='more than one type'):
        metadata.type()


def test_set_rejects_an_unsupported_datatype(dataset):
    with pytest.raises(Exception, match="aren't supported"):
        DatasetMetadataValue(dataset=dataset).set('x', 'complex')


def test_str_of_a_zero_valued_metadata_is_the_zero(dataset):
    metadata = set_metadata(DatasetMetadataValue, 'dataset', dataset, 'count',
                            0, datatype='int')

    assert str(metadata) == '0'


def test_document_metadata_round_trips_a_zero_year(db):
    """The document metadata table has its own __str__; year 0 is a real year."""
    dataset = Dataset.objects.create(name='year_zero_corpus', visible=True)
    document = Document.objects.create(dataset=dataset, index=0,
                                       filename='doc0.txt', source='',
                                       length=100)
    metadata = set_metadata(DocumentMetadataValue, 'document', document,
                            'year', 0, datatype='int')

    assert metadata.value() == 0
    assert metadata.type() == 'int'
