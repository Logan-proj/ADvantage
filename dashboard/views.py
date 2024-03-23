import ldap
import logging
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .forms import LDAPSettingsForm
from .models import LDAPSettings
from django.contrib import messages
from .forms import SearchADForm
from ldap.filter import escape_filter_chars
from ldap.controls import SimplePagedResultsControl
from django.http import JsonResponse
from django.template.loader import render_to_string
from .ldap_utils import get_user_details
from ldap3 import Server, Connection, ALL_ATTRIBUTES

# Get an instance of a logger
logger = logging.getLogger(__name__)

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


@login_required
def search_ad(request):
    search_results = []
    search_query = ''

    if request.method == 'POST':
        form = SearchADForm(request.POST)
        if form.is_valid():
            search_query = escape_filter_chars(form.cleaned_data['search_query'])

            ldap_config = LDAPSettings.objects.first()
            if ldap_config:
                conn = ldap.initialize(ldap_config.server_uri)
                conn.simple_bind_s(ldap_config.bind_dn, ldap_config.bind_password)

                # Prepare the search filter
                search_filter = f"(&(objectClass=top)(|(sAMAccountName=*{search_query}*)(displayName=*{search_query}*)))"
                search_scope = ldap.SCOPE_SUBTREE
                # Include additional attributes such as userAccountControl for account status and distinguishedName for OU
                search_attributes = [
                    'displayName', 'sAMAccountName', 'description', 
                    'userAccountControl', 'distinguishedName', 'objectClass', 'distinguishedName'
                ]

                # Create a page control object to handle paginated results
                page_control = SimplePagedResultsControl(True, size=100, cookie='')

                try:
                    # Request the paged results control to be critical
                    while True:
                        # Request new page of results
                        ldap_result_id = conn.search_ext(
                            ldap_config.user_search_base_dn,
                            search_scope,
                            search_filter,
                            search_attributes,
                            serverctrls=[page_control]
                        )

                        # Process results
                        rtype, rdata, rmsgid, serverctrls = conn.result3(ldap_result_id)
                        # Process and format the search results
                        for dn, entry in rdata:
                            if dn:  # If the result has a DN, it's valid
                                account_control = entry.get('userAccountControl', [0])[0]
                                is_disabled = int(account_control) & 2 > 0
                                is_locked = int(account_control) & 16 > 0
                                ou = entry.get('distinguishedName', [b''])[0].decode('utf-8').split(',')[1]  # Adjust based on actual DN format
                                object_class = [item.decode('utf-8') for item in entry.get('objectClass', [])]
                                display_name = entry.get('displayName', [b''])[0].decode('utf-8')
                                sam_account_name = entry.get('sAMAccountName', [b''])[0].decode('utf-8')
                                description = entry.get('description', [b''])[0].decode('utf-8')
                                dn = entry.get('distinguishedName', [b''])[0].decode('utf-8')

                                #formatted_result = f"{display_name} ({sam_account_name})\t{description}"
                                formatted_result = {
                                    'display_name': display_name,
                                    'sam_account_name': sam_account_name,
                                    'description': description,
                                    'is_disabled': is_disabled,
                                    'is_locked': is_locked,
                                    'ou': ou,
                                    'object_class': object_class,
                                    'dn': dn
                                }

                                search_results.append(formatted_result)

                        # Extract cookie from response
                        pctrls = [c for c in serverctrls if c.controlType == SimplePagedResultsControl.controlType]
                        if pctrls:
                            if pctrls[0].cookie:
                                # Assign new cookie for next iteration
                                page_control.cookie = pctrls[0].cookie
                            else:
                                break

                except ldap.LDAPError as e:
                    messages.error(request, f"LDAP Error: {str(e)}")

                finally:
                    conn.unbind_s()

    else:
        form = SearchADForm()

    return render(request, 'dashboard/search_ad.html', {'form': form, 'search_results': search_results, 'search_query': search_query})


def user_details(request):
    dn = request.GET.get('dn')
    ldap_config = LDAPSettings.objects.first()
    server_uri = ldap_config.server_uri
    user_dn = ldap_config.bind_dn
    password = ldap_config.bind_password

    # Establish a connection to the server
    conn = ldap.initialize(server_uri)

    try:
        # Connect with service account
        conn.simple_bind_s(user_dn, password)

        # Perform a search operation
        search_scope = ldap.SCOPE_BASE
        search_filter = '(objectClass=*)'
        result = conn.search_s(dn, search_scope, search_filter, None) # Get all attributes

        if result:
            _, attrs = result[0]  # Get attributes of the DN
            user_info = {}

            for key, value in attrs.items():
                # Check if the attribute's value is a byte string and decode accordingly
                if isinstance(value[0], bytes):
                    try:
                        user_info[key] = value[0].decode('utf-8')
                    except UnicodeDecodeError:
                        # For binary data, you can convert it to base64 or simply indicate it's binary data
                        user_info[key] = 'BINARY DATA'
                else:
                    user_info[key] = value[0]
            print(user_info)
            return JsonResponse(user_info)
        else:
            return JsonResponse({'error': 'User not found'}, status=404)

    except ldap.LDAPError as e:
        return JsonResponse({'error': str(e)}, status=500)

    finally:
        conn.unbind_s()
