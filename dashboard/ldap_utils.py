import ldap
from .models import LDAPSettings
from django.conf import settings

def get_user_details(dn):
    try:
        ldap_config = LDAPSettings.objects.first()
        conn = ldap.initialize(ldap_config.server_uri)
        conn.simple_bind_s(ldap_config.bind_dn, ldap_config.bind_password)

        search_filter = f"(distinguishedName={dn})"
        search_attribute = ['displayName', 'sAMAccountName', 'description', 'objectClass', 'userAccountControl']
        
        result = conn.search_s(dn, ldap.SCOPE_BASE, search_filter, search_attribute)
        
        # Assuming the search returns at least one entry
        if result:
            _, user_attrs = result[0]
            # Extract the necessary attributes and return them
            user_info = {
                'displayName': user_attrs.get('displayName', [b''])[0].decode('utf-8'),
                'sAMAccountName': user_attrs.get('sAMAccountName', [b''])[0].decode('utf-8'),
                'description': user_attrs.get('description', [b''])[0].decode('utf-8'),
                'objectClass': [obj.decode('utf-8') for obj in user_attrs.get('objectClass', [])],
                'userAccountControl': user_attrs.get('userAccountControl', [b''])[0].decode('utf-8'),
            }
            return user_info
    except ldap.LDAPError as e:
        print("LDAP Error: ", e)
        return None
    finally:
        conn.unbind_s()
