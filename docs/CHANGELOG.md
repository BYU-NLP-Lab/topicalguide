# Changelog

## [Unreleased] - 2025-11-29

### Added - BERTopic Integration
- **BERTopic Analysis**: Full integration of BERTopic neural topic modeling
  - New analysis interface in `import_tool/analysis/interfaces/bertopic_analysis.py`
  - Support for both automatic topic discovery and fixed topic count
  - Subdocument support for long documents
  - Topic embeddings saved to `topic_embeddings.json`
  - Hierarchical topic visualization support
  - BERTopic-specific topic naming scheme
- **Embedding Distance Metric**: New pairwise topic metric for BERTopic analyses
  - Computes cosine distance between topic embeddings
  - Added to `import_tool/metric/topic/pairwise/embedding_distance.py`
  - Automatically computed for new BERTopic analyses
  - `extract_embeddings.py` utility to extract embeddings from existing models

### Added - UI Enhancements
- **Global Selectors**: Persistent dropdown selectors for Dataset, Analysis, and Topic Name Scheme
  - New `visualize/static/scripts/global_selectors.js`
  - Automatically selects first available dataset/analysis on load
  - Smart default for topic naming (prefers LLM-10words > BERTopic > Top3)
  - Integrated Topical Guide logo into selector bar
- **Dataset Metadata View**: New tab for viewing dataset-level metadata
  - New `visualize/static/scripts/dataset_metadata_view.js`
- **Topic Embeddings View**: BERTopic hierarchical topic visualization
  - New `visualize/static/scripts/topic_embeddings_view.js`
  - New `visualize/bertopic_viz.py` for serving BERTopic visualizations
- **Navigation Improvements**:
  - Moved logo to top selector row alongside Dataset/Analysis/Topic Names selectors
  - Removed duplicate logo from navigation menu
  - Removed Datasets tab (functionality replaced by global selector + Dataset Info tab)

### Added - Visualization Enhancements
- **Topics Over Time**:
  - Added min/max year range controls for filtering
  - Moved controls to left side, plot to right side
  - Reduced plot size to 600×400 for better screen fit
  - Restructured as top-level tab (removed from Visualizations submenu)
- **2D Plots**:
  - Added document picker dropdown control
  - Fixed crash when BERTopic outlier topics are present
  - Sync between document picker and point clicks
  - Restructured as top-level tab
- **Chord Diagram**:
  - Renamed "Correlation Metric" to "Distance Metric"
  - Added embedding distance support for BERTopic
  - Updated help text
  - Restructured as top-level tab
- **Force View**:
  - Audited and fixed memory leak issues
  - Updated to support embedding distance metric
  - Currently disabled but ready to re-enable
  - Code location: `visualize/static/scripts/visualizations/force_view.js`

### Added - Development Tools
- **Server Management Scripts**:
  - `start_server.sh`: Start Django server with logging
  - `stop_server.sh`: Stop background server
  - `tail_server_log.sh`: Tail the latest server log
  - Logs stored in `logs/` directory with timestamps

### Fixed - BERTopic Outlier Topic Handling
- **Null Topic Filtering**: Comprehensive filtering of BERTopic's outlier topic (-1)
  - Fixed "Topic null" appearing in document listings
  - Added null checks in all topic metrics
  - Updated metrics in `import_tool/metric/topic/`:
    - `token_count.py`
    - `type_count.py`
    - `document_entropy.py`
    - `word_entropy.py`
    - `pairwise/document_correlation.py`
    - `pairwise/word_correlation.py`
- **Documents View**: Filter out null/undefined topic keys from display
- **2D Plots**: Skip topics that don't exist in allTopics object

### Fixed - MALLET Subdocument Token Position Bug
- **Token Position Tracking**: Complete rewrite of subdocument handling in `mallet_analysis.py`
  - Old approach: Tracked token positions with offsets (error-prone)
  - New approach: Each subdocument is a completely separate document for MALLET
  - Eliminated complex offset tracking that caused position mismatches
  - Simplified token start index storage (subdocument-relative positions)
  - Fixes token position assertions that were failing

### Fixed - Entropy Calculation Edge Cases
- **Division by Zero Protection**: Added checks for zero probabilities in entropy calculations
  - `import_tool/metric/analysis/entropy.py`
  - `import_tool/metric/topic/document_entropy.py`
  - `import_tool/metric/topic/word_entropy.py`
  - Properly handles limit of p*log(p) as p→0

### Changed - Dependencies
- **Updated requirements.txt**:
  - Added BERTopic dependencies (bertopic, sentence-transformers, umap-learn, hdbscan)
  - Note: Requires Python ≤3.13 due to numba compatibility

### Changed - Default Topic Namers
- **Updated DEFAULT_TOPIC_NAMERS** in `import_tool/import_system_utilities.py`:
  - Added `BertopicNamer(5)` to default namers
  - Conditionally adds `LLMTopicNamer(n_words=10, n_docs=3)` if OpenAI API key available
  - Updated from `[TopNTopicNamer(3), TfitfTopicNamer(3)]`

### Changed - URL Routing
- **Added BERTopic visualization endpoint** in `visualize/urls.py`:
  - `/api/bertopic_viz/<dataset>/<analysis>/` for serving interactive BERTopic visualizations

### Documentation
- **BERTOPIC_EMBEDDINGS.md**: Comprehensive guide to BERTopic embedding features
- **Updated README.md**:
  - Added server management documentation
  - Marked BERTopic as implemented
  - Added EDA enhancements section
  - Added Force View to visualization opportunities
  - Moved to `docs/` directory structure
- **This CHANGELOG.md**: Detailed change log for this release

### Developer Notes
- All new BERTopic analyses automatically compute embedding distance metric
- Existing analyses need manual metric computation via `extract_embeddings.py` then running metric
- Force View is disabled but implementation complete and ready to re-enable in `force_view.js`
- Logo now integrated into global selector bar using flexbox layout
