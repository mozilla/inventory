from string import Template
import pdb
# Knobs
name_just = 40
type_just = 15
class_just = 10
prio_just = 3
data_just = 7
extra_just = 3

def render_mx(mx_set):
    BUILD_STR = ''
    template = Template("{name:$name_just} {rclass:$class_just} {rtype:$type_just} {prio:$prio_just} {server:$data_just}.\n")
    template = template.substitute(name_just=name_just, class_just=class_just,
                        type_just=type_just, prio_just=prio_just, data_just=data_just)
    for mx in mx_set:
        BUILD_STR += "$TTL %s\n" % (mx.ttl)
        #name = mx.fqdn + '.' if mx.label != '' else '@'
        name = mx.fqdn + '.'
        BUILD_STR += template.format(name=name, rclass='IN', rtype='MX', prio=str(mx.priority),
                                    server=mx.server)
    return BUILD_STR

def render_ns(nameserver_set):
    BUILD_STR = ''
    template = Template("{name:$name_just} {rclass:$class_just} {rtype:$type_just} {server:$data_just}.\n")
    template = template.substitute(name_just=name_just, class_just=class_just,
                        type_just=type_just, data_just=data_just)
    for ns in nameserver_set:
        BUILD_STR += template.format(name='@', rclass='IN', rtype='NS', server=ns.server)
    return BUILD_STR

def render_address_record(addressrecord_set):
    BUILD_STR = ''
    template = Template("{name:$name_just} {rclass:$class_just} {rtype:$type_just} {address:$data_just}\n")
    template = template.substitute(name_just=name_just, class_just=class_just,
                        type_just=type_just, data_just=data_just)
    BUILD_STR += "$TTL %s\n" % (3600)
    for rec in addressrecord_set:
        if rec.ip_type == '4':
            rec_type = 'A'
        else:
            rec_type = 'AAAA'
        #name = rec.fqdn + '.' if rec.label != '' else '@'
        name = rec.fqdn + '.'
        BUILD_STR += template.format(name=name, rclass='IN', rtype=rec_type, address=rec.ip_str)
    return BUILD_STR

def render_cname(cname_set):
    BUILD_STR = ''

    template = Template("{name:$name_just} {rclass:$class_just} {rtype:$type_just} {data:$data_just}.\n")
    template = template.substitute(name_just=name_just, class_just=class_just,
                        type_just=type_just, data_just=data_just)
    for cname in cname_set:
        #name = cname.fqdn+'.' if cname.label != '' else '@'
        name = cname.fqdn + '.'
        BUILD_STR += template.format(name=name, rclass='IN', rtype='CNAME', data=cname.data)
    return BUILD_STR

def render_srv(srv_set):
    BUILD_STR = ''
    template = Template("{name:$name_just} {rclass:$class_just} {rtype:$type_just} {prio:$prio_just} {weight:$extra_just} {port:$extra_just} {target:$extra_just}.\n")
    template = template.substitute(name_just=name_just, class_just=class_just,
                        type_just=type_just, prio_just=prio_just, extra_just=extra_just)
    for srv in srv_set:
        #name = srv.fqdn + '.' if srv.label != '' else '@'
        name = srv.fqdn + '.'
        BUILD_STR += template.format(name=name, rclass='IN', rtype='SRV', prio=str(srv.priority), weight=str(srv.weight), port=str(srv.port), target=str(srv.target))
    return BUILD_STR

def render_txt(txt_set):
    BUILD_STR = ''

    template = Template("{name:$name_just} {rclass:$class_just} {rtype:$type_just} \"{data:$data_just}\"\n")
    template = template.substitute(name_just=name_just, class_just=class_just,
                        type_just=type_just, data_just=data_just)
    for txt in txt_set:
        #name = txt.fqdn + '.' if txt.label != '' else '@'
        name = txt.fqdn + '.'
        BUILD_STR += template.format(name=name, rclass='IN', rtype='TXT', data=txt.txt_data)
    return BUILD_STR

def render_zone( default_ttl, nameserver_set, mx_set, addressrecord_set,
        interface_set, cname_set, srv_set, txt_set):
    BUILD_STR = ''
    BUILD_STR += render_ns(nameserver_set)
    BUILD_STR += render_mx(mx_set)
    BUILD_STR += render_address_record(addressrecord_set)
    BUILD_STR += render_address_record(interface_set)
    BUILD_STR += render_cname(cname_set)
    BUILD_STR += render_srv(srv_set)
    BUILD_STR += render_txt(txt_set)
    return BUILD_STR
