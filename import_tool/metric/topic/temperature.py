from __future__ import division, print_function, unicode_literals
from visualize.models import MetadataType
from django.db.models import Count
from django.db import connections
import scipy.stats

metric_name='Temperature'

"""
Use the following to perform the query raw (changing the topic id).

SELECT "visualize_documentmetadatavalue"."int_value", COUNT("visualize_documentmetadatavalue"."int_value") AS "count"
FROM "visualize_wordtoken" INNER JOIN "visualize_wordtokentopic" ON ( "visualize_wordtoken"."id" = "visualize_wordtokentopic"."token_id" ) 
    INNER JOIN "visualize_document" ON ( "visualize_wordtoken"."document_id" = "visualize_document"."id" ) 
    INNER JOIN "visualize_documentmetadatavalue" ON ( "visualize_document"."id" = "visualize_documentmetadatavalue"."document_id" ) 
    INNER JOIN "visualize_metadatatype" ON ( "visualize_documentmetadatavalue"."metadata_type_id" = "visualize_metadatatype"."id" )
WHERE ("visualize_wordtokentopic"."topic_id" = 51 AND "visualize_metadatatype"."name" = "year")
GROUP BY "visualize_documentmetadatavalue"."int_value"


For some reason Django is adding two joins that look similar in a row, eliminating either yields the correct answer

SELECT "visualize_documentmetadatavalue"."int_value", COUNT("visualize_documentmetadatavalue"."int_value") AS "count"
FROM "visualize_wordtoken" INNER JOIN "visualize_wordtokentopic" ON ( "visualize_wordtoken"."id" = "visualize_wordtokentopic"."token_id" ) 
    INNER JOIN "visualize_document" ON ( "visualize_wordtoken"."document_id" = "visualize_document"."id" ) 
    LEFT OUTER JOIN "visualize_documentmetadatavalue" ON ( "visualize_document"."id" = "visualize_documentmetadatavalue"."document_id" ) 
    INNER JOIN "visualize_documentmetadatavalue" T6 ON ( "visualize_document"."id" = T6."document_id" ) 
    INNER JOIN "visualize_metadatatype" ON ( T6."metadata_type_id" = "visualize_metadatatype"."id" )
WHERE ("visualize_wordtokentopic"."topic_id" = 51 AND "visualize_metadatatype"."name" = "year")
GROUP BY "visualize_documentmetadatavalue"."int_value";
"""

def compute_metric(database_id, dataset_db, analysis_db):
    topics_iter = analysis_db.topics.all()
    results = []
    
    for topic in topics_iter:
        topic_token_counts_query = topic.tokens.values_list('document__metadata_values__int_value', 'document__metadata_values__metadata_type__meaning')
        yearcounter = {}
        for row in topic_token_counts_query:
            if row[1] == MetadataType.TIME:
                yearcounter[row[0]] = yearcounter.setdefault(row[0],0)+1
        if len(yearcounter) > 1:
            xypairs = [(k, yearcounter[k]) for k in yearcounter]
            slope, intercept, r_value, p_value, std_err = scipy.stats.linregress(xypairs)
            results.append({
                'topic_id': topic.id,
                'value': slope,
            })
    #~ print('\n'.join([unicode(e) for e in results]))
    #~ raise Exception('stop')
    
    return results
