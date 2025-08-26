from django.urls import path, include
from django.views.generic import RedirectView
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", RedirectView.as_view(pattern_name="accounts:login", permanent=False)),
    path("accounts/", include("accounts.urls", namespace="accounts")),
    path("student/", include("student.urls", namespace="student")),
    path("lecturer/", include("lecturer.urls", namespace="lecturer")),
    path("adminportal/", include("adminportal.urls")),
    path("dashboard/", include("dashboard.urls", namespace="dashboard")),
    path(
        "logout/",
        auth_views.LogoutView.as_view(next_page="accounts:login"),
        name="logout",
    ),
    path("accounts/", include("django.contrib.auth.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
