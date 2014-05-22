# It's important for users to be able to see the schemas available for
# searching in the UI. This file consists of functions that 'autodiscover'
# those schemas.
from django.db.models.related import RelatedObject

from core.search.compiler.invfilter import dsearchables, searchables


def discover_for_class(dclass, depth=3):
    """
    Loop over all fields on a class and add them to the field_names list. If a
    relational field is found, recursively call discover_for_class to find the
    fields on the related class. Keep track of depth so we don't get into
    a recursive loop or end up with overly verbose output.
    """
    field_names = []

    if not depth:
        return field_names

    opts = dclass._meta

    # Appending a related model's fields to field_names after the
    # non-relational fields will make the output prettier and more organized
    relational_fields = []

    for field in opts.fields:
        if hasattr(field, 'rel') and bool(field.rel):
            # the field is relational
            relational_fields.append((field, field.rel.to))
        elif hasattr(field, 'model') and isinstance(field, RelatedObject):
            # its a related set
            relational_fields.append((field, field.model))
        else:
            field_names.append(field.name)

    # recursively sort out the related fields we saw
    for rfield, klass in relational_fields:
        field_names += map(
            lambda ifield: "{0}__{1}".format(rfield.name, ifield),
            discover_for_class(klass, depth=depth - 1)
        )

    return field_names


def prepend_dtype(search_fields, dtype):
    return map(lambda field: "{0}.{1}".format(dtype, field), search_fields)


def discover_help():
    system_search_fields = discover_for_class(dsearchables['SYS'])
    # get rid of system_rack__location because we don't use it anymore.
    system_search_fields = filter(
        lambda field: "system_rack__location" not in field,
        system_search_fields
    )

    return {
        'SYS': prepend_dtype(system_search_fields, 'sys')
    }


def discover_all():
    base_schema = discover_help()
    for class_name, Klass in searchables:
        if class_name in base_schema:
            continue
        search_fields = discover_for_class(Klass)
        base_schema[class_name] = prepend_dtype(
            search_fields, class_name.lower()
        )
    return base_schema

# Cache the schema so we don't have to recalculate
# HELP_SEARCH_SCHEMA is printed to html
HELP_SEARCH_SCHEMA = discover_help()
# SEACH_SCHEMA is never dumped completely. A use can ask specifically for a
# class' schema and have it be looked up here.
SEARCH_SCHEMA = discover_all()
