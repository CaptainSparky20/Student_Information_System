# notifications/views.py

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Notification

@login_required
def notification_list(request):
    # Get all notifications for the current user, ordered by creation time (newest first)
    notifications = request.user.notifications.order_by('-created_at')
    return render(request, 'notifications/list.html', {'notifications': notifications})

@login_required
def mark_notification_as_read(request, pk):
    """
    Marks a specific notification as read.
    This example uses form submission for simplicity.
    For a better user experience, consider using AJAX.
    """
    notification = get_object_or_404(Notification, pk=pk, lecturer=request.user)
    if request.method == 'POST':
        notification.is_read = True
        notification.save()
        # Redirect back to the notifications list or another appropriate page
        return redirect('notifications:list')  # Assuming you've named your URL pattern 'list'
    # If it's a GET request (e.g., displaying a confirmation form), render a template
    return render(request, 'notifications/confirm_mark_as_read.html', {'notification': notification})
