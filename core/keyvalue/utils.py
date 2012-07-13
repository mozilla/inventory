import re
from django.core.exceptions import ValidationError


is_attr = re.compile("^attr_\d+$")

def get_aa(obj):
    members = dir(obj)
    aa = []
    for member in members:
        if member.startswith("_aa"):
            aa.append(member[4:])
    return aa

def get_attrs(query_dict):
    kv = {}
    for param, values in query_dict.iteritems():
        if (is_attr.match(param) and
            query_dict.has_key("{0}_value".format(param))):
                # u'attr_0': [u'<attr>']
                # u'key_attr_0': [u'<attr_value>']
                key = query_dict[param]
                value = query_dict["{0}_value".format(param)]

                if key in kv:
                    raise ValidationError("{0} is already an "
                        "attribute.".format(key))
                kv[key] = value

    return kv

def update_attrs(kv, attrs, KVClass, obj, obj_name):
    """
    :param kv: The KV pairs being added to the object.
    :type kv: dict
    :param attrs: The existing KV pairs.
    :type attrs: :class:`QuerySet`
    :param KVClass: The KeyValue Class being used to validate new KV pairs.
    :type KVClass: class
    :param obj: The object the KV paris are being associated to.
    :type obj: object
    :param obj_name: The name of the foreign key back to obj
    :type obj_name: str
    """
    to_save = []
    for attr, value in kv.iteritems():
        if not attr and not value:
            continue
        if attrs.filter(key=attr):
            kv = attrs.get(key=attr)
            kv.value = value
            to_save.append(kv)
        else:
            # This kv is new. Let's create it and add it to the
            # to_save list for saving!
            kv = KVClass(key=attr, value=value)
            to_save.append(kv)

    for kv in to_save:
        setattr(kv, obj_name, obj)
        kv.clean()
        kv.save()

def get_docstrings(obj):
    members = dir(obj)
    docs = []
    for member in members:
        if member.startswith("_aa"):
            docs.append((member[4:], getattr(obj, member).__doc__))

    return docs
