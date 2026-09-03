-- Archive the orphaned dataset-1 subtree out of working/tg.sqlite3.
--
-- Context: TASKS.md 1.6. Dataset 1 and analysis 1 were deleted by hand from a
-- connection with PRAGMA foreign_keys off, which stranded their whole subtree
-- -- 5,312,660 rows that no code path can reach, because every query starts
-- from Dataset or Analysis. Analysis 2 belongs to the same deleted dataset and
-- is equally unreachable, so it goes with them: 5,312,660 rows in all.
--
-- This copies those rows into a standalone database before they are deleted.
-- Tables are created with CREATE TABLE AS SELECT: data only, no indexes and no
-- constraints, which is what an archive wants -- the rows reference parents
-- that no longer exist, so re-imposing the foreign keys would reject them.
--
-- Run against the LIVE database (it only reads from it):
--   sqlite3 working/tg.sqlite3 < scripts/archive_dataset1_subtree.sql
--
-- The six subtree tables that hold no rows -- documentmetricvalue,
-- documentpairwisemetricvalue, topicmetadatavalue, topicwordtypemetric,
-- excludedword and stopword -- are deliberately not created.

ATTACH DATABASE 'working/tg-dataset1-subtree.sqlite3' AS archive;

-- The two parent rows are already gone; what survives is their children.
-- Row counts are asserted against the live database in the verification step.

CREATE TABLE archive.visualize_datasetmetadatavalue AS
    SELECT * FROM main.visualize_datasetmetadatavalue WHERE dataset_id = 1;

CREATE TABLE archive.visualize_datasetmetricvalue AS
    SELECT * FROM main.visualize_datasetmetricvalue WHERE dataset_id = 1;

-- Analysis 2 itself: a live row whose parent dataset is missing.
CREATE TABLE archive.visualize_analysis AS
    SELECT * FROM main.visualize_analysis WHERE dataset_id = 1;

CREATE TABLE archive.visualize_analysismetadatavalue AS
    SELECT * FROM main.visualize_analysismetadatavalue WHERE analysis_id IN (1, 2);

CREATE TABLE archive.visualize_analysismetricvalue AS
    SELECT * FROM main.visualize_analysismetricvalue WHERE analysis_id IN (1, 2);

CREATE TABLE archive.visualize_document AS
    SELECT * FROM main.visualize_document WHERE dataset_id = 1;

CREATE TABLE archive.visualize_documentmetadatavalue AS
    SELECT * FROM main.visualize_documentmetadatavalue
    WHERE document_id IN (SELECT id FROM main.visualize_document WHERE dataset_id = 1);

CREATE TABLE archive.visualize_documentanalysismetricvalue AS
    SELECT * FROM main.visualize_documentanalysismetricvalue
    WHERE analysis_id IN (1, 2)
       OR document_id IN (SELECT id FROM main.visualize_document WHERE dataset_id = 1);

CREATE TABLE archive.visualize_topic AS
    SELECT * FROM main.visualize_topic WHERE analysis_id IN (1, 2);

CREATE TABLE archive.visualize_topicmetricvalue AS
    SELECT * FROM main.visualize_topicmetricvalue
    WHERE topic_id IN (SELECT id FROM main.visualize_topic WHERE analysis_id IN (1, 2));

CREATE TABLE archive.visualize_topicname AS
    SELECT * FROM main.visualize_topicname
    WHERE topic_id IN (SELECT id FROM main.visualize_topic WHERE analysis_id IN (1, 2));

CREATE TABLE archive.visualize_topicpairwisemetricvalue AS
    SELECT * FROM main.visualize_topicpairwisemetricvalue
    WHERE origin_topic_id IN (SELECT id FROM main.visualize_topic WHERE analysis_id IN (1, 2))
       OR ending_topic_id IN (SELECT id FROM main.visualize_topic WHERE analysis_id IN (1, 2));

-- The bulk: 2,653,815 tokens and one topic assignment each. Analysis 1 is the
-- only tokenization in this database that kept function words (155,287 'the',
-- 100,301 'of', 61,517 'and'; the surviving analyses have none), which is the
-- one thing here that exists nowhere else.
CREATE TABLE archive.visualize_wordtoken AS
    SELECT * FROM main.visualize_wordtoken WHERE analysis_id IN (1, 2);

CREATE TABLE archive.visualize_wordtokentopic AS
    SELECT * FROM main.visualize_wordtokentopic
    WHERE token_id IN (SELECT id FROM main.visualize_wordtoken WHERE analysis_id IN (1, 2));

-- The 160 word types used only by these analyses -- the stopword vocabulary.
-- Left in place in the live database, where they are merely unreferenced, but
-- archived so the tokenization can be read back on its own terms.
CREATE TABLE archive.visualize_wordtype AS
    SELECT * FROM main.visualize_wordtype
    WHERE id IN (SELECT word_type_id FROM main.visualize_wordtoken WHERE analysis_id IN (1, 2)
                 EXCEPT
                 SELECT word_type_id FROM main.visualize_wordtoken WHERE analysis_id NOT IN (1, 2));

DETACH DATABASE archive;
