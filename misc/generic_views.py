from django.views.generic import create_update
from django.core.urlresolvers import reverse

def gen_info_dict(cls):
    return {
        'queryset': cls.objects.all()
    }

def gen_del_dict(cls, redirect):
    return {
        'model': cls,
        'post_delete_redirect': redirect,
    }

def gen_mod_dict(cls, redirect):
    return {
        'model': cls,
        'post_save_redirect': redirect,
    }
    

def delete_object(*args, **kwargs):
    kwargs['post_delete_redirect'] = reverse(kwargs['post_delete_redirect'])
    kwargs['template_name'] = kwargs.get('template_name', 'systems/generic_confirm_delete.html')
    return create_update.delete_object(*args, **kwargs)

def create_object(*args, **kwargs):
    try:
        kwargs['post_save_redirect'] = reverse(kwargs['post_save_redirect'])
    except:
        kwargs['post_save_redirect'] = ['post_save_redirect']
    kwargs['template_name'] = kwargs.get('template_name', 'systems/generic_form.html')
    return create_update.create_object(*args, **kwargs)

def update_object(*args, **kwargs):
    try:
        kwargs['post_save_redirect'] = reverse(kwargs['post_save_redirect'])
    except:
        kwargs['post_save_redirect'] = 'post_save_redirect']
    kwargs['template_name'] = kwargs.get('template_name', 'systems/generic_form.html')
    return create_update.update_object(*args, **kwargs)
