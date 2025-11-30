"""
BERTopic Native Visualizations

This module provides endpoints to generate BERTopic's native Plotly visualizations
for the web interface.
"""

import os
import pickle
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_http_methods
from visualize.models import Dataset, Analysis


@require_http_methods(["GET"])
def get_bertopic_visualization(request, dataset_name, analysis_name, viz_type):
    """
    Generate a BERTopic visualization and return it as HTML.

    Args:
        dataset_name: Name of the dataset
        analysis_name: Name of the analysis (must be a BERTopic analysis)
        viz_type: Type of visualization:
            - topics: 2D topic map
            - documents: 2D document map
            - heatmap: Topic similarity matrix
            - hierarchy: Hierarchical clustering
            - hierarchical_documents: Documents across hierarchy
            - barchart: Top words per topic
            - term_rank: Term rank decline
            - topics_over_time: Topic evolution (requires timestamps)
            - topics_per_class: Topics by class (requires class labels)

    Returns:
        HTML response containing the Plotly visualization
    """
    try:
        # Get the dataset and analysis
        dataset = Dataset.objects.get(name=dataset_name)
        analysis = Analysis.objects.get(dataset=dataset, name=analysis_name)

        # Check if this is a BERTopic analysis
        if not analysis.name.startswith('bertopic'):
            return JsonResponse({
                'error': f'{analysis.name} is not a BERTopic analysis'
            }, status=400)

        # Load the BERTopic model
        model_file = os.path.join(
            dataset.dataset_dir,
            'analyses',
            analysis.name,
            'bertopic_model.pkl'
        )

        if not os.path.exists(model_file):
            return JsonResponse({
                'error': 'BERTopic model file not found'
            }, status=404)

        with open(model_file, 'rb') as f:
            topic_model = pickle.load(f)

        # Generate the requested visualization
        fig = None

        if viz_type == 'topics':
            # 2D visualization of topics in embedding space
            fig = topic_model.visualize_topics()

        elif viz_type == 'documents':
            # 2D visualization of documents colored by topic
            # Need to load the original documents for this
            docs_file = os.path.join(dataset.dataset_dir, 'analyses', analysis.name, 'documents.txt')
            if os.path.exists(docs_file):
                with open(docs_file, 'r', encoding='utf-8') as f:
                    docs = [line.strip() for line in f.readlines()]
                fig = topic_model.visualize_documents(docs)
            else:
                return JsonResponse({
                    'error': 'Documents file not found. This visualization requires the original documents.'
                }, status=404)

        elif viz_type == 'heatmap':
            # Topic similarity heatmap
            fig = topic_model.visualize_heatmap()

        elif viz_type == 'hierarchy':
            # Hierarchical clustering of topics
            fig = topic_model.visualize_hierarchy()

        elif viz_type == 'hierarchical_documents':
            # Documents across hierarchy levels
            docs_file = os.path.join(dataset.dataset_dir, 'analyses', analysis.name, 'documents.txt')
            if os.path.exists(docs_file):
                with open(docs_file, 'r', encoding='utf-8') as f:
                    docs = [line.strip() for line in f.readlines()]
                hierarchical_topics = topic_model.hierarchical_topics(docs)
                fig = topic_model.visualize_hierarchical_documents(docs, hierarchical_topics)
            else:
                return JsonResponse({
                    'error': 'Documents file not found. This visualization requires the original documents.'
                }, status=404)

        elif viz_type == 'barchart':
            # Top words per topic (limited to first 10 topics for performance)
            topics = list(range(min(10, len(topic_model.get_topic_freq()))))
            fig = topic_model.visualize_barchart(topics=topics, n_words=10)

        elif viz_type == 'term_rank':
            # Term rank decline visualization
            fig = topic_model.visualize_term_rank()

        elif viz_type == 'topics_over_time':
            # Topics over time (requires timestamps)
            timestamps_file = os.path.join(dataset.dataset_dir, 'analyses', analysis.name, 'timestamps.txt')
            docs_file = os.path.join(dataset.dataset_dir, 'analyses', analysis.name, 'documents.txt')
            if os.path.exists(timestamps_file) and os.path.exists(docs_file):
                with open(timestamps_file, 'r', encoding='utf-8') as f:
                    timestamps = [line.strip() for line in f.readlines()]
                with open(docs_file, 'r', encoding='utf-8') as f:
                    docs = [line.strip() for line in f.readlines()]
                topics_over_time = topic_model.topics_over_time(docs, timestamps)
                fig = topic_model.visualize_topics_over_time(topics_over_time)
            else:
                return JsonResponse({
                    'error': 'Timestamp data not found. This visualization requires temporal information.'
                }, status=404)

        elif viz_type == 'topics_per_class':
            # Topics per class (requires class labels)
            classes_file = os.path.join(dataset.dataset_dir, 'analyses', analysis.name, 'classes.txt')
            docs_file = os.path.join(dataset.dataset_dir, 'analyses', analysis.name, 'documents.txt')
            if os.path.exists(classes_file) and os.path.exists(docs_file):
                with open(classes_file, 'r', encoding='utf-8') as f:
                    classes = [line.strip() for line in f.readlines()]
                with open(docs_file, 'r', encoding='utf-8') as f:
                    docs = [line.strip() for line in f.readlines()]
                topics_per_class = topic_model.topics_per_class(docs, classes=classes)
                fig = topic_model.visualize_topics_per_class(topics_per_class)
            else:
                return JsonResponse({
                    'error': 'Class label data not found. This visualization requires document class labels.'
                }, status=404)

        else:
            return JsonResponse({
                'error': f'Unknown visualization type: {viz_type}'
            }, status=400)

        if fig is None:
            return JsonResponse({
                'error': 'Failed to generate visualization'
            }, status=500)

        # Convert Plotly figure to HTML
        html = fig.to_html(
            include_plotlyjs='cdn',
            full_html=True,
            config={'responsive': True}
        )

        # Create response with proper headers for iframe embedding
        response = HttpResponse(html, content_type='text/html')
        # Allow embedding in iframes from same origin
        response['X-Frame-Options'] = 'SAMEORIGIN'
        # Add cache control for large visualizations
        response['Cache-Control'] = 'public, max-age=3600'

        return response

    except Dataset.DoesNotExist:
        return JsonResponse({
            'error': f'Dataset "{dataset_name}" not found'
        }, status=404)
    except Analysis.DoesNotExist:
        return JsonResponse({
            'error': f'Analysis "{analysis_name}" not found in dataset "{dataset_name}"'
        }, status=404)
    except Exception as e:
        import traceback
        return JsonResponse({
            'error': f'Error generating visualization: {str(e)}',
            'traceback': traceback.format_exc()
        }, status=500)
