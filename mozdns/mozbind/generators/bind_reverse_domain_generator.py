from mozdns.mozbind.generators.bind_domain_generator import render_ns

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
    BUILD_STR = ''
    template = Template("{ip:$ip_just} {rclass:$class_just} {rtype:$type_just} {name:$name_just}.\n")
    template = template.substitute(ip_just=ip_just, class_just=class_just,\
                        type_just=type_just, name_just=name_just)
    for ptr in ptr_set:
        BUILD_STR += template.format(ip=ptr.ip_str, rclass='IN', rtype='PTR', name=ptr.name)
    return BUILD_STR

def render_reverse_domain( default_ttl, nameserver_set, ptr_set ):
    BUILD_STR = ''
    BUILD_STR += render_ns(nameserver_set)
    BUILD_STR += render_ptr(ptr_set)
    return BUILD_STR
