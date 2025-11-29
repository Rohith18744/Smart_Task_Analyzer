from django.urls import path
from django.views.generic import TemplateView
from tasks.views import analyze_tasks, suggest_tasks

urlpatterns = [
    path("", TemplateView.as_view(template_name="index.html")),
    path("api/v1/tasks/analyze/", analyze_tasks),
    path("api/v1/tasks/suggest/", suggest_tasks),
]
