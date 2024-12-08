from django.urls import path

from apps.dashboard.views import AnalyticsView

urlpatterns = [
    path('analytics/', AnalyticsView.as_view(), name='analytics'),
]