import ldap
import logging
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .forms import LDAPSettingsForm
from .models import LDAPSettings
from django.contrib import messages
from django.template.loader import render_to_string
from .ldap_utils import get_user_details


@login_required
def dashboard_view(request):
    return render(request, 'dashboard/dashboard.html')


@login_required
def settings_view(request):
    try:
        # Try to get the current settings
        current_settings = LDAPSettings.objects.get(id=1)
    except LDAPSettings.DoesNotExist:
        # If settings do not exist, create a new empty instance
        current_settings = LDAPSettings.objects.create()

    if request.method == 'POST':
        # If form is submitted, populate the form with the request data
        form = LDAPSettingsForm(request.POST, instance=current_settings)
        if form.is_valid():
            form.save()
            messages.success(request, 'Settings updated successfully.')
            # Add logging or print statement here for debugging
            print("Form saved successfully.")
            return redirect('dashboard-settings')

    else:
        # If not a POST request, instantiate the form with current settings
        form = LDAPSettingsForm(instance=current_settings)

    # Render the settings page with the form
    return render(request, 'dashboard/settings.html', {'form': form})
