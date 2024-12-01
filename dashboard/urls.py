from django.urls import path

from dashboard.views import AnalyticsView

urlpatterns = [
    path('analytics/', AnalyticsView.as_view(), name='analytics'),
]