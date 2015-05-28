## About this Document

This document serves to inform users of the import system which database tables are effected during the differenct stages of the import process.

## Importing a Dataset

While importing a dataset the database tables effected are (in order):
1. Dataset
2. MetadataType and Ordinal
3. DatasetMetadataValue
4. Document
5. MetadataType and Ordinal
6. DocumentMetadataValue
7. Metric
8. DatasetMetricValue

## Importing an Analysis

The tables effected during an analysis run are as follows:
1. Analysis
2. MetadataType and Ordinal
3. AnalysisMetadataValue
4. WordType
5. WordToken and Topic
6. Stopword
7. ExcludedWord
8. TopicNameScheme and TopicName
9. DocumentAnalysisMetricValue
10. AnalysisMetricValue
11. TopicMetricValue
12. TopicPairwiseMetricValue

