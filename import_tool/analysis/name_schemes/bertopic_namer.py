import os
import pickle
from .abstract_topic_namer import AbstractTopicNamer


class BertopicNamer(AbstractTopicNamer):
    """
    Use BERTopic's built-in c-TF-IDF topic representations for naming.

    BERTopic uses class-based TF-IDF to find words that are distinctive
    to each topic, which often produces better topic labels than simple
    frequency-based approaches.
    """

    def __init__(self, n=5):
        """
        Initialize BERTopic namer.

        Args:
            n: Number of top words to use in topic name (default: 5)
        """
        self.n = n

    @property
    def name_scheme(self):
        return f"BERTopic c-TF-IDF Top {self.n}"

    def name_topics(self, database_id, analysis_db):
        """
        Name topics using BERTopic's c-TF-IDF representations.

        This only works for BERTopic analyses. For other analysis types,
        it returns empty names.
        """
        # Check if this is a BERTopic analysis by looking for the model file
        dataset_dir = analysis_db.dataset.dataset_dir
        analysis_name = analysis_db.name
        model_path = os.path.join(dataset_dir, 'analyses', analysis_name, 'bertopic_model.pkl')

        if not os.path.exists(model_path):
            # Not a BERTopic analysis, return empty names
            return {}

        # Load the BERTopic model
        try:
            with open(model_path, 'rb') as f:
                model = pickle.load(f)
        except Exception as e:
            print(f"Warning: Could not load BERTopic model: {e}")
            return {}

        # Extract topic names from BERTopic's c-TF-IDF representations
        topic_names = {}
        for topic_db in analysis_db.topics.all():
            topic_num = topic_db.number

            # Get BERTopic's representation for this topic
            topic_words = model.get_topic(topic_num)

            if topic_words and len(topic_words) > 0:
                # Take top N words from c-TF-IDF representation
                top_words = [word for word, score in topic_words[:self.n]]
                name = ' '.join(top_words)
                topic_names[topic_num] = name
            else:
                # Fallback for topics without representation
                topic_names[topic_num] = f"Topic {topic_num}"

        return topic_names
