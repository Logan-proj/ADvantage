from django.db import models

class LDAPSettings(models.Model):
    """Model to store LDAP settings."""
    server_uri = models.CharField(max_length=255)
    bind_dn = models.CharField(max_length=255)
    bind_password = models.CharField(max_length=255)
    user_search_base_dn = models.CharField(max_length=255)
    user_search_filter = models.CharField(max_length=255, default="(sAMAccountName=%(user)s)")
    group_search_base_dn = models.CharField(max_length=255)
    group_search_filter = models.CharField(max_length=255, default="(objectClass=groupOfNames)")
    require_group_dn = models.CharField(max_length=255, blank=True, null=True)
    start_tls = models.BooleanField(default=True)
    # ... add other LDAP settings fields as needed

    def __str__(self):
        return "LDAP Settings"
