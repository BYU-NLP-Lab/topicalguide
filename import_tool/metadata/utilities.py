from __future__ import division, print_function, unicode_literals

from django.db import transaction
from django.db import connections
from visualize.models import *

def get_all_metadata_types(database_id):
    """Return all types by name and type in the form of a dictionary.
    The keys are a tuple (name, datatype) and the values are the database
    objects.
    database_id -- the dict key specifying the database in django
    """
    return {(t.name, t.datatype): t for t in \
        MetadataType.objects.using(database_id).all()}

def create_metadata_types(database_id, metadata_types, meta_types_db):
    """Add entries for all metadata types and add to existing hash.
    database_id -- the dict key specifying the database in django
    metadata_types -- the dictionary mapping keys to types
    meta_types_db -- what is returned by the get_all_metadata_types method in the
                     metadata.utilities module
    """
    with transaction.atomic(using=database_id):
        # commit
        to_commit = []
        meta_type_names = []
        meta_types = []
        for name, t in metadata_types.iteritems():
            if (name, t) not in meta_types_db:
                meta_type_names.append(name)
                meta_types.append(t)
                to_commit.append(MetadataType(name=name, datatype=t))
        MetadataType.objects.using(database_id).bulk_create(to_commit)
        
        # requery to get newly created ones
        query = MetadataType.objects.using(database_id)\
            .filter(name__in=meta_type_names, datatype__in=meta_types)
        for t in query:
            meta_types_db[(t.name, t.datatype)] = t

def create_metadata(database_id, db_objects, db_value_table, attr_name,
                    metadata_types, meta_types_db, metadata_values):
    """Add metadata to a database and link to given db_object.
    The indices in the db_objects list must match the corresponding 
    metadata_values list.
    databased_id -- the identifier of the database to use
    attr_name -- the name of the model attribute where the db_object reference
                 will be stored
    db_objects -- the database objects the metadata_values are added to
    db_value_table -- the table to store the values in
    metadata_types -- the dict with the datatypes of each metadata type
    meta_types_db -- the MetadataType objects in the database
    metadata_values -- a list of dicts, each dict containing the values
    """
    assert len(db_objects) == len(metadata_values)
    
    con = connections[database_id]
    query_count = len(con.queries)
    with transaction.atomic(using=database_id):
        # create the metadata values
        meta_values_db_to_create = []
        kwargs = { attr_name: None, 'metadata_type': None }
        for db_object, metadata_values_dict in zip(db_objects, metadata_values):
            for name, value in metadata_values_dict.items():
                kwargs[attr_name] = db_object
                kwargs['metadata_type'] = meta_types_db[(name, metadata_types[name])]
                meta_value_db = db_value_table(**kwargs)
                meta_value_db.set(value, metadata_types[name])
                meta_values_db_to_create.append(meta_value_db)
        db_value_table.objects.using(database_id)\
            .bulk_create(meta_values_db_to_create)
        
