__import__('inventory_context')

from mozdns.domain.models import Domain

import pprint
import simplejson as json

pp = pprint.PrettyPrinter(depth=4)


def emit_node(domain):
    node = {}
    node['name'] = domain.name
    children = []
    for child_domain in domain.domain_set.all():
        children.append(emit_node(child_domain))

    object_sets = [
        domain.addressrecord_set,
        domain.cname_set,
        domain.mx_set,
        domain.srv_set,
        domain.sshfp_set,
        domain.staticreg_set,
        domain.reverse_staticreg_set,
        domain.txt_set,
        domain.ptr_set,
        domain.nameserver_set
    ]
    for obj_type in object_sets:
        for obj in obj_type.all():
            children.append({
                'name': obj.bind_render_record()
            })
    if children:
        node['children'] = children
    return node

net = Domain.objects.get(name='net')

children = []

for domain in Domain.objects.filter(master_domain=None):
    children.append(emit_node(domain))

tree = {'name': '.', 'children': children}

print json.dumps(tree)
