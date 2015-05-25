from __future__ import division, print_function, unicode_literals
from visualize.models import MetadataType

def metadata_generator(dataset_db, documents_db):
    metadata_type = dataset_db.metadata_types.get(name='year', datatype='int')
    metadata_type.meaning = MetadataType.TIME
    metadata_type.save()
    return []
