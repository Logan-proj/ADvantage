from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from dashboard.forms import SearchADForm
from ldap.filter import escape_filter_chars
from dashboard.models import LDAPSettings
import ldap
from ldap.controls import SimplePagedResultsControl
from django.contrib import messages
from django.http import JsonResponse
import logging


@login_required
def search_view(request):
    return render(request, 'search/search_ad.html')

@login_required
def user_details_view(request, dn):
    return render(request, 'search/user-details.html', {'dn': dn})

logger = logging.getLogger(__name__)

def get_ldap_connection():
    """
    Establishes an LDAP connection using settings from the LDAPSettings model.
    Returns:
        conn: The LDAP connection object if successful, None otherwise.
        error_message: Error message string if an error occurs, otherwise None.
    """
    try:
        ldap_config = LDAPSettings.objects.first()
        if not ldap_config:
            return None, 'LDAP configuration not found.'
        conn = ldap.initialize(ldap_config.server_uri)
        conn.simple_bind_s(ldap_config.bind_dn, ldap_config.bind_password)
        return conn, None
    except ldap.LDAPError as e:
        logger.error(f'Error establishing LDAP connection: {e}')
        return None, f'Error establishing LDAP connection: {e}'

@login_required
def search_ad(request):
    search_results = []
    search_query = ''
    form = SearchADForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        # Escape special characters in the search query
        search_query = escape_filter_chars(form.cleaned_data['search_query'])
        conn, error_message = get_ldap_connection()

        if error_message:
            messages.error(request, error_message)
            return render(request, 'search/search_ad.html', {'form': form, 'search_results': search_results, 'search_query': search_query})

        try:
            # Refactor repeated strings into variables
            ldap_config = LDAPSettings.objects.first()
            search_base = ldap_config.user_search_base_dn
            search_filter = f"(&(objectClass=top)(|(sAMAccountName=*{search_query}*)(displayName=*{search_query}*)))"
            search_attributes = [
                'displayName', 'sAMAccountName', 'description', 
                'userAccountControl', 'distinguishedName', 'objectClass'
            ]

             # Utilize a utility function for search and handling paginated results
            search_results = perform_ldap_search(conn, search_base, search_filter, search_attributes) # list of dictionaries

        except ldap.LDAPError as e:
            messages.error(request, f"LDAP Error: {e}")
        finally:
            if conn:
                conn.unbind_s()

    return render(request, 'search/search_ad.html', {'form': form, 'search_results': search_results, 'search_query': search_query})


def perform_ldap_search(conn, base_dn, search_filter, search_attributes):
    """
    Performs an LDAP search and returns formatted results.
    """
    page_control = SimplePagedResultsControl(True, size=100, cookie='')
    search_results = []

    while True:
        ldap_result_id = conn.search_ext(
            base_dn,
            ldap.SCOPE_SUBTREE,
            search_filter,
            search_attributes,
            serverctrls=[page_control]
        )
        
        rtype, rdata, rmsgid, serverctrls = conn.result3(ldap_result_id)
        search_results.extend(parse_ldap_entries(rdata))

        pctrls = [c for c in serverctrls if c.controlType == SimplePagedResultsControl.controlType]
        if not pctrls or not pctrls[0].cookie:
            break  # Exit the loop if no more pages
        page_control.cookie = pctrls[0].cookie  # Prepare for next page

    return search_results


def parse_ldap_entries(entries):
    """
    Parses LDAP entries into a more usable format.
    """
    results = []
    for dn, entry in entries:
        if dn:
            # Extract and process LDAP entry attributes as needed
            formatted_result = process_ldap_entry(entry)
            results.append(formatted_result)
    return results


def process_ldap_entry(entry):
    """
    Processes a single LDAP entry and returns a formatted result.
    """
    account_control = entry.get('userAccountControl', [0])[0]
    is_disabled = int(account_control) & 2 > 0
    is_locked = int(account_control) & 16 > 0
    ou = entry.get('distinguishedName', [b''])[0].decode('utf-8').split(',')[1]

    formatted_result = {
        'display_name': entry.get('displayName', [b''])[0].decode('utf-8'),
        'sam_account_name': entry.get('sAMAccountName', [b''])[0].decode('utf-8'),
        'description': entry.get('description', [b''])[0].decode('utf-8'),
        'is_disabled': is_disabled,
        'is_locked': is_locked,
        'ou': ou,
        'object_class': [item.decode('utf-8') for item in entry.get('objectClass', [])],
        'dn': entry.get('distinguishedName', [b''])[0].decode('utf-8'),
    }

    return formatted_result


# parse binary logonHours attribute
def parse_logon_hours(logonHours):
    allowed_hours = []
    for day in range(7):  # 7 days in a week
        for hour in range(24):  # 24 hours in a day
            byte_index = (day * 24 + hour) // 8
            bit_index = (day * 24 + hour) % 8
            if logonHours[byte_index] & (1 << bit_index):
                allowed_hours.append((day, hour))
    # Decode logon hours
    days_of_the_week = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
    formatted_allowed_hours = [(days_of_the_week[day], hour) for day, hour in allowed_hours]
    return formatted_allowed_hours


def get_user_details(request):
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
                        # Special functions for interpreting binary data
                        # if key == 'logonHours':
                        #     user_info[key] = parse_logon_hours(value[0])
                        # else:
                        #     # Handle other binary data appropriately
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


def get_logonHours(request):
    dn = request.GET.get('dn')
    if not dn:
        return JsonResponse({'error': 'DN parameter is required.'}, status=400)

    conn, error = get_ldap_connection()
    if error:
        return JsonResponse({'error': error}, status=500)

    try:
        if conn:
            ldap_config = LDAPSettings.objects.first()
            if not ldap_config:
                return JsonResponse({'error': 'LDAP configuration not found.'}, status=500)

            conn = ldap.initialize(ldap_config.server_uri)
            conn.set_option(ldap.OPT_REFERRALS, 0)  # Necessary for some LDAP servers
            conn.simple_bind_s(ldap_config.bind_dn, ldap_config.bind_password)

            search_scope = ldap.SCOPE_BASE
            search_filter = '(objectClass=*)'
            search_attributes = ['logonHours']
            result_id = conn.search(dn, search_scope, search_filter, search_attributes)
            result_type, result_data = conn.result(result_id, 0)  # Synchronously wait for the result

        if result_data:
            # Assuming 'result_data' is [(dn, {'logonHours': [binary_data]})]
            _, attributes = result_data[0]
            if 'logonHours' in attributes:
                logon_hours_binary = attributes['logonHours'][0]
                logon_hours_data = parse_logon_hours(logon_hours_binary)
                return JsonResponse({'logonHours': logon_hours_data})
            else:
                return JsonResponse({'error': 'Logon hours data not found.'}, status=404)
        else:
            return JsonResponse({'error': 'User not found'}, status=404)
    except ldap.LDAPError as e:
        return JsonResponse({'error': str(e)}, status=500)
    finally:
        if conn:
            conn.unbind_s()
