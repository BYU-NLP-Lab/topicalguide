from __future__ import division, print_function, unicode_literals

from django.db import transaction
from django.db import connections
from visualize.models import *
from import_tool import basic_tools

def get_all_metadata_types(database_id, dataset_db):
    """Return all types by name and type in the form of a dictionary.
    The keys are a tuple (name, datatype) and the values are the database
    objects.
    database_id -- the dict key specifying the database in django
    """
    return {(t.name, t.datatype): t for t in \
        MetadataType.objects.using(database_id).filter(dataset=dataset_db)}

def create_metadata_types(database_id, dataset_db, metadata_types, meta_types_db, metadata_ordinals={}):
    """Add entries for all metadata types and add to existing hash.
    database_id -- the dict key specifying the database in django
    metadata_types -- the dictionary mapping keys to types
    meta_types_db -- what is returned by the get_all_metadata_types method in the
                     metadata.utilities module
    metadata_ordinals -- metadata type name to list of lists of string(s) mapping
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
                new_metadata_type = MetadataType(dataset=dataset_db, name=name, datatype=t)
                to_commit.append(new_metadata_type)
        MetadataType.objects.using(database_id).bulk_create(to_commit)
        
        # requery to get newly created ones
        query = MetadataType.objects.using(database_id)\
            .filter(name__in=meta_type_names, datatype__in=meta_types)
        for t in query:
            meta_types_db[(t.name, t.datatype)] = t
        
        # create the ordinal values now that the metadata types have id's
        for name, t in metadata_types.iteritems():
            if t == MetadataType.ORDINAL: # create the ordinal values and such before proceeding
                meta_type_db = meta_types_db[(name, t)]
                ordinals_to_commit = []
                for index, ordinal_lists in enumerate(metadata_ordinals[name]):
                    for ordinal_name in ordinal_lists:
                        ordinal = Ordinal(sequence=meta_type_db, value=index, name=ordinal_name)
                        ordinals_to_commit.append(ordinal)
                Ordinal.objects.using(database_id).bulk_create(ordinals_to_commit)

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
                meta_value_db.set(value)
                meta_values_db_to_create.append(meta_value_db)
        db_value_table.objects.using(database_id)\
            .bulk_create(meta_values_db_to_create)
        
def all_document_metadata_checker(dataset, die_on_error=True):
    """Check the dataset's documents for incorrect metadata.
    dataset -- an AbstractDataset
    die_on_error -- indicate if the method should throw an error if inconsistencies
                    are found, otherwise they are added to the returned data
    Return dictionaries or lists mapping documents to metadata or metadata key violations.
    Return (actual_doc_metadata_types, doc_no_metadata, doc_metadata_type_violations, doc_required_metadata_violations).
    Return (dict:key=>string, list, dict:key=>list, dict:key=>list).
    If die_on_error = True, only the actual_doc_metadata_types is collected and accurate.
    """
    actual_doc_metadata_types = {}
    doc_no_metadata = {}
    doc_metadata_type_violations = {}
    doc_required_metadata_violations = {}
    
    doc_meta_types = dataset.document_metadata_types
    doc_meta_required = dataset.document_required_metadata
    doc_meta_ordinals = dataset.document_metadata_ordinals
    
    # collect the valid ordinal values as sets
    doc_meta_ordinal_sets = {}
    for ord_name, ord_lists in doc_meta_ordinals.iteritems():
        s = set()
        for ord_list in ord_lists:
            for ord_val in ord_list:
                s.add(ord_val)
        doc_meta_ordinal_sets[ord_name] = s
    
    # initialize the actual values, from there they can only degrade
    for key, value in doc_meta_types.iteritems():
        actual_doc_metadata_types[key] = value
    
    for doc in dataset:
        doc_uri = doc.source
        doc_metadata = doc.metadata
        
        # find documents with no metadata
        if len(doc_metadata) == 0:
            doc_no_metadata.append(doc_uri)
        
        # find documents with the wrong types
        offending_keys = basic_tools.verify_types(doc_meta_types, doc_metadata, doc_meta_ordinal_sets)
        if len(offending_keys) > 0:
            if die_on_error:
                raise Exception('Metadata types did not match those found.')
            else:
                doc_metadata_type_violations[doc_uri] = offending_keys
        
        # find documents missing required metadata
        missing = []
        for meta_name in doc_meta_required:
            if meta_name not in doc_metadata:
                missing.append(meta_name)
        if len(missing) > 0:
            if die_on_error:
                raise Exception('Document missing required metadata values.')
            else:
                doc_required_metadata_violations[doc_uri] = missing
        
        # verify the types, downgrading as needed
        basic_tools.collect_types(actual_doc_metadata_types, doc_metadata, doc_meta_ordinal_sets)
    
    return (actual_doc_metadata_types, doc_no_metadata, doc_metadata_type_violations, doc_required_metadata_violations)
