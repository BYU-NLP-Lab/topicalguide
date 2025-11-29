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

```bash
python manage.py runserver
```

Open a web browser and navigate to:

**http://localhost:8000/**

You should see the Topical Guide interface with your imported dataset(s).

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
- **BERTopic**: Leverage transformer-based embeddings (BERT, RoBERTa) for context-aware topic extraction
  - Better handling of semantic relationships and polysemy
  - Improved topic coherence, especially for domain-specific terminology
  - Particularly valuable for State of the Union dataset with evolving political language
- **Top2Vec**: Combines document and word embeddings for automatic topic discovery
  - No need to specify number of topics in advance
  - Better captures semantic similarity
- **CTM (Contextualized Topic Models)**: Combines neural language models with topic modeling
  - Handles short texts better than traditional LDA
  - More robust to vocabulary changes over time

**Implementation Path**: Add new analysis interfaces in `import_tool/analysis/interfaces/` similar to `mallet_analysis.py`

### Temporal and Dynamic Analysis

**Dynamic Topic Modeling**
- Track topic evolution across time periods in the State of the Union dataset (1790-2025)
- Identify emerging topics, declining topics, and persistent themes
- Visualize topic trajectories over 235 years of presidential addresses
- Detect topic "birth" and "death" events correlated with historical periods

**Topic Evolution Metrics**
- Topic stability over time windows
- Topic drift detection (gradual vs. sudden changes)
- Cross-administration topic comparison
- Era-specific topic clustering (Revolutionary, Civil War, Industrial, Modern, etc.)

**Implementation Path**: Extend `import_tool/metric/topic/` with temporal analysis modules; enhance `visualize/api.py` to support time-series queries

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
- **LLM-based topic labeling**: Use GPT/Claude to generate human-readable topic names from top words and example documents
- **Named Entity Recognition (NER)**: Extract key entities (people, places, organizations) to enrich topic descriptions
- **Phrase extraction**: Use noun phrases instead of single words for more descriptive labels
- **Hierarchical labeling**: Multi-level topic descriptions (short label + detailed description)

**Current State**: Simple Top-N and TF-ITF naming in `import_tool/analysis/name_schemes/`

**Implementation Path**: Extend `AbstractTopicNamer` with new naming schemes; integrate with external APIs or local NER models

### Visualization Enhancements

**Topic Embedding Visualizations**
- **t-SNE/UMAP**: 2D visualizations of topic relationships based on word distributions
- **Topic correlation networks**: Interactive graphs showing related topics
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
1. Integrate BERTopic or similar neural approach
2. Build dynamic topic modeling for temporal analysis
3. Create interactive topic evolution visualization
4. Implement LLM-based topic labeling

**Research-Oriented**
1. Develop comparative analysis framework
2. Build topic stability and reproducibility metrics
3. Create automated optimal topic count selection
4. Implement cross-lingual topic alignment

### Contributing

We welcome contributions in any of these areas. For major enhancements, please open an issue first to discuss the approach. See the Contributing section above for details on submitting pull requests.
