from django.utils import timezone
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

    # find the restaurant associated with this user
    # for servers, drivers, kitchen staff this is the restaurant they are linked to via their tables
    # for managers it is the restaurant where they are the manager
    # for owners it shows all active notes across all restaurants
    try:
        if request.user.role == models.User.Role.MANAGER:
            restaurant = models.Restaurant.objects.filter(user=request.user).first()
            if not restaurant:
                return {'active_manager_notes': []}
            notes = models.ManagerNote.objects.filter(
                restaurant=restaurant,
                expires_at__gt=now
            ).filter(
                models.Q(target_role=0) | models.Q(target_role=request.user.role)
            ).order_by('-created_at')

        elif request.user.role == models.User.Role.OWNER:
            notes = models.ManagerNote.objects.filter(
                expires_at__gt=now
            ).filter(
                models.Q(target_role=0) | models.Q(target_role=request.user.role)
            ).order_by('-created_at')

        else:
            # for all other staff roles, find their restaurant via assigned table
            # if no table is assigned, fall back to the first active restaurant
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
                models.Q(target_role=0) | models.Q(target_role=request.user.role)
            ).order_by('-created_at')
            notes = models.ManagerNote.objects.filter(
                restaurant=assigned_table.restaurant,
                expires_at__gt=now
            ).filter(
                models.Q(target_role=0) | models.Q(target_role=request.user.role)
            ).order_by('-created_at')

    except Exception:
        return {'active_manager_notes': []}

    return {'active_manager_notes': list(notes)}