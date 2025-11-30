"""
Embedding Distance - Pairwise metric for BERTopic analyses

Computes cosine distance between topic embeddings in the semantic space.
Only applicable to BERTopic analyses that have topic embeddings.
"""

import os
import json
import io
import math

metric_name = "Embedding Distance"


def cosine_distance(vec1, vec2):
    """
    Compute cosine distance between two vectors.

    Returns a value between 0 (identical) and 2 (opposite).
    Cosine distance = 1 - cosine similarity
    """
    # Compute dot product
    dot_product = sum(a * b for a, b in zip(vec1, vec2))

    # Compute magnitudes
    mag1 = math.sqrt(sum(a * a for a in vec1))
    mag2 = math.sqrt(sum(b * b for b in vec2))

    if mag1 == 0 or mag2 == 0:
        return 1.0  # Undefined, return neutral value

    # Cosine similarity
    cosine_sim = dot_product / (mag1 * mag2)

    # Cosine distance
    return 1.0 - cosine_sim


def compute_metric(database_id, dataset_db, analysis_db):
    """
    Compute embedding distance metric for all pairs of topics in a BERTopic analysis.

    This function yields pairwise distance values between topic embeddings.
    Only applicable to BERTopic analyses that have topic embeddings.

    Args:
        database_id: Database identifier
        dataset_db: Dataset model object
        analysis_db: Analysis model object

    Yields:
        dict: Dictionary with 'origin_topic_id', 'ending_topic_id', and 'value' keys
    """
    # Check if this is a BERTopic analysis
    if not analysis_db.name.startswith('bertopic'):
        print(f"Skipping {analysis_db.name} - not a BERTopic analysis")
        return

    # Load topic embeddings
    embeddings_file = os.path.join(
        dataset_db.dataset_dir,
        'analyses',
        analysis_db.name,
        'topic_embeddings.json'
    )

    if not os.path.exists(embeddings_file):
        print(f"Warning: No embeddings file found at {embeddings_file}")
        print("Run the analysis with the latest BERTopic code to generate embeddings.")
        return

    print(f"Loading topic embeddings from {embeddings_file}")
    with io.open(embeddings_file, 'r', encoding='utf-8') as f:
        embeddings = json.load(f)

    # Get all topics
    topics = list(analysis_db.topics.all().order_by('number'))
    topics_idx = {topic.number: topic.id for topic in topics}

    print(f"Computing pairwise embedding distances for {len(topics)} topics...")

    # Compute pairwise distances
    for i, topic1 in enumerate(topics):
        if i % 10 == 0:
            print(f"  Processing topic {i}/{len(topics)}")

        topic1_id = str(topic1.number)
        if topic1_id not in embeddings:
            print(f"Warning: No embedding for topic {topic1_id}")
            continue

        emb1 = embeddings[topic1_id]

        for topic2 in topics:
            topic2_id = str(topic2.number)
            if topic2_id not in embeddings:
                continue

            emb2 = embeddings[topic2_id]

            # Compute cosine distance
            distance = cosine_distance(emb1, emb2)

            yield {
                'origin_topic_id': topics_idx[topic1.number],
                'ending_topic_id': topics_idx[topic2.number],
                'value': distance,
            }

    print(f"✓ {metric_name} computed successfully")
