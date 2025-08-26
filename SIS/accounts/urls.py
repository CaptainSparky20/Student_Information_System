# accounts/urls.py
from django.urls import path, reverse_lazy
from django.contrib.auth import views as auth_views

from .views import unified_login  # you already have this

app_name = "accounts"

urlpatterns = [
    path("login/", unified_login, name="login"),
    # --- Password reset: request reset link by email ---
    path(
        "password-reset/",
        auth_views.PasswordResetView.as_view(
            template_name="accounts/password_reset/password_reset_form.html",
            email_template_name="accounts/password_reset/password_reset_email.txt",
            html_email_template_name="accounts/password_reset/password_reset_email.html",
            subject_template_name="accounts/password_reset/password_reset_subject.txt",
            success_url=reverse_lazy("accounts:password_reset_done"),
        ),
        name="password_reset",
    ),
    # --- "We sent you an email" confirmation page ---
    path(
        "password-reset/done/",
        auth_views.PasswordResetDoneView.as_view(
            template_name="accounts/password_reset/password_reset_done.html"
        ),
        name="password_reset_done",
    ),
    # --- Link in the email lands here (user sets a new password) ---
    path(
        "reset/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="accounts/password_reset/password_reset_confirm.html",
            success_url=reverse_lazy("accounts:password_reset_complete"),
        ),
        name="password_reset_confirm",
    ),
    # --- Final "password changed" page ---
    path(
        "reset/complete/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="accounts/password_reset/password_reset_complete.html"
        ),
        name="password_reset_complete",
    ),
]
