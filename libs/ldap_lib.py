import ldap

from django.conf import settings

def get_ldap_dn(email):
    try:
        conn = ldap.initialize('ldap://%s/' % settings.LDAP_HOST)
        conn.simple_bind_s(settings.LDAP_USER, settings.LDAP_PASS)
        res = conn.search_s('dc=mozilla', ldap.SCOPE_SUBTREE, '(mail=%s)' % email, ['dn'])
        return res[0][0]
    except Exception, e:
        return None

def get_ldap_groups(dn):
    try:
        conn = ldap.initialize('ldap://%s/' % settings.LDAP_HOST)
        conn.simple_bind_s(settings.LDAP_USER, settings.LDAP_PASS)
        res = conn.search_s('ou=groups,dc=mozilla', ldap.SCOPE_SUBTREE, '(member=%s)' % dn, ['cn'])
        return [ r[1]['cn'][0] for r in res ] 
    except Exception, e:
        return None

def ldap_user_in_group(email, group):
    dn = get_ldap_dn(email)
    groups = get_ldap_groups(dn)
    if dn is not None and groups is not None:
        for ldap_group in groups:
            if str(ldap_group).lower() == str(group).lower():
                return True
    else:
        return False




def get_all_names():
    conn = ldap.initialize('ldap://%s/' % settings.LDAP_HOST)
    conn.simple_bind_s(settings.LDAP_USER, settings.LDAP_PASS)
    res = conn.search_s(settings.LDAP_SEARCH_PATH, ldap.SCOPE_SUBTREE, '(mail=*)', ['cn'])

    name_list = []
    for r in res:
        name_list.append(r[1]['cn'][0])
    name_list.sort()

    return name_list
