#!/usr/bin/env python
"""
Extract topic embeddings from existing BERTopic models and save them.
"""

import os
import sys
import json
import io
import pickle

sys.path.append(os.curdir)
os.environ['DJANGO_SETTINGS_MODULE'] = 'topicalguide.settings'

import django
django.setup()

from visualize.models import Analysis, Dataset

def extract_embeddings_for_analysis(analysis_name, dataset_name='state_of_the_union'):
    """Extract and save embeddings from a BERTopic model."""

    # Get the analysis
    analysis = Analysis.objects.get(dataset__name=dataset_name, name=analysis_name)

    # Path to the model file
    model_file = os.path.join(
        analysis.dataset.dataset_dir,
        'analyses',
        analysis.name,
        'bertopic_model.pkl'
    )

    if not os.path.exists(model_file):
        print(f"Model file not found: {model_file}")
        return False

    print(f"Loading BERTopic model from {model_file}...")
    with open(model_file, 'rb') as f:
        topic_model = pickle.load(f)

    # Check if the model has embeddings
    if not hasattr(topic_model, 'topic_embeddings_') or topic_model.topic_embeddings_ is None:
        print("Warning: No topic embeddings found in model")
        return False

    # Extract embeddings
    embeddings_dict = {}
    topic_info = topic_model.get_topic_info()

    for idx, topic_id in enumerate(topic_info['Topic']):
        if topic_id != -1:  # Skip outlier topic
            embedding = topic_model.topic_embeddings_[idx].tolist()
            embeddings_dict[str(topic_id)] = embedding

    # Save embeddings
    embeddings_file = os.path.join(
        analysis.dataset.dataset_dir,
        'analyses',
        analysis.name,
        'topic_embeddings.json'
    )

    print(f"Saving embeddings for {len(embeddings_dict)} topics to {embeddings_file}...")
    with io.open(embeddings_file, 'w', encoding='utf-8') as f:
        json.dump(embeddings_dict, f)

    print(f"✓ Successfully extracted embeddings for {analysis_name}")
    return True


if __name__ == '__main__':
    # Extract embeddings for both BERTopic analyses
    for analysis_name in ['bertopicauto', 'bertopic50topics']:
        print(f"\n{'='*60}")
        print(f"Processing {analysis_name}")
        print('='*60)
        extract_embeddings_for_analysis(analysis_name)
