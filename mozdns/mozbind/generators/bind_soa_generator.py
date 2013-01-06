from gettext import gettext as _

# Don't actually write the serial number. Something later in the builds will
# worry about this

def render_soa(soa, root_domain, domains, bind_path):
    BUILD_STR = "{root_domain}.     IN      SOA     {primary}. {contact}. (\n\
                            {{serial:20}}     ; Serial\n\
                            {serial:20}     ; Serial Number\n\
                            {refresh:20}     ; Refresh\n\
                            {retry:20}     ; Retry\n\
                            {expire:20}     ; Expire\n\
                            {minimum:20}     ; Minimum\n\
            )\n\n".format(root_domain=root_domain.name, primary=soa.primary,
                          contact=soa.contact, refresh=str(soa.refresh),
                          retry=str(soa.retry), expire=str(soa.expire),
                          minimum=soa.minimum)

    for domain in domains:
        BUILD_STR += _("\t$INCLUDE {bind_path}/db.{domain}\n".
                       format(bind_path=bind_path,
                       domain=domain.name))
    return BUILD_STR


def render_soa_only(soa, root_domain):
    BUILD_STR = "{root_domain}.     IN      SOA     {primary}. {contact}. (\n\
                            {{serial:20}}     ; Serial\n\
                            {refresh:20}     ; Refresh\n\
                            {retry:20}     ; Retry\n\
                            {expire:20}     ; Expire\n\
                            {minimum:20}     ; Minimum\n\
                )\n\n".format(root_domain=root_domain.name,
                              primary=soa.primary, contact=soa.contact,
                              refresh=str(soa.refresh), retry=str(soa.retry),
                              expire=str(soa.expire), minimum=soa.minimum)
    return BUILD_STR
