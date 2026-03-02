from django.urls import path
from .views import AnaliseOverlapView

urlpatterns = [
    path("overlap/", AnaliseOverlapView.as_view(), name="analise-overlap"),
]
