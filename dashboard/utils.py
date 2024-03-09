from django_auth_ldap.config import LDAPSearch
from ldap import SCOPE_SUBTREE
from .models import LDAPSettings

def get_ldap_config():
    """Function to retrieve LDAP configuration from the database."""
    ldap_settings = LDAPSettings.objects.first()
    if ldap_settings:
        # Set user search filter and base
        user_search_base = LDAPSearch(
            ldap_settings.user_search_base_dn,
            SCOPE_SUBTREE,
            ldap_settings.user_search_filter #user_search_filter
        )
        
        # Set group search filter and base
        group_search_base = LDAPSearch(
            ldap_settings.group_search_base_dn,
            SCOPE_SUBTREE,
            ldap_settings.group_search_filter #group_search_filter
        )
        
        config = {
            # Set LDAP configuration parameters
            'server_uri': ldap_settings.server_uri,
            'bind_dn': ldap_settings.bind_dn,
            'bind_password': ldap_settings.bind_password,
            'user_search': user_search_base,
            'group_search': group_search_base,
            'require_group_dn': ldap_settings.require_group_dn,
            'start_tls': ldap_settings.start_tls,
        }
        return config
    else:
        raise ValueError("LDAP settings not configured")
