# The Topical Guide

Copyright 2010-2015 Brigham Young University

## About

The Topical Guide is a tool aimed at helping laymen and experts intuitively
navigate the topic distribution produced by a topic model, such as LDA, over a
given dataset.

Learn more by visiting [the wiki](https://github.com/BYU-NLP-Lab/topicalguide/wiki).

## Requirements

- Python 3.10 or higher
- Django 4.2 (LTS)
- MALLET (for topic modeling)
- See `requirements.txt` for complete list of dependencies

## Installation

### 1. Clone the Source

Clone the source with the following:
    
    git clone https://github.com/BYU-NLP-Lab/topicalguide.git

Then navigate to the `topicalguide` directory.

### 2. Install Dependencies

**It is strongly recommended to use a virtual environment.** You can create one using Python's built-in `venv` module:

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

You must activate your virtual environment any time that `(venv)` does not appear in front of your command line.

Once activated, install all dependencies:

```bash
pip install -r requirements.txt
```

Note: If you encounter issues, ensure you're using Python 3.10 or higher:

```bash
python --version
```

If you want to use the word stemmer then run the following:
    
    cd tools/stemmer/
    ./make_english_stemmer.sh

### 3. Configure Django Settings

The project uses Django 4.2. If you need to customize settings, copy the template:

```bash
cp topicalguide/settings.py.template topicalguide/settings.py
```

Then edit `topicalguide/settings.py`:

1. Generate a `SECRET_KEY` at [django-secret-key-generator](http://www.miniwebtool.com/django-secret-key-generator/) and insert it
2. The default SQLite database configuration should work out of the box
3. For development, keep `DEBUG = True` (already set)
4. For production, set `DEBUG = False` and configure `ALLOWED_HOSTS`

**For most users, the existing `settings.py` file should work without modification.**

### 3a. Initialize the Database

Run Django migrations to set up the database:

```bash
python manage.py migrate
```

### 4. Import a Dataset

#### State of the Union Dataset (1790-2025)

The project includes a State of the Union addresses dataset spanning from 1790 to 2025.

**Option 1: Quick Import (recommended)**

```bash
python tg.py import default_datasets/state_of_the_union/ --identifier state_of_the_union --public --verbose
python tg.py analyze state_of_the_union --number-of-topics 20 --stopwords stopwords/english_all.txt --verbose
```

**Option 2: Using the provided script**

```bash
./default_datasets/import_state_of_the_union.sh
```

The project includes several stopword files in the `stopwords/` directory (`english_all.txt`, `english_mallet.txt`, `en.txt`) for filtering common words during topic modeling.

#### Updating the State of the Union Dataset

To download the most recent State of the Union addresses (2011-2025):

```bash
python download_sotu.py
```

This will fetch recent speeches from the American Presidency Project and save them in the proper format.

#### Custom Datasets

For more options on importing custom datasets:

```bash
python tg.py -h
```

### 5. Start the Web Server

Make sure your virtual environment is activated, then start the Django development server:

**Option 1: Direct start (output to console)**
```bash
python manage.py runserver
```

**Option 2: Start with logging (recommended for development)**
```bash
./start_server.sh
```

This starts the server with all output logged to `logs/server-YYYY-MM-DD_HH-MM-SS.log`. A symlink `logs/server-latest.log` always points to the most recent log. In another terminal, you can tail the log:

```bash
./tail_server_log.sh
# or
tail -f logs/server-latest.log
```

To stop a background server:
```bash
./stop_server.sh
```

Open a web browser and navigate to:

**http://localhost:8000/**

You should see the Topical Guide interface with your imported dataset(s).

### 6. (Optional) Generate LLM-Based Topic Names

For more intuitive topic names, you can use OpenAI's GPT models to automatically generate human-readable labels:

```bash
# Install OpenAI package
pip install openai

# Set your OpenAI API key
export OPENAI_API_KEY='your-api-key-here'

# Generate LLM-based topic names for your analysis
python generate_llm_topic_names.py state_of_the_union lda20topics
```

This will create topic names like "Military Operations and National Defense" instead of "war military troops".

**See [docs/LLM_TOPIC_NAMING.md](docs/LLM_TOPIC_NAMING.md) for detailed documentation, configuration options, and cost information.**

## POSTGRESQL

It can be tons faster to use postgres. Because it took me a bit of hunting to
get it to behave, here's how to do it on Fedora::

    sudo yum install postgres*
    sudo yum install python-psycopg2

    sudo systemctl enable postgresql.service
    sudo postgresql-setup initdb
    sudo -u postgres createdb topicalguide

In your settings.py you'll then need to switch DBTYPE to 'postgres' and
update the settings for the postgres database. For a local connection, we
prefer to use peer authentication, so we leave the user and password blank.
If you prefer to use md5 authentication, set the user and password
appropriately. Update the name field to 'topicalguide', or whatever you named
the database created for the topical guide.

Once the database is setup run the commands starting at step 4 with the prefix
`sudo -u postgres`.

## Apache

As an example, the following template apache configuration file could be 
filled in and placed in /etc/httpd/conf.d to run your server assuming your 
project is located at /srv/topicalguide::

    ServerAdmin your_admin_email@somewhere.com
    ServerName your.server.com
    ErrorLog /var/log/httpd/your-error_log
    CustomLog /var/log/httpd/your-access_log common
    LogLevel warn

    Alias /scripts /srv/topicalguide/topic_modeling/media/scripts/
    Alias /styles /srv/topicalguide/topic_modeling/media/styles/
    Alias /site-media /srv/topicalguide/topic_modeling/media
    <Directory "/srv/topicalguide/topic_modeling/media">
       Require all granted
    </Directory>

    WSGIApplicationGroup %{GLOBAL}
    WSGIScriptAlias / /srv/topicalguide/topic_modeling/apache/django.wsgi
    <Directory "/srv/topicalguide/topic_modeling/apache">
       Require all granted
    </Directory>

Note that the django.wsgi file we use is included in the repository.
Further information on setting up Django to run with Apache can be found
in the official Django documentation.

## Contributing

We welcome contributions to the code of this project. 
The best way to do so is to fork the code and then submit a [pull request](https://help.github.com/articles/using-pull-requests). 
For licensing purposes we ask that you assignthe copyright of any patch that you contribute to Brigham Young University.

## Citations

We also request that any published papers resulting from the use of this code
cite the following paper:

Matthew J. Gardner, Joshua Lutes, Jeff Lund, Josh Hansen, Dan Walker, Eric
Ringger, Kevin Seppi. "The Topic Browser: An Interactive Tool for Browsing
Topic Models".  In the Proceedings of the Workshop on Challenges of Data
Visualization, held in conjunction with the 24th Annual Conference on Neural
Information Processing Systems (NIPS 2010). December 11, 2010. Whistler, BC,
Canada.

## Licence

This file is part of the [Topical Guide](http://github.com/BYU-NLP-Lab/topicalguide/wiki).

The Topical Guide is free software: you can redistribute it and/or modify it
under the terms of the GNU Affero General Public License as published by the
Free Software Foundation, either version 3 of the License, or any later version.

The Topical Guide is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Affero General Public License
for more details.

You should have received a copy of the [GNU Affero General Public License](http://www.gnu.org/licenses/) along
with the Topical Guide.

If you have inquiries regarding any further use of the Topical Guide, please
contact:

    Copyright Licensing Office
    Brigham Young University
    3760 HBLL
    Provo, UT 84602
    Phone: (801) 422-9339 or (801) 422-3821
    Email: copyright@byu.edu

## Opportunities for Enhanced Topic Analysis

The Topical Guide provides a solid foundation for topic modeling with LDA and HLDA. Based on an audit of the current implementation, here are opportunities to enhance topic analysis capabilities:

### Modern Topic Modeling Approaches

**Neural Topic Models**
- ✅ **BERTopic**: **IMPLEMENTED** - Leverage transformer-based embeddings (BERT, RoBERTa) for context-aware topic extraction
  - Better handling of semantic relationships and polysemy
  - Improved topic coherence, especially for domain-specific terminology
  - Particularly valuable for State of the Union dataset with evolving political language
  - Uses sentence transformers → UMAP → HDBSCAN → c-TF-IDF pipeline
  - Automatic topic discovery (no need to specify topic count) or fixed topic count
  - **Embedding-based features**: Topic similarity metrics, interactive visualizations (see [docs/BERTOPIC_EMBEDDINGS.md](docs/BERTOPIC_EMBEDDINGS.md))
  - **Hierarchical topics**: Visualization available; full hierarchy navigation and data model integration pending
  - **Usage**: `python tg.py analyze state_of_the_union --analysis-tool BERTopic --number-of-topics 20 --stopwords stopwords/english_all.txt --verbose`
  - **Note**: Requires Python ≤3.13 due to dependency constraints (numba/hdbscan compatibility)
- **Top2Vec**: Simpler alternative to BERTopic for document/word embeddings
  - No need to specify number of topics in advance
  - Better captures semantic similarity
- **CTM (Contextualized Topic Models)**: Hybrid neural/topic model approach
  - Handles short texts better than traditional LDA
  - More robust to vocabulary changes over time

**Implementation Path**: Add new analysis interfaces in `import_tool/analysis/interfaces/` similar to `mallet_analysis.py`

### Temporal and Dynamic Analysis

**Dynamic Topic Models (DTM)**
- **Core Capability**: Track how topics evolve over time in the State of the Union dataset (1790-2025)
- **Key Features**:
  - Topic birth, evolution, and death across 235 years
  - Word probability changes within topics over time (e.g., "defense" terminology evolution)
  - Topic trajectory visualization (topic strength over decades)
  - Historical event correlation (wars, economic shifts, policy changes)
- **Implementation Options**:
  - Build on LDA using `gensim.models.ldaseqmodel` for DTM
  - Extend BERTopic with temporal binning (`topics_over_time()` method)
  - Custom temporal slicing with post-hoc analysis
- **Ideal Time Slices for SOTU**:
  - By decade (1790s, 1800s, ..., 2020s)
  - By presidential administration
  - By historical era (Revolutionary, Antebellum, Civil War, Gilded Age, etc.)
- **Visualizations Needed**:
  - Sankey diagrams for topic flow across time periods
  - River plots showing topic prevalence over time
  - Topic trajectory line charts
  - Era comparison heatmaps

**Topic Evolution Metrics**
- Topic stability over time windows
- Topic drift detection (gradual vs. sudden changes)
- Cross-administration topic comparison
- Crisis-correlated topic shifts (wars, depressions, pandemics)
- Policy topic emergence and decline patterns

**Implementation Path**: Extend `import_tool/metric/topic/` with temporal analysis modules; enhance `visualize/api.py` to support time-series queries; add new visualization components for temporal flows

**Unique Value for SOTU Dataset**: The 235-year span makes DTM particularly powerful for understanding American political discourse evolution, tracking topics like "national defense" from Revolutionary War → Cold War → War on Terror, or following the emergence of topics like civil rights, environmentalism, and technology policy.

### Advanced Coherence and Quality Metrics

**Beyond PMI Coherence**
- **C_v coherence**: Better correlates with human interpretability judgments
- **NPMI (Normalized PMI)**: Addresses PMI bias toward rare words
- **U_Mass coherence**: Uses document co-occurrence instead of sliding windows
- **Topic Diversity**: Measure uniqueness of words across topics (avoid redundant topics)
- **Topic Exclusivity**: Balance between topic coherence and topic distinctiveness

**Current State**: Basic PMI coherence implemented in `import_tool/metric/topic/coherence.py`

**Implementation Path**: Add new metric modules following the pattern in `import_tool/metric/topic/`

### Enhanced Topic Naming and Labeling

**Modern Labeling Approaches**
- ✅ **LLM-based topic labeling**: **IMPLEMENTED** - Use OpenAI GPT models to generate human-readable topic names from top words and example documents (see [LLM_TOPIC_NAMING.md](LLM_TOPIC_NAMING.md))
- **Named Entity Recognition (NER)**: Extract key entities (people, places, organizations) to enrich topic descriptions
- **Phrase extraction**: Use noun phrases instead of single words for more descriptive labels
- **Hierarchical labeling**: Multi-level topic descriptions (short label + detailed description)

**Current State**: Top-N, TF-ITF, and LLM-based naming implemented in `import_tool/analysis/name_schemes/`

**Implementation Path**: Extend `AbstractTopicNamer` with additional naming schemes; integrate NER or phrase extraction

### Visualization Enhancements

**Topic Embedding Visualizations**
- **t-SNE/UMAP**: 2D visualizations of topic relationships based on word distributions
- **Topic correlation networks**: Interactive graphs showing related topics
  - **Force View visualization**: Force-directed graph showing topic relationships based on distance metrics (document correlation, word correlation, embedding distance) - Currently disabled but implementation complete and audited; ready to re-enable
- **Temporal topic flows**: Sankey diagrams or river plots showing topic evolution
- **Topic-document heatmaps**: Visualize topic distributions across document collections

**Hierarchical Topic Improvements**
- Interactive tree visualization for HLDA results
- Dendrogram-based topic browsing
- Topic merging and splitting suggestions

**Implementation Path**: Extend frontend in `visualize/` directory; add JavaScript libraries for interactive visualizations

### Document-Level Improvements

**Advanced Document Analysis**
- **Document clustering**: Group documents by topic similarity beyond simple topic assignment
- **Topic threading**: Trace topic development across related documents (e.g., follow "healthcare" through multiple administrations)
- **Anomaly detection**: Identify documents with unusual topic distributions
- **Cross-reference analysis**: Find documents that bridge multiple topics

**Implementation Path**: Add to `import_tool/metric/document/` and enhance `visualize/models.py` Document methods

### Preprocessing Enhancements

**Text Processing**
- **Better bigram/trigram detection**: Use pointwise mutual information or log-likelihood ratios
- **Advanced stemming/lemmatization**: Integrate spaCy or NLTK's WordNet lemmatizer
- **Domain-specific stopwords**: Automatically identify and filter domain-specific common words
- **Rare word filtering**: More sophisticated frequency-based filtering
- **Spelling normalization**: Handle historical spelling variations in older State of the Union addresses

**Current State**: Basic bigram detection and Porter stemming in `mallet_analysis.py`

**Implementation Path**: Enhance `_prepare_analysis_input()` in `import_tool/analysis/interfaces/mallet_analysis.py`

### Model Diagnostics and Evaluation

**Model Quality Assessment**
- **Perplexity**: Measure how well the model predicts held-out documents
- **Topic stability**: Cross-validation to assess topic reproducibility
- **Optimal topic count selection**: Automated methods to determine ideal number of topics
- **Convergence diagnostics**: Track and visualize MALLET training convergence

**Comparative Analysis**
- Side-by-side comparison of different topic counts
- Compare LDA vs. HLDA results on same dataset
- A/B testing framework for preprocessing choices

**Implementation Path**: Add to `import_tool/metric/analysis/` for dataset-level metrics

### Interactive Topic Refinement

**User-Driven Improvements**
- **Topic merging**: Combine similar topics based on user judgment
- **Topic splitting**: Break overly broad topics into subtopics
- **Word inclusion/exclusion**: Manually adjust topic-word associations
- **Feedback loop**: Re-run analysis incorporating user corrections

**Implementation Path**: Add API endpoints in `visualize/api.py`; create admin interface

### Sentiment and Affect Analysis

**Emotion Detection**
- Sentiment analysis per topic (expand existing `sentiment.py`)
- Emotion classification (joy, anger, fear, etc.) for topic instances
- Tone analysis across presidential administrations
- Rhetorical device detection

**Implementation Path**: Enhance `import_tool/metric/topic/sentiment.py`; integrate sentiment lexicons or pre-trained models

### Multi-Modal and Cross-Lingual Extensions

**Language Support**
- Multi-language topic modeling for translated documents
- Cross-lingual topic alignment
- Language-specific preprocessing pipelines

**Multi-Modal Analysis**
- Integrate image analysis for documents with figures
- Audio/video transcript topic modeling
- Joint text-metadata modeling

### Performance and Scalability

**Optimization Opportunities**
- **Parallel processing**: Parallelize MALLET training and metric computation
- **Incremental updates**: Add new documents without full retraining
- **Caching strategies**: Cache frequently accessed topic-document matrices
- **Database optimization**: Index optimization for large-scale queries

**Current State**: Single-threaded MALLET execution

**Implementation Path**: Add multiprocessing to `import_tool/analysis/interfaces/`; optimize database queries in `visualize/models.py`

### Specific Recommendations for State of the Union Dataset

Given the 235-year temporal span (1790-2025):

1. **Historical language evolution**: Track vocabulary changes and topic shifts across centuries
2. **Presidential comparison**: Cluster presidents by topic emphasis
3. **Crisis detection**: Identify periods where topic distributions shift dramatically (wars, depressions, pandemics)
4. **Policy tracking**: Follow specific policy topics (taxation, immigration, healthcare) across time
5. **Rhetorical analysis**: Compare speaking styles and themes across different eras

### Implementation Priority Recommendations

**High Impact, Lower Effort**
1. Add C_v coherence metric
2. Improve topic naming with phrase extraction
3. Add temporal visualization (topic over time)
4. Implement topic diversity metrics

**High Impact, Higher Effort**
1. ~~Integrate BERTopic for neural topic modeling~~ ✅ **COMPLETED**
2. Build dynamic topic modeling (DTM) for temporal analysis
3. Create interactive topic evolution visualization
4. ~~Implement LLM-based topic labeling~~ ✅ **COMPLETED**

**Research-Oriented**
1. Develop comparative analysis framework
2. Build topic stability and reproducibility metrics
3. Create automated optimal topic count selection
4. Implement cross-lingual topic alignment

### Exploratory Data Analysis (EDA) Enhancements

The Topical Guide's core strength is facilitating exploratory data analysis of document collections. While BERTopic provides excellent visualizations, the Topical Guide adds value through persistent storage, multi-analysis comparison, and document-level exploration. However, several key EDA capabilities are missing:

**Document Search and Filtering**
- **Full-text search**: Search across all documents for keywords or phrases
- **Faceted browsing**: Filter documents by topic, year, metadata fields, or combinations
- **Advanced queries**: Boolean search, phrase matching, proximity search
- **Regex search**: Pattern-based document discovery
- **Export filtered sets**: Save/export document lists for further analysis

**Interactive Document Analysis**
- **Document comparison**: Side-by-side view of multiple documents
- **Similar document finder**: Use embeddings or topic distributions to find related documents
- **Outlier detection**: Identify documents with unusual topic distributions
- **Document clustering**: Group documents beyond simple topic assignment
- **Topic threading**: Trace how topics develop across related documents

**Statistical Summaries and Overviews**
- **Corpus statistics**: Document count by year, average document length, vocabulary size
- **Topic distribution summaries**: Documents per topic, topic concentration metrics
- **Temporal patterns**: Documents and topics over time periods
- **Coverage analysis**: Which documents/time periods are well-covered by topics?
- **Data quality metrics**: Missing metadata, outlier documents, coverage gaps

**Enhanced Filtering and Facets**
- **Year range slider**: Filter documents by date range
- **Topic filters**: Show only documents with specific topics above threshold
- **Metadata facets**: Filter by president, party, event type, custom fields
- **Combinatorial filters**: AND/OR logic for complex queries
- **Filter persistence**: Save and share filter configurations

**Document-Centric Views**
- **Document cards**: Rich preview with metadata, topics, and text snippet
- **Document timelines**: Chronological visualization of documents
- **Document networks**: Visualize document relationships based on topic similarity
- **Reading list**: Curate and annotate collections of documents for analysis
- **Annotation support**: Add notes and tags to documents

**Comparative Analysis Tools**
- **Compare topic models**: Side-by-side comparison of different analyses on same dataset
- **Compare time periods**: Contrast document collections from different eras
- **Compare document subsets**: Analyze differences between filtered document sets
- **Metric comparison**: Compare documents using different similarity measures

**Export and Integration**
- **CSV export**: Export filtered document lists with metadata and topic scores
- **JSON API**: Programmatic access to filtered documents
- **Citation export**: Export document references in standard formats
- **Analysis export**: Save complete analysis state for reproduction

**Implementation Priority for EDA**

**Quick Wins (High Value, Lower Effort)**
1. Add full-text search to document browser
2. Implement basic year range filtering
3. Add "find similar documents" using existing topic distributions
4. Create document count summaries by year/topic

**Medium Effort**
1. Build faceted filtering UI (year + topic + metadata)
2. Implement document comparison view
3. Add CSV export for filtered document lists
4. Create statistical summary dashboard

**Higher Effort**
1. Implement embedding-based document similarity (requires storing document embeddings)
2. Build document network visualization
3. Create advanced query builder with Boolean logic
4. Implement document clustering beyond topic assignments

**Why This Matters for EDA**

These features address the core EDA workflow:
1. **Discover**: Find interesting documents through search and filtering
2. **Explore**: Navigate related documents and understand patterns
3. **Compare**: Contrast different document sets or time periods
4. **Validate**: Check that topics capture meaningful document groupings
5. **Export**: Take findings to other tools for deeper analysis

This differentiates the Topical Guide from BERTopic (which focuses on topic-level visualization) by emphasizing **document-level exploration and discovery**.

### Contributing

We welcome contributions in any of these areas. For major enhancements, please open an issue first to discuss the approach. See the Contributing section above for details on submitting pull requests.
