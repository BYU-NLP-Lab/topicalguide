"""
LLM-based topic naming using OpenAI API.

This module provides topic naming using Large Language Models (LLMs) to generate
human-readable, interpretable topic names from topic word distributions and
optionally sample documents.
"""

import os
import json
from django.db.models import Count
from .abstract_topic_namer import AbstractTopicNamer
from visualize.models import TopicNameScheme, TopicName


class LLMTopicNamer(AbstractTopicNamer):
    """
    Generate topic names using OpenAI API.

    This namer uses GPT models to analyze the top words in a topic and optionally
    sample documents to generate concise, human-readable topic names.

    Args:
        n_words (int): Number of top words to include in the prompt (default: 10)
        n_docs (int): Number of sample documents to include (default: 3, 0 to disable)
        model (str): OpenAI model to use (default: gpt-4o-mini)
        api_key (str): OpenAI API key (default: from OPENAI_API_KEY env var)
        max_label_length (int): Maximum length for generated labels (default: 50)
        fallback_to_topn (bool): If True, fall back to Top-N naming on API errors (default: True)
    """

    def __init__(self, n_words=10, n_docs=3, model="gpt-4o-mini",
                 api_key=None, max_label_length=50, fallback_to_topn=True):
        self.n_words = n_words
        self.n_docs = n_docs
        self.model = model
        self.api_key = api_key or os.environ.get('OPENAI_API_KEY')
        self.max_label_length = max_label_length
        self.fallback_to_topn = fallback_to_topn

        # Check if API key is available
        if not self.api_key:
            raise ValueError(
                "OpenAI API key not found. Set OPENAI_API_KEY environment variable "
                "or pass api_key parameter."
            )

    @property
    def name_scheme(self):
        """Return the name of this naming scheme."""
        return f"LLM-{self.n_words}words"

    def name_topics(self, database_id, analysis_db):
        """
        Name all topics in the analysis using OpenAI API.

        Args:
            database_id: Database identifier for Django
            analysis_db: Analysis Django database object

        Returns:
            dict: Mapping of topic_number -> topic_name
        """
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError(
                "openai package not found. Install it with: pip install openai"
            )

        client = OpenAI(api_key=self.api_key)

        analysis_db.topics.prefetch_related('tokens')
        topic_names = {}

        for topic_db in analysis_db.topics.all():
            try:
                name = self._name_single_topic(client, topic_db, analysis_db)
                topic_names[topic_db.number] = name
            except Exception as e:
                print(f"Error naming topic {topic_db.number}: {e}")
                if self.fallback_to_topn:
                    # Fallback to simple Top-N naming
                    name = self._fallback_name(topic_db)
                    topic_names[topic_db.number] = name
                else:
                    raise

        return topic_names

    def _name_single_topic(self, client, topic_db, analysis_db):
        """
        Generate a name for a single topic using OpenAI API.

        Args:
            client: OpenAI API client
            topic_db: Topic Django database object
            analysis_db: Analysis Django database object

        Returns:
            str: Generated topic name
        """
        # Get top N words for this topic
        top_words_dict = topic_db.top_n_words(words='*', top_n=self.n_words)
        top_words = list(top_words_dict.keys())

        # Build the prompt
        prompt = self._build_prompt(top_words, topic_db, analysis_db)

        # Call OpenAI API
        response = client.chat.completions.create(
            model=self.model,
            max_tokens=100,
            temperature=0.3,  # Lower temperature for more consistent naming
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant that generates concise topic names for topic models."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        # Extract the topic name from the response
        topic_name = response.choices[0].message.content.strip()

        # Ensure it's not too long
        if len(topic_name) > self.max_label_length:
            topic_name = topic_name[:self.max_label_length].rsplit(' ', 1)[0]

        # Remove quotes if present
        topic_name = topic_name.strip('"').strip("'")

        return topic_name

    def _build_prompt(self, top_words, topic_db, analysis_db):
        """
        Build the prompt for the LLM to generate a topic name.

        Args:
            top_words: List of top words in the topic
            topic_db: Topic Django database object
            analysis_db: Analysis Django database object

        Returns:
            str: Prompt for the LLM
        """
        prompt_parts = [
            "You are analyzing topics from a topic model. Your task is to generate a concise, "
            "human-readable name for a topic based on its most frequent words.",
            "",
            f"Top words in this topic: {', '.join(top_words)}",
        ]

        # Optionally include sample documents
        if self.n_docs > 0:
            sample_docs = self._get_sample_documents(topic_db, analysis_db)
            if sample_docs:
                prompt_parts.append("")
                prompt_parts.append("Sample document excerpts containing this topic:")
                for i, doc_text in enumerate(sample_docs, 1):
                    prompt_parts.append(f"{i}. {doc_text}")

        prompt_parts.extend([
            "",
            f"Generate a concise topic name (maximum {self.max_label_length} characters) that captures "
            "the main theme. The name should be:",
            "- Clear and descriptive",
            "- Useful for human interpretation",
            "- Focused on the core concept",
            "- Professional and neutral in tone",
            "",
            "Respond with ONLY the topic name, nothing else."
        ])

        return "\n".join(prompt_parts)

    def _get_sample_documents(self, topic_db, analysis_db):
        """
        Get sample document excerpts for this topic.

        Args:
            topic_db: Topic Django database object
            analysis_db: Analysis Django database object

        Returns:
            list: List of document text excerpts
        """
        # Get top documents for this topic
        top_docs_dict = topic_db.top_n_documents(documents='*', top_n=self.n_docs)

        sample_texts = []
        for doc_filename in list(top_docs_dict.keys())[:self.n_docs]:
            try:
                doc = analysis_db.dataset.documents.get(filename=doc_filename)
                content = doc.get_content()

                # Get a reasonable excerpt (first 200 characters)
                excerpt = content[:200].strip()
                if len(content) > 200:
                    excerpt += "..."

                sample_texts.append(excerpt)
            except Exception as e:
                print(f"Warning: Could not retrieve document {doc_filename}: {e}")
                continue

        return sample_texts

    def _fallback_name(self, topic_db):
        """
        Generate a simple fallback name using Top-N words.

        Args:
            topic_db: Topic Django database object

        Returns:
            str: Simple topic name from top words
        """
        top_n_items = topic_db.tokens.values("word_type__word")\
                      .annotate(count=Count("word_type__word"))\
                      .order_by('-count')[:3]
        return ' '.join(str(x['word_type__word']) for x in top_n_items)
