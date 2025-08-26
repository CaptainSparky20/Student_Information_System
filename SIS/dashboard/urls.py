from django.urls import path
from .views import unified_dashboard, profile_view, profile_update
from .views import parent_update

app_name = "dashboard"

urlpatterns = [
    path("", unified_dashboard, name="main_dashboard"),
    path("profile/", profile_view, name="profile"),
    path("profile/update/", profile_update, name="profile_update"),
    path("guardian/<int:pk>/update/", parent_update, name="parent_update"),
]
