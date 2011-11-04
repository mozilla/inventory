import ldap

from django.conf import settings


def get_all_names():
    conn = ldap.initialize('ldap://%s/' % settings.LDAP_HOST)
    conn.simple_bind_s(settings.LDAP_USER, settings.LDAP_PASS)
    res = conn.search_s(settings.LDAP_SEARCH_PATH,dc=mozilla', ldap.SCOPE_SUBTREE, '(mail=*)', ['cn'])

    name_list = []
    for r in res:
        name_list.append(r[1]['cn'][0])
    name_list.sort()

    return name_list
