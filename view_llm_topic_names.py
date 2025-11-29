#!/usr/bin/env python
"""
View LLM-generated topic names for analyses.

Usage:
    python view_llm_topic_names.py <dataset_name> <analysis_name> [num_topics_to_show]

Example:
    python view_llm_topic_names.py state_of_the_union lda20topics
    python view_llm_topic_names.py state_of_the_union lda100topics 20
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'topicalguide.settings')
django.setup()

from visualize.models import Analysis, TopicNameScheme, TopicName


def view_topic_names(dataset_name, analysis_name, num_to_show=None):
    """View LLM-generated topic names for an analysis."""

    try:
        analysis = Analysis.objects.get(
            dataset__name=dataset_name,
            name=analysis_name
        )
    except Analysis.DoesNotExist:
        print(f"Error: Analysis '{analysis_name}' not found for dataset '{dataset_name}'")
        print()
        print("Available analyses:")
        for a in Analysis.objects.filter(dataset__name=dataset_name):
            print(f"  - {a.name}")
        return 1

    try:
        llm_scheme = TopicNameScheme.objects.get(name='LLM-10words')
    except TopicNameScheme.DoesNotExist:
        print("Error: LLM-10words naming scheme not found.")
        print("Have you run generate_llm_topic_names.py yet?")
        return 1

    topic_names = TopicName.objects.filter(
        topic__analysis=analysis,
        name_scheme=llm_scheme
    ).order_by('topic__number')

    total_count = topic_names.count()

    if total_count == 0:
        print(f"No LLM-generated topic names found for {analysis_name}")
        print()
        print("Run this to generate them:")
        print(f"  python generate_llm_topic_names.py {dataset_name} {analysis_name}")
        return 1

    # Determine how many to show
    if num_to_show is None:
        num_to_show = min(20, total_count)
    else:
        num_to_show = min(num_to_show, total_count)

    print("=" * 70)
    print(f"LLM-Generated Topic Names: {dataset_name} / {analysis_name}")
    print("=" * 70)
    print()

    for topic_name in topic_names[:num_to_show]:
        print(f"Topic {topic_name.topic.number:3d}: {topic_name.name}")

    if total_count > num_to_show:
        print()
        print(f"... and {total_count - num_to_show} more topics")

    print()
    print("=" * 70)
    print(f"Total: {total_count} LLM-generated topic names")
    print("=" * 70)

    # Also show other naming schemes for comparison
    print()
    print("Other naming schemes available:")
    other_schemes = TopicNameScheme.objects.exclude(name='LLM-10words')
    for scheme in other_schemes:
        count = TopicName.objects.filter(
            topic__analysis=analysis,
            name_scheme=scheme
        ).count()
        if count > 0:
            # Show first topic as example
            example = TopicName.objects.filter(
                topic__analysis=analysis,
                name_scheme=scheme
            ).order_by('topic__number').first()
            print(f"  {scheme.name}: {count} names (e.g., Topic 0: '{example.name}')")

    return 0


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        return 1

    dataset_name = sys.argv[1]
    analysis_name = sys.argv[2]
    num_to_show = int(sys.argv[3]) if len(sys.argv) > 3 else None

    return view_topic_names(dataset_name, analysis_name, num_to_show)


if __name__ == '__main__':
    sys.exit(main())
