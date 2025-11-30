# BERTopic Embeddings and Visualizations

This document describes the embedding-based features added to support BERTopic topic models.

## Overview

BERTopic models use neural embeddings to represent topics in a high-dimensional semantic space. These embeddings enable advanced visualizations and similarity metrics that are not available for traditional LDA/HLDA models.

## Features Implemented

### 1. Topic Embedding Storage

**File**: `import_tool/analysis/interfaces/bertopic_analysis.py`

Topic embeddings are now automatically saved during BERTopic analysis:

- **Location**: `analyses/{analysis_name}/topic_embeddings.json`
- **Format**: JSON dictionary mapping topic IDs to embedding vectors
- **Source**: BERTopic's `topic_embeddings_` attribute (centroid embeddings for each topic)

**Implementation**:
```python
def _save_topic_embeddings(self, topic_model):
    """Save topic embeddings for visualization and similarity calculations."""
    embeddings_dict = {}
    topic_info = topic_model.get_topic_info()

    for idx, topic_id in enumerate(topic_info['Topic']):
        if topic_id != -1:  # Skip outlier topic
            embedding = topic_model.topic_embeddings_[idx].tolist()
            embeddings_dict[str(topic_id)] = embedding

    with io.open(self.topic_embeddings_file, 'w', encoding='utf-8') as f:
        json.dump(embeddings_dict, f)
```

### 2. Embedding Distance Metric

**File**: `import_tool/metric/topic/pairwise/embedding_distance.py`

A new pairwise metric computes semantic similarity between topics using cosine distance in embedding space.

**Key Features**:
- Automatically computed for all BERTopic analyses
- Uses cosine distance: `1 - cosine_similarity`
- Range: 0 (identical) to 2 (opposite)
- Stored in database as `PairwiseTopicMetricValue` with metric name "Embedding Distance"

**Usage**:
```bash
# Manually compute for an existing analysis
python import_tool/metric/topic/pairwise/embedding_distance.py \
    -d state_of_the_union \
    -a bertopicauto
```

**Registration**: Added to `import_tool/metric/topic/pairwise/__init__.py` to run automatically during import.

### 3. BERTopic Native Visualizations

**Files**:
- Backend: `visualize/bertopic_viz.py`
- Frontend: `visualize/static/scripts/topic_embeddings_view.js`
- URL routing: `visualize/urls.py`

Provides access to BERTopic's built-in Plotly visualizations through the Topical Guide UI.

**Available Visualizations**:

1. **Topics Map** (`visualize_topics()`)
   - 2D scatter plot of topics in embedding space
   - Uses UMAP or t-SNE for dimensionality reduction
   - Topics closer together are more semantically similar
   - Interactive: hover for details, click to explore

2. **Documents Map** (`visualize_documents()`)
   - 2D visualization of individual documents colored by their assigned topics
   - Helps identify document clusters and outliers
   - Shows how well documents fit within their assigned topics

3. **Similarity Heatmap** (`visualize_heatmap()`)
   - Matrix showing pairwise similarity between all topics
   - Color-coded for easy comparison
   - Interactive tooltips with exact values

4. **Topic Hierarchy** (`visualize_hierarchy()`)
   - Hierarchical clustering dendrogram
   - Shows how topics group together at different similarity levels
   - Useful for understanding topic structure

5. **Top Words** (`visualize_barchart()`)
   - Bar charts of most representative words per topic
   - Shows first 10 topics with top 10 words each
   - Side-by-side comparison

6. **Term Rank** (`visualize_term_rank()`)
   - Shows how c-TF-IDF scores decline as more terms are added to topic representations
   - Useful for determining optimal number of words per topic
   - Helps assess topic quality

7. **Topics Over Time** (`visualize_topics_over_time()`)
   - Track how topic frequencies change over time
   - Requires temporal data (timestamps for documents)
   - Perfect for datasets like State of the Union speeches

8. **Topics Per Class** (`visualize_topics_per_class()`)
   - Compare topic representations across different document classes
   - Requires class labels (e.g., by president, party, decade)
   - Shows how different groups approach topics

9. **Hierarchical Documents** (`visualize_hierarchical_documents()`)
   - View documents across different levels of the topic hierarchy
   - Combines hierarchy and document views

**Access**: Navigate to **Topic Space** in the Topical Guide UI (only available for BERTopic analyses).

### 4. Embedding Distance in Similar Topics Tab

The "Similar Topics" tab in the single topic view now includes an "Embedding Distance" column alongside existing metrics like:
- Document Correlation
- Word Correlation

This column shows the semantic distance between the current topic and other topics based on their neural embeddings.

## Technical Details

### Cosine Distance Calculation

```python
def cosine_distance(vec1, vec2):
    """
    Compute cosine distance between two vectors.
    Returns a value between 0 (identical) and 2 (opposite).
    """
    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    mag1 = math.sqrt(sum(a * a for a in vec1))
    mag2 = math.sqrt(sum(b * b for b in vec2))

    if mag1 == 0 or mag2 == 0:
        return 1.0  # Undefined, return neutral value

    cosine_sim = dot_product / (mag1 * mag2)
    return 1.0 - cosine_sim
```

### API Endpoint

**URL**: `/bertopic-viz/<dataset>/<analysis>/<viz_type>/`

**Parameters**:
- `dataset`: Dataset name
- `analysis`: Analysis name (must be a BERTopic analysis)
- `viz_type`: One of `topics`, `documents`, `heatmap`, `hierarchy`, `hierarchical_documents`, `barchart`, `term_rank`, `topics_over_time`, `topics_per_class`

