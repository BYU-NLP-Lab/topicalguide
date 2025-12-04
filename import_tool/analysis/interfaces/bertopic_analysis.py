import io
import json
import os
import pickle
import re
from os.path import join, abspath
from import_tool import basic_tools
from import_tool.import_system_utilities import TOKEN_REGEX
from .abstract_analysis import AbstractAnalysis


class BertopicAnalysis(AbstractAnalysis):
    """
    BERTopic-based topic modeling using transformer embeddings.

    BERTopic uses sentence transformers to create embeddings, UMAP for
    dimensionality reduction, and HDBSCAN for clustering. It can automatically
    determine the optimal number of topics or use a fixed number.
    """

    def __init__(self, mallet_path, dataset_dir, base_dir):
        """
        Initialize BERTopic analysis.

        Args:
            mallet_path: Unused (for compatibility with tg.py interface)
            dataset_dir: Directory where analysis subdirectory will be created
            base_dir: Base directory of the project
        """
        # mallet_path is ignored - BERTopic doesn't use MALLET
        self.dataset_dir = dataset_dir
        self.base_dir = base_dir

        self.metadata = {}
        self.stopwords = {}
        self._excluded_words = {}

        # Set defaults
        self._embedding_model = "all-MiniLM-L6-v2"  # Fast, good quality
        self._min_topic_size = 3  # Minimum cluster size for topics
        self._nr_topics = None  # Auto-determine by default
        self._calculate_probabilities = True

        self._set_names_and_description()
        self.token_regex = TOKEN_REGEX

        # Preprocessing flags (mostly unused for BERTopic but required by interface)
        self.remove_singletons = False
        self.find_bigrams = False
        self.stem_words = False

        # Will store the trained model
        self._model = None
        self._topics = None
        self._probs = None
        self._documents = None
        self._doc_indices = None

        # Subdocument support
        self.create_subdocuments_method = None

    def _set_names_and_description(self):
        """Set the analysis name and description."""
        if self._nr_topics:
            self.name = f'bertopic{self._nr_topics}topics'
            self.readable_name = f'BERTopic with {self._nr_topics} Topics'
            self.description = f'BERTopic analysis with {self._nr_topics} topics using {self._embedding_model} embeddings.'
        else:
            self.name = 'bertopicauto'
            self.readable_name = 'BERTopic (Auto Topics)'
            self.description = f'BERTopic analysis with automatic topic discovery using {self._embedding_model} embeddings.'

    @property
    def metadata_types(self):
        result = {}
        basic_tools.collect_types(result, self.metadata)
        return result

    @property
    def name(self):
        """Get the name."""
        return self._name

    @name.setter
    def name(self, name):
        """Set identifier and corresponding working directory."""
        self._name = name
        self.working_directory = abspath(join(self.dataset_dir, 'analyses/' + self.name))

    @property
    def readable_name(self):
        return self.metadata.setdefault('readable_name', self.name)

    @readable_name.setter
    def readable_name(self, readable_name):
        self.metadata['readable_name'] = readable_name

    @property
    def description(self):
        return self.metadata['description']

    @description.setter
    def description(self, description):
        self.metadata['description'] = description

    @property
    def embedding_model(self):
        """Get the sentence transformer model name."""
        return self._embedding_model

    @embedding_model.setter
    def embedding_model(self, model_name):
        """Set the sentence transformer model."""
        self._embedding_model = model_name
        self.metadata['embedding_model'] = model_name
        self._set_names_and_description()

    @property
    def min_topic_size(self):
        """Minimum size of topics."""
        return self._min_topic_size

    @min_topic_size.setter
    def min_topic_size(self, size):
        self._min_topic_size = size
        self.metadata['min_topic_size'] = size

    @property
    def nr_topics(self):
        """Number of topics (None for auto-discovery)."""
        return self._nr_topics

    @nr_topics.setter
    def nr_topics(self, num):
        """Set number of topics (None for automatic)."""
        self._nr_topics = num
        if num is not None:
            self.metadata['nr_topics'] = num
        self._set_names_and_description()

    @property
    def num_topics(self):
        """Alias for nr_topics (for compatibility with tg.py)."""
        return self._nr_topics

    @num_topics.setter
    def num_topics(self, num):
        """Alias for nr_topics setter (for compatibility with tg.py).

        Special handling: if num <= 0, use auto-discovery (nr_topics = None).
        """
        if num <= 0:
            self.nr_topics = None
        else:
            self.nr_topics = num

    @property
    def working_directory(self):
        return self._working_dir

    @working_directory.setter
    def working_directory(self, working_dir):
        """Set the working directory and create necessary file paths."""
        self._working_dir = abspath(working_dir)
        if not os.path.exists(self._working_dir):
            os.makedirs(self._working_dir)

        # Define file paths
        self.model_file = join(self._working_dir, 'bertopic_model.pkl')
        self.documents_file = join(self._working_dir, 'documents.json')
        self.topics_file = join(self._working_dir, 'topics.json')
        self.probs_file = join(self._working_dir, 'probabilities.json')
        self.vocab_file = join(self._working_dir, 'vocabulary.json')
        self.token_assignments_file = join(self._working_dir, 'token_assignments.json')
        self.topic_embeddings_file = join(self._working_dir, 'topic_embeddings.json')
        self.hierarchy_file = join(self._working_dir, 'hierarchy.json')

        # Additional files for BERTopic visualizations
        self.documents_txt_file = join(self._working_dir, 'documents.txt')
        self.timestamps_file = join(self._working_dir, 'timestamps.txt')
        self.classes_file = join(self._working_dir, 'classes.txt')

    @property
    def token_regex(self):
        return self._token_regex

    @token_regex.setter
    def token_regex(self, regex):
        self._token_regex = regex
        self._compiled_regex = re.compile(regex, re.UNICODE)
        self.metadata['token_regex'] = regex

    @property
    def excluded_words(self):
        return self._excluded_words

    @excluded_words.setter
    def excluded_words(self, words_dict):
        self._excluded_words = words_dict

    def tokenize(self, text):
        """
        Tokenize text using the configured regex.
        Returns list of (token, start_position) tuples.
        """
        tokens = []
        for match in self._compiled_regex.finditer(text):
            wordtype = match.group().lower()
            if wordtype not in self.stopwords:
                tokens.append((wordtype, match.start()))
        return tokens

    def add_stopwords_file(self, filepath):
        """Load stopwords from file."""
        with io.open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            for token, __ in self.tokenize(f.read()):
                self.stopwords[token] = True

    def set_create_subdocuments_method(self, method):
        """
        Set the method for creating subdocuments.
        This allows analyzing paragraphs instead of full documents.
        """
        self.create_subdocuments_method = method

    def create_subdocuments(self, name, content):
        """
        Create subdocuments from a document.
        If no subdocument method is set, returns the full document.
        """
        if self.create_subdocuments_method:
            return self.create_subdocuments_method(str(name), content)
        else:
            return [(name, content)]

    def run_analysis(self, documents):
        """
        Run BERTopic analysis on the documents.

        Args:
            documents: Iterator over document objects with get_content() method
        """
        if documents.count() == 0:
            raise Exception('No documents to perform analysis on.')

        print("Preparing documents for BERTopic...")

        # Extract document texts and track indices
        # If using subdocuments, split each document into chunks
        doc_texts = []
        doc_indices = []
        doc_timestamps = []
        doc_classes = []

        for doc_index, doc in enumerate(documents):
            content = doc.get_content()
            subdocuments = self.create_subdocuments(doc_index, content)

            # Try to extract metadata for visualizations
            timestamp = None
            doc_class = None

            # Get metadata from document (using Django model method)
            try:
                metadata = doc.get_metadata()

                # Check for temporal metadata (year, date, etc.)
                for key in ['year', 'date', 'timestamp', 'time', 'published_date']:
                    if key in metadata and metadata[key]:
                        timestamp = str(metadata[key])
                        break

                # Check for class/category metadata
                for key in ['class', 'category', 'label', 'type', 'author', 'author_name', 'president_name', 'source']:
                    if key in metadata and metadata[key]:
                        doc_class = str(metadata[key])
                        break
            except Exception as e:
                # If metadata extraction fails, continue without it
                pass

            for subdoc_name, subdoc_content in subdocuments:
                doc_texts.append(subdoc_content)
                doc_indices.append(doc_index)  # Track original document index
                doc_timestamps.append(timestamp)
                doc_classes.append(doc_class)

        if self.create_subdocuments_method:
            print(f"Loaded {len(documents)} documents, split into {len(doc_texts)} subdocuments")
        else:
            print(f"Loaded {len(doc_texts)} documents")

        # Save documents for later retrieval
        with io.open(self.documents_file, 'w', encoding='utf-8') as f:
            json.dump({'texts': doc_texts, 'indices': doc_indices}, f)

        try:
            from bertopic import BERTopic
            from sentence_transformers import SentenceTransformer
        except ImportError:
            raise ImportError(
                "BERTopic dependencies not installed. "
                "Install with: pip install bertopic sentence-transformers umap-learn hdbscan"
            )

        print(f"Initializing BERTopic with embedding model: {self._embedding_model}")

        # Initialize BERTopic model
        topic_model = BERTopic(
            embedding_model=self._embedding_model,
            min_topic_size=self._min_topic_size,
            nr_topics=self._nr_topics,
            calculate_probabilities=self._calculate_probabilities,
            verbose=True
        )

        print("Training BERTopic model...")

        # Fit the model
        topics, probs = topic_model.fit_transform(doc_texts)

        # Store model and results
        self._model = topic_model
        self._topics = topics
        self._probs = probs
        self._documents = doc_texts
        self._doc_indices = doc_indices

        print(f"BERTopic found {len(set(topics))} topics (including outliers)")

        # Save the model
        print("Saving BERTopic model...")
        with open(self.model_file, 'wb') as f:
            pickle.dump(topic_model, f)

        # Save topic assignments
        with io.open(self.topics_file, 'w', encoding='utf-8') as f:
            json.dump(topics, f)

        # Save probabilities
        if probs is not None:
            with io.open(self.probs_file, 'w', encoding='utf-8') as f:
                json.dump(probs.tolist(), f)

        # Save topic embeddings
        self._save_topic_embeddings(topic_model)

        # Compute and save hierarchical topic structure
        self._save_hierarchy(topic_model, doc_texts)

        # Extract and save vocabulary
        self._extract_vocabulary()

        # Create token-to-topic assignments for compatibility
        self._create_token_assignments()

        # Save additional files for BERTopic native visualizations
        self._save_visualization_files(doc_texts, doc_timestamps, doc_classes)

        print("BERTopic analysis complete!")

    def _save_visualization_files(self, doc_texts, doc_timestamps, doc_classes):
        """
        Save additional files needed for BERTopic native visualizations.

        Args:
            doc_texts: List of document text strings
            doc_timestamps: List of timestamps (may contain None values)
            doc_classes: List of class labels (may contain None values)
        """
        # Save documents.txt for Documents Map and Hierarchical Documents visualizations
        print("Saving documents.txt for visualizations...")
        with io.open(self.documents_txt_file, 'w', encoding='utf-8') as f:
            for text in doc_texts:
                # Write each document on a single line, escaping newlines
                f.write(text.replace('\n', ' ').replace('\r', ' ') + '\n')

        # Save timestamps.txt if temporal data is available
        if any(ts is not None for ts in doc_timestamps):
            print("Saving timestamps.txt for Topics Over Time visualization...")
            with io.open(self.timestamps_file, 'w', encoding='utf-8') as f:
                for timestamp in doc_timestamps:
                    # Write timestamp or empty line if None
                    f.write(str(timestamp) if timestamp is not None else '' + '\n')
            print(f"  Found temporal data for {sum(1 for ts in doc_timestamps if ts is not None)} documents")
        else:
            print("No temporal metadata found - skipping timestamps.txt")

        # Save classes.txt if class labels are available
        if any(cls is not None for cls in doc_classes):
            print("Saving classes.txt for Topics Per Class visualization...")
            with io.open(self.classes_file, 'w', encoding='utf-8') as f:
                for doc_class in doc_classes:
                    # Write class or empty line if None
                    f.write(str(doc_class) if doc_class is not None else '' + '\n')
            print(f"  Found class labels for {sum(1 for cls in doc_classes if cls is not None)} documents")
        else:
            print("No class/category metadata found - skipping classes.txt")

    def _save_topic_embeddings(self, topic_model):
        """
        Save topic embeddings for visualization and similarity calculations.

        BERTopic's topic_embeddings_ attribute contains the centroid embeddings
        for each topic in the embedding space.
        """
        if not hasattr(topic_model, 'topic_embeddings_') or topic_model.topic_embeddings_ is None:
            print("Warning: No topic embeddings found in model")
            return

        # topic_embeddings_ is a numpy array of shape (n_topics, embedding_dim)
        # Convert to list for JSON serialization
        import numpy as np

        embeddings_dict = {}
        topic_info = topic_model.get_topic_info()

        for idx, topic_id in enumerate(topic_info['Topic']):
            if topic_id != -1:  # Skip outlier topic
                embedding = topic_model.topic_embeddings_[idx].tolist()
                embeddings_dict[str(topic_id)] = embedding

        print(f"Saving embeddings for {len(embeddings_dict)} topics...")
        with io.open(self.topic_embeddings_file, 'w', encoding='utf-8') as f:
            json.dump(embeddings_dict, f)

    def _save_hierarchy(self, topic_model, doc_texts):
        """
        Compute and save the hierarchical topic structure.

        BERTopic's hierarchical_topics() performs agglomerative clustering on topics
        based on their c-TF-IDF representations, creating a dendrogram showing which
        topics are most similar and how they merge.

        Args:
            topic_model: Trained BERTopic model
            doc_texts: List of document texts
        """
        print("Computing hierarchical topic structure...")

        # Get the hierarchical topics DataFrame
        # This performs agglomerative clustering on the topics
        hierarchical_topics = topic_model.hierarchical_topics(doc_texts)

        # The DataFrame has columns: Parent_ID, Parent_Name, Topics,
        # Child_Left_ID, Child_Left_Name, Child_Right_ID, Child_Right_Name, Distance

        # Convert DataFrame to a list of dictionaries for JSON serialization
        hierarchy_data = {
            'merges': hierarchical_topics.to_dict('records'),
            'num_topics': len(topic_model.get_topic_freq()) - 1  # Exclude outlier topic (-1)
        }

        # Save the full hierarchy data
        with io.open(self.hierarchy_file, 'w', encoding='utf-8') as f:
            json.dump(hierarchy_data, f, indent=2)

        print(f"Saved hierarchical structure with {len(hierarchical_topics)} merge steps")

    def _extract_vocabulary(self):
        """Extract vocabulary from all documents."""
        vocab = set()

        # Extract all unique tokens from all documents
        # (not just topic representation words)
        for text in self._documents:
            tokens = self.tokenize(text)
            for token, _ in tokens:
                vocab.add(token)

        # Save vocabulary
        with io.open(self.vocab_file, 'w', encoding='utf-8') as f:
            json.dump(list(vocab), f)

    def _create_token_assignments(self):
        """
        Create token-level topic assignments for compatibility with Topical Guide.

        Since BERTopic works at document level, we assign all tokens in a document
        to that document's topic(s).
        """
        token_assignments = []

        for doc_idx, (text, topic_id) in enumerate(zip(self._documents, self._topics)):
            tokens = self.tokenize(text)

            for token, start_pos in tokens:
                # Each token gets assigned to the document's topic
                assignment = {
                    'doc_index': self._doc_indices[doc_idx],
                    'start_index': start_pos,
                    'token': token,
                    'token_abstraction': token,  # No stemming by default
                    'topics': [topic_id] if topic_id != -1 else []  # Skip outliers
                }
                token_assignments.append(assignment)

        # Save token assignments
        with io.open(self.token_assignments_file, 'w', encoding='utf-8') as f:
            json.dump(token_assignments, f)

    def get_vocab_iterator(self):
        """Return iterator over vocabulary."""
        with io.open(self.vocab_file, 'r', encoding='utf-8') as f:
            vocab_list = json.load(f)
        return {word: True for word in vocab_list}

    def get_token_iterator(self):
        """
        Return iterator over tokens with topic assignments.

        Yields: (document_index, start_index, token, token_abstraction, topic_list)
        """
        with io.open(self.token_assignments_file, 'r', encoding='utf-8') as f:
            assignments = json.load(f)

        for assignment in assignments:
            yield (
                assignment['doc_index'],
                assignment['start_index'],
                assignment['token'],
                assignment['token_abstraction'],
                tuple(assignment['topics'])
            )

    def get_hierarchy_iterator(self):
        """
        Return topic hierarchy as an iterator of (parent_topic, child_topic) tuples.

        BERTopic's hierarchical clustering creates a dendrogram with synthetic parent
        nodes that don't correspond to real topics. The hierarchy information is saved
        in hierarchy.json and can be used directly to find related topics based on
        merge distances, without needing to store parent-child relationships in the
        database Topic.parent field.

        Returns:
            list: Empty list - BERTopic hierarchy is stored in hierarchy.json instead
        """
        # BERTopic's hierarchical_topics() creates synthetic parent topic IDs that
        # don't exist in the actual topic list. For example, with topics 0-19, the
        # hierarchy creates parent IDs like 20, 21, 22, etc. representing merged
        # clusters. These don't map well to the Topic.parent field which expects
        # all nodes to be real topics.
        #
        # Instead, the hierarchy.json file contains the full dendrogram with merge
        # distances, which can be used to find related topics more accurately.
        return []
