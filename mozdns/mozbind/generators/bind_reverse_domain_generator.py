from mozdns.mozbind.generators.bind_domain_generator import render_ns
from mozdns.ip.utils import ip_to_dns_form

from string import Template
import pdb
# Knobs
ip_just = 30
name_just = 1
type_just = 15
class_just = 10
prio_just = 3
data_just = 7
extra_just = 3

def render_ptr(ptr_set):
    """
    name ttl  class   rr     name
    """
    BUILD_STR = ''
    template = Template("{ip:$ip_just} {ttl} {rclass:$class_just} {rtype:$type_just} {name:$name_just}.\n")
    template = template.substitute(ip_just=ip_just, class_just=class_just,
                        type_just=type_just, name_just=name_just)
    for ptr in ptr_set:
        if ptr.ttl == 3600 or ptr.ttl is None:
            ttl = ''
        else:
            ttl = str(ptr.ttl)
        BUILD_STR += template.format(ip=ptr.dns_name(), ttl=ttl, rclass='IN',
                rtype='PTR', name=ptr.name)
    return BUILD_STR

def render_intr(interface_set):
    BUILD_STR = ''
    template = Template("{ip:$ip_just} {ttl} {rclass:$class_just} {rtype:$type_just} {name:$name_just}.\n")
    template = template.substitute(ip_just=ip_just, class_just=class_just,
                        type_just=type_just, name_just=name_just)
    for intr in interface_set:
        if intr.ttl == 3600 or intr.ttl is None:
            ttl = ''
        else:
            ttl = str(intr.ttl)
        BUILD_STR += template.format(ip=ip_to_dns_form(intr.ip_str), ttl=ttl, rclass='IN',
                rtype='PTR', name=intr.fqdn)
    return BUILD_STR

def render_reverse_domain(default_ttl, nameserver_set, interface_set, ptr_set):
    BUILD_STR = ''
    BUILD_STR += render_ns(nameserver_set)
    BUILD_STR += render_intr(interface_set)
    BUILD_STR += render_ptr(ptr_set)
    return BUILD_STR
