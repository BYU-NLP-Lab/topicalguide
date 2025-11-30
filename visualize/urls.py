from django.urls import path
from visualize import root, api, bertopic_viz

urlpatterns = [
    path('', root.root, name='root'),
    path('terms', root.terms, name='terms'),
    path('api', api.api, name='api'),
    path('bertopic-viz/<str:dataset_name>/<str:analysis_name>/<str:viz_type>/',
         bertopic_viz.get_bertopic_visualization,
         name='bertopic_viz'),
]
