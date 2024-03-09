# Custom LDAP backend to dynamically set LDAP configuration
# Extends django_auth_ldap.backend.LDAPBackend
from django_auth_ldap.backend import LDAPBackend
from django.core.exceptions import ImproperlyConfigured
from .utils import get_ldap_config

class DynamicLDAPBackend(LDAPBackend):
    """Custom LDAP backend to dynamically set LDAP configuration"""
    def authenticate(self, request, username=None, password=None, **kwargs):
        """Override the authenticate method to dynamically set the LDAP configuration."""
        # Retrieve LDAP configuration from the database
        ldap_config = get_ldap_config()

        if ldap_config:
            # Set LDAP server URI and BIND credentials
            self.settings.SERVER_URI = ldap_config['server_uri']
            self.settings.BIND_DN = ldap_config['bind_dn']
            self.settings.BIND_PASSWORD = ldap_config['bind_password']
            self.settings.USER_SEARCH = ldap_config['user_search']
            self.settings.GROUP_SEARCH = ldap_config['group_search']
            self.settings.REQUIRE_GROUP = ldap_config['require_group_dn']
            # ... set other required login parameters as needed
        else:
            # Raise an ImproperlyConfigured exception if settings are not found
            raise ImproperlyConfigured("LDAP settings not found in the database")

        # Authenticate the user using the super() function to call the parent method
        return super().authenticate(request, username=username, password=password, **kwargs)
