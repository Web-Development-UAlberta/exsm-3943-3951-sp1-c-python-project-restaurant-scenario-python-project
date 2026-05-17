from django.utils import timezone
from django.db.models import Q
from . import models


def manager_notes(request):
    """
    Injects active manager notes into every template context so the base.html
    can render them without each view needing to query for them manually.
    Only runs for authenticated non-customer users.
    Notes are filtered to the user's restaurant and their role (or all staff notes).
    """
    if not request.user.is_authenticated:
        return {'active_manager_notes': []}

    if request.user.role == models.User.Role.CUSTOMER:
        return {'active_manager_notes': []}

    now = timezone.now()

    # managers see notes for their own restaurant
    if request.user.role == models.User.Role.MANAGER:
        restaurant = models.Restaurant.objects.filter(user=request.user).first()
        if not restaurant:
            return {'active_manager_notes': []}
        notes = models.ManagerNote.objects.filter(
            restaurant=restaurant,
            expires_at__gt=now
        ).filter(
            Q(target_role=0) | Q(target_role=request.user.role)
        ).order_by('-created_at')

    # owners see all notes across all restaurants
    elif request.user.role == models.User.Role.OWNER:
        notes = models.ManagerNote.objects.filter(
            expires_at__gt=now
        ).filter(
            Q(target_role=0) | Q(target_role=request.user.role)
        ).order_by('-created_at')

    # all other staff roles: find restaurant via assigned table or fall back to first active restaurant
    else:
        assigned_table = models.Table.objects.filter(
            assigned_server=request.user
        ).select_related('restaurant').first()

        if assigned_table:
            restaurant = assigned_table.restaurant
        else:
            # kitchen staff and drivers are not assigned to tables
            # fall back to the first active restaurant so they still see notes
            restaurant = models.Restaurant.objects.filter(is_active=True).first()

        if not restaurant:
            return {'active_manager_notes': []}

        notes = models.ManagerNote.objects.filter(
            restaurant=restaurant,
            expires_at__gt=now
        ).filter(
            Q(target_role=0) | Q(target_role=request.user.role)
        ).order_by('-created_at')

    return {'active_manager_notes': list(notes)}