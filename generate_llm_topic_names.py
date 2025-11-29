#!/usr/bin/env python
"""
Generate LLM-based topic names for an existing topic model analysis.

Usage:
    python generate_llm_topic_names.py <dataset_name> <analysis_name>

Example:
    python generate_llm_topic_names.py state_of_the_union lda20topics

Requirements:
    - OpenAI API key set as OPENAI_API_KEY environment variable
    - openai package installed (pip install openai)
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'topicalguide.settings')
django.setup()

from import_tool.analysis.name_schemes.llm_namer import LLMTopicNamer
from import_tool.analysis.utilities import create_topic_names
from visualize.models import Analysis


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)

    dataset_name = sys.argv[1]
    analysis_name = sys.argv[2]

    # Optional: Get model from command line (default: gpt-4o-mini)
    model = sys.argv[3] if len(sys.argv) > 3 else "gpt-4o-mini"

    print(f"Generating LLM-based topic names for:")
    print(f"  Dataset: {dataset_name}")
    print(f"  Analysis: {analysis_name}")
    print(f"  Model: {model}")
    print()

    # Get the analysis from the database
    try:
        analysis_db = Analysis.objects.get(
            dataset__name=dataset_name,
            name=analysis_name
        )
    except Analysis.DoesNotExist:
        print(f"Error: Analysis '{analysis_name}' not found for dataset '{dataset_name}'")
        print()
        print("Available analyses:")
        for analysis in Analysis.objects.filter(dataset__name=dataset_name):
            print(f"  - {analysis.name}")
        sys.exit(1)

    num_topics = analysis_db.topics.count()
    print(f"Found {num_topics} topics to name.")
    print()

    # Check for OpenAI API key
    if not os.environ.get('OPENAI_API_KEY'):
        print("Error: OPENAI_API_KEY environment variable not set.")
        print("Set it with: export OPENAI_API_KEY='your-api-key'")
        sys.exit(1)

    # Create LLM topic namer
    llm_namer = LLMTopicNamer(
        n_words=10,              # Number of top words to consider
        n_docs=3,                # Number of sample documents to include
        model=model,             # OpenAI model
        max_label_length=50,     # Maximum characters in generated label
        fallback_to_topn=True    # Fall back to simple naming on errors
    )

    print("Generating topic names (this may take a minute)...")
    print()

    try:
        # Generate topic names
        create_topic_names('default', analysis_db, [llm_namer], verbose=True)
        print()
        print("✓ LLM-based topic names generated successfully!")
        print()
        print("View them in the web interface:")
        print("  1. python manage.py runserver")
        print("  2. Navigate to http://localhost:8000/")
        print(f"  3. Select dataset '{dataset_name}' and analysis '{analysis_name}'")
        print("  4. Look for the 'LLM-10words' naming scheme")

    except Exception as e:
        print(f"Error generating topic names: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
