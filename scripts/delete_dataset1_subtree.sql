-- Delete the orphaned dataset-1 subtree from working/tg.sqlite3.
--
-- Context: TASKS.md 1.6. Run scripts/archive_dataset1_subtree.sql FIRST -- this
-- script is destructive and assumes working/tg-dataset1-subtree.sqlite3 exists
-- and has been verified against the row counts recorded in 1.6.
--
--   sqlite3 working/tg.sqlite3 < scripts/delete_dataset1_subtree.sql
--
-- foreign_keys is ON deliberately. It is off by default in the sqlite3 shell,
-- and that default is how these orphans were created in the first place; with
-- it on, any statement here that would strand a row is rejected rather than
-- silently accepted. That makes the pragma a check on this script, so the
-- deletes run leaf-first: assignments, then tokens, then the metric and name
-- rows, then topics, then documents, then the analysis, then the dataset-level
-- values.

PRAGMA foreign_keys = ON;

BEGIN;

-- Topic assignments: children of both wordtoken and topic, so they go first.
DELETE FROM visualize_wordtokentopic
 WHERE token_id IN (SELECT id FROM visualize_wordtoken WHERE analysis_id IN (1, 2))
    OR topic_id IN (SELECT id FROM visualize_topic WHERE analysis_id IN (1, 2));

DELETE FROM visualize_wordtoken WHERE analysis_id IN (1, 2);

DELETE FROM visualize_documentanalysismetricvalue
 WHERE analysis_id IN (1, 2)
    OR document_id IN (SELECT id FROM visualize_document WHERE dataset_id = 1);

DELETE FROM visualize_topicpairwisemetricvalue
 WHERE origin_topic_id IN (SELECT id FROM visualize_topic WHERE analysis_id IN (1, 2))
    OR ending_topic_id IN (SELECT id FROM visualize_topic WHERE analysis_id IN (1, 2));

DELETE FROM visualize_topicname
 WHERE topic_id IN (SELECT id FROM visualize_topic WHERE analysis_id IN (1, 2));

DELETE FROM visualize_topicmetricvalue
 WHERE topic_id IN (SELECT id FROM visualize_topic WHERE analysis_id IN (1, 2));

DELETE FROM visualize_topic WHERE analysis_id IN (1, 2);

DELETE FROM visualize_documentmetadatavalue
 WHERE document_id IN (SELECT id FROM visualize_document WHERE dataset_id = 1);

DELETE FROM visualize_document WHERE dataset_id = 1;

DELETE FROM visualize_analysismetadatavalue WHERE analysis_id IN (1, 2);
DELETE FROM visualize_analysismetricvalue WHERE analysis_id IN (1, 2);

-- Analysis 2: the one live row whose parent dataset was already missing.
DELETE FROM visualize_analysis WHERE dataset_id = 1;

DELETE FROM visualize_datasetmetadatavalue WHERE dataset_id = 1;
DELETE FROM visualize_datasetmetricvalue WHERE dataset_id = 1;

COMMIT;

-- Must return no rows. If it returns any, the transaction above missed a table.
SELECT 'REMAINING VIOLATIONS: ' || count(*) FROM pragma_foreign_key_check;
