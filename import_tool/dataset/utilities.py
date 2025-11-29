import io
from os.path import join
from django.db import transaction
from django.db import connections
from visualize.models import *
from visualize.models import MAX_ELEMENTS_FOR_IN_OPERATOR
from import_tool.metadata.utilities import create_metadata_types, create_metadata
from import_tool.tools import VerboseTimer

MAX_DOCUMENTS_TO_COMMIT = 20000 # affects memory usage
MAX_DOCUMENTS_TO_QUERY = MAX_ELEMENTS_FOR_IN_OPERATOR # affects query size
RELATIVE_DOCUMENT_DIRECTORY = 'documents'

def create_dataset(database_id, dataset, dataset_dir, meta_types_db, **kwargs):
    """Create the dataset entry and metadata entries.
    database_id -- the dict key specifying the database in django
    dataset -- an AbstractDataset type
    dataset_dir -- the directory that the dataset can use to store documents
                   and analysis directories to store intermediate results
    meta_types_db -- what is returned by the get_all_metadata_types method in the
                     metadata.utilities module
    
    Keyword Arguments:
    public -- make this dataset public (anybody can explore it) (default False)
    public_documents -- make the document text publicly available (default True)
    
    Return the Dataset django database object after creation.
    """
    with transaction.atomic(using=database_id):
        dataset_db, created = Dataset.objects.using(database_id).\
                get_or_create(name=dataset.name, 
                              dataset_dir=dataset_dir)
        
        if created:
            dataset_db.public = kwargs.setdefault('public', False)
            dataset_db.public_documents = kwargs.setdefault('public_documents', True)
            dataset_db.visible = False
            dataset_db.save()
            metadata_types = dataset.metadata_types
            create_metadata_types(database_id, metadata_types, meta_types_db)
            create_metadata(database_id, [dataset_db], 
                            DatasetMetadataValue, 'dataset',
                            metadata_types, 
                            meta_types_db, 
                            [dataset.metadata])
    return dataset_db

def create_documents(database_id, dataset_db, dataset, 
                     meta_types_db, verbose=False):
    """Create entries for documents and their associated metadata.
    database_id -- the dict key specifying the database in django
    dataset_db -- the Dataset django database object
    dataset -- the AbstractDataset object
    meta_types_db -- what is returned by the get_all_metadata_types method in the
                     metadata.utilities module
    verbose -- if True print out progress to the console; do nothing otherwise
    """
    document_dir = join(dataset_db.dataset_dir, RELATIVE_DOCUMENT_DIRECTORY)
    document_metadata_types = dataset.document_metadata_types
    create_metadata_types(database_id, document_metadata_types,
                          meta_types_db)
    # Helper function
    def bulk_create_documents(documents, metadata):
        if len(documents) == 0: return
        with transaction.atomic(using=database_id):
            low_high = (documents[0].index, documents[-1].index)
            # create document entries
            Document.objects.using(database_id).bulk_create(documents)
            names = []
            for doc in documents:
                names.append(doc.filename)
            # retrieve documents from database since bulk_create doesn't return
            # a primary key
            documents_db = \
                Document.objects.using(database_id).filter(dataset=dataset_db,
                index__range=low_high).order_by('index')
            # create metadata entries
            create_metadata(database_id, 
                            documents_db, 
                            DocumentMetadataValue, 'document',
                            document_metadata_types,
                            meta_types_db,
                            metadata)
        del documents[:]
        del metadata[:]
    
    documents_to_commit = []
    documents_metadata_to_commit = []
    already_created_documents = {d.filename: d for d in Document.objects.using(database_id).filter(dataset=dataset_db.id)}
    if verbose: timer = VerboseTimer(len(dataset))
    for doc_index, doc in enumerate(dataset):
        if verbose: timer.tick()
        filename = doc.name
        # Create document and get metadata
        if filename not in already_created_documents:
            full_path = os.path.join(document_dir, filename)
            metadata = doc.metadata
            content = doc.content
            with io.open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            doc_db = Document(dataset=dataset_db, filename=filename, index=doc_index, length=len(content))
            documents_to_commit.append(doc_db)
            documents_metadata_to_commit.append(metadata)
        # Bulk create periodically to keep memory usage minimized
        if len(documents_to_commit) > MAX_DOCUMENTS_TO_COMMIT:
            bulk_create_documents(documents_to_commit, 
                documents_metadata_to_commit)
    bulk_create_documents(documents_to_commit, documents_metadata_to_commit)
    if verbose: print("Document count:", doc_index + 1)
