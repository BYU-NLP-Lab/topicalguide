from collections import OrderedDict
from .dataset import metrics as dataset_metrics, database_table as dataset_database_table, metric_exists as dataset_exists
from .analysis import metrics as analysis_metrics, database_table as analysis_database_table, metric_exists as analysis_exists
from .document.analysis import metrics as document_analysis_metrics, database_table as document_analysis_database_table, metric_exists as document_analysis_exists
from .topic import metrics as topic_metrics, database_table as topic_database_table, metric_exists as topic_exists
#~ from .document.pairwise import metrics as document_pairwise_metrics, database_table as document_pairwise_database_table, metric_exists as document_pairwise_exists
from .topic.pairwise import metrics as topic_pairwise_metrics, database_table as topic_pairwise_database_table, metric_exists as topic_pairwise_exists

all_metrics = OrderedDict()
name_extensions = OrderedDict([
    ('dataset:', dataset_metrics),
    ('analysis:', analysis_metrics),
    ('document-analysis:', document_analysis_metrics),
    ('topic:', topic_metrics),
    #~ ('document-pairwise:', document_pairwise_metrics), 
    ('topic-pairwise:', topic_pairwise_metrics), 
])
for extension in name_extensions:
    for name in name_extensions[extension]:
        all_metrics[extension + name] = name_extensions[extension][name]

all_tables = OrderedDict()
table_extensions = OrderedDict([
    ('dataset:', dataset_database_table),
    ('analysis:', analysis_database_table),
    ('document-analysis:', document_analysis_database_table),
    ('topic:', topic_database_table),
    #~ ('document-pairwise:', document_pairwise_database_table), 
    ('topic-pairwise:', topic_pairwise_database_table), 
])
for extension in name_extensions:
    for name in name_extensions[extension]:
        all_tables[extension + name] = table_extensions[extension]

all_metrics_exists = OrderedDict()
exists_extensions = OrderedDict([
    ('dataset:', dataset_exists),
    ('analysis:', analysis_exists),
    ('document-analysis:', document_analysis_exists),
    ('topic:', topic_exists),
    #~ ('document-pairwise:', document_pairwise_exists), 
    ('topic-pairwise:', topic_pairwise_exists), 
])
for extension in name_extensions:
    for name in name_extensions[extension]:
        all_metrics_exists[extension + name] = exists_extensions[extension]

