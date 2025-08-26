from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from .forms import UnifiedLoginForm
from .models import CustomUser
from django.db.models import Q


def unified_login(request):
    if request.method == "POST":
        form = UnifiedLoginForm(request.POST)
        if form.is_valid():
            identifier = form.cleaned_data["identifier"]
            password = form.cleaned_data["password"]

            user = None

            # Try to get user by email or IC (case-insensitive)
            try:
                user_obj = CustomUser.objects.get(
                    Q(email__iexact=identifier)
                    | Q(identity_card_number__iexact=identifier)
                )
                # Authenticate always using email (username field)
                user = authenticate(request, username=user_obj.email, password=password)
            except CustomUser.DoesNotExist:
                # No such user
                user = None

            if user is not None and user.is_active:
                login(request, user)
                # Unified dashboard redirect
                if user.role in [
                    CustomUser.Role.STUDENT,
                    CustomUser.Role.LECTURER,
                    CustomUser.Role.ADMIN,
                ]:
                    return redirect("dashboard:main_dashboard")
                else:
                    messages.error(request, "User role not recognized.")
                    return redirect("accounts:login")
            else:
                messages.error(request, "Invalid email/IC or password.")
    else:
        form = UnifiedLoginForm()
    return render(request, "accounts/login.html", {"form": form})
