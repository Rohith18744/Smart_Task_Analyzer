from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView

urlpatterns = [
    path('admin/', admin.site.urls),
    # API versioning allows for future non-breaking changes
    path('api/v1/', include('tasks.urls')),
    # Serve the frontend application on the root URL
    path('', TemplateView.as_view(template_name='index.html')),
]