**Returns**: HTML containing interactive Plotly visualization

**Example**:
```
GET /bertopic-viz/state_of_the_union/bertopicauto/topics/
```

### Frontend Integration

The visualization view loads BERTopic visualizations in an iframe:

```javascript
var url = "/bertopic-viz/" + dataset + "/" + analysis + "/" + vizType + "/";

d3.select("#embeddings-plot")
    .append("iframe")
    .attr("src", url)
    .attr("width", "100%")
    .attr("height", "700px");
```

## Benefits

### For Researchers

1. **Semantic Similarity**: Understand which topics are semantically related, not just through word overlap
2. **Visual Exploration**: Interactive 2D maps make it easy to explore topic structure
3. **Hierarchical Relationships**: See how topics group at different levels of granularity
4. **Quality Assessment**: Visualizations help assess whether topics are well-separated or overlapping

### For Topic Model Comparison

- Compare embedding-based distance vs. word-based correlation
- Identify topics that are:
  - **Semantically similar but lexically different** (low embedding distance, low word correlation)
  - **Lexically similar but semantically different** (high word correlation, high embedding distance)

## Upgrading Existing Analyses

If you have existing BERTopic analyses that were created before this feature was added:

1. Re-run the analysis to generate embeddings:
   ```bash
   python tg.py analyze state_of_the_union \
       --analysis-tool BERTopic \
       --number-of-topics 20 \
       --stopwords stopwords/english_all.txt \
       --verbose
   ```

2. The embedding distance metric will be computed automatically during import.

3. Visualizations will be available in the UI.

## Dependencies

**Required packages** (already in `requirements.txt` for BERTopic):
- `bertopic` - Core BERTopic library
- `sentence-transformers` - For generating embeddings
- `plotly` - For interactive visualizations
- `umap-learn` - For dimensionality reduction
- `hdbscan` - For clustering

## Future Enhancements

Potential additions:

1. **Hierarchical Topics (High Priority)**: Full data model integration for BERTopic hierarchies
   - **Current Status**: Visualization available via `visualize_hierarchy()` and `visualize_hierarchical_documents()`
   - **Needed**: Implement `get_hierarchy_iterator()` in `bertopic_analysis.py` to populate the database hierarchy
   - **BERTopic Method**: Use `topic_model.hierarchical_topics()` to generate the hierarchy
   - **Benefit**: Enable browsing topic trees similar to HLDA but with embedding-based hierarchies

2. **Cross-Dataset Alignment**: Compare topics across different datasets using embedding alignment
   - Use embedding space to map equivalent topics across analyses

3. **Topic Merging/Splitting**: Use embeddings to suggest topic consolidation or division
   - Identify topics that should be merged (high embedding similarity)
   - Identify topics that are too broad (high internal variance)

4. **Custom Embedding Models**: Allow users to specify different sentence transformer models
   - Currently fixed to "all-MiniLM-L6-v2"
   - Add UI option to select from common models (e.g., "all-mpnet-base-v2", domain-specific models)

5. **Save Auxiliary Data for Advanced Visualizations**: Store documents, timestamps, and class labels during analysis
   - Currently some visualizations may fail if auxiliary data files don't exist
   - Modify `bertopic_analysis.py` to save this data automatically

## Examples

### Example 1: Finding Semantically Similar Topics

In the Topics view:
1. Click on a topic to view its details
2. Go to the "Similar Topics" tab
3. Sort by "Embedding Distance" column (ascending)
4. Topics at the top are most semantically similar

### Example 2: Exploring Topic Space

In Topic Space:
1. Select "Topics Map" to see topics in 2D space
2. Hover over points to see topic names
3. Zoom and pan to explore different regions
4. Try "Documents Map" to see how individual documents cluster by topic

### Example 3: Understanding Topic Hierarchy

1. Navigate to Topic Space
2. Select "Topic Hierarchy"
3. Examine the dendrogram to see how topics cluster
4. Identify major theme groups and sub-themes

### Example 4: Temporal Analysis

1. Navigate to Topic Space
2. Select "Topics Over Time"
3. See how topic frequencies evolve across different time periods
4. Identify trending topics and declining themes

## Troubleshooting

### "No embedding distances found"

**Cause**: Analysis was run before embedding support was added.

**Solution**: Re-run the analysis with the latest code.

### "BERTopic model file not found"

**Cause**: Model pickle file is missing or corrupted.

**Solution**: Re-run the analysis.

### Visualization iframe shows error

**Cause**: Django view error or missing dependencies.

**Solution**:
1. Check server logs for detailed error message
2. Ensure all dependencies are installed
3. Verify the model file exists and is valid

### "Documents file not found" error

**Cause**: Visualizations like Documents Map and Hierarchical Documents require the original document text.

**Solution**: These visualizations need auxiliary data files that may not be saved by default. This is a known limitation (see Future Enhancements #5).

### "Timestamp data not found" or "Class label data not found"

**Cause**: Topics Over Time and Topics Per Class require temporal/class metadata.

**Solution**:
1. For temporal analysis, ensure your dataset includes timestamp information
2. For class-based analysis, add class labels to your documents
3. These are advanced features that may not be available for all datasets

## See Also

- [BERTopic Documentation](https://maartengr.github.io/BERTopic/)
- [README.md](README.md) - Main project documentation
- [LLM_TOPIC_NAMING.md](LLM_TOPIC_NAMING.md) - LLM-based topic naming feature
