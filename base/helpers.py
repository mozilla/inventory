import jingo


@jingo.register.filter
def url(view_name, *args, **kwargs):
    from django.core.urlresolvers import reverse, NoReverseMatch
    try:
        return reverse(view_name, args=args, kwargs=kwargs)
    except NoReverseMatch:
        try:
            project_name = 'inventory'
            return reverse(project_name + '.' + view_name,
                           args=args, kwargs=kwargs)
        except NoReverseMatch:
            return ''
