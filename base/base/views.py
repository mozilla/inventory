from django.contrib import messages
from django.forms import ValidationError
from django.db import IntegrityError
from django.shortcuts import redirect, render, get_object_or_404
from django.views.generic import DeleteView
from django.views.generic import DetailView
from django.views.generic import CreateView
from django.views.generic import UpdateView
from django.views.generic import ListView


class BaseListView(ListView):
    """
    Inherit ListView to specify our pagination.
    """
    template_name = 'list.html'
    paginate_by = 200


class BaseDetailView(DetailView):
    template_name = 'detail.html'
    extra_context = None

    def get_context_data(self, **kwargs):

        context = super(DetailView, self).get_context_data(**kwargs)
        context['form_title'] = "{0} Details".format(
            self.form_class.Meta.model.__name__
        )

        # extra_context takes precedence over original values in context
        if self.extra_context:
            context = dict(context.items() + self.extra_context.items())
        return context


class BaseCreateView(CreateView):
    template_name = "form.html"
    extra_context = None

    def post(self, request, *args, **kwargs):
        try:
            obj = super(BaseCreateView, self).post(request, *args, **kwargs)

        # redirect back to form if errors
        except (IntegrityError, ValidationError), e:
            messages.error(request, str(e))
            request.method = 'GET'
            return super(BaseCreateView, self).get(request, *args, **kwargs)

        return obj

    def get(self, request, *args, **kwargs):
        return super(BaseCreateView, self).get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(CreateView, self).get_context_data(**kwargs)
        context['form_title'] = "Create {0}".format(
            self.form_class.Meta.model.__name__
        )

        # extra_context takes precedence over original values in context
        if self.extra_context:
            context = dict(context.items() + self.extra_context.items())
        return context


class BaseUpdateView(UpdateView):
    template_name = "form.html"
    extra_context = None

    def __init__(self, *args, **kwargs):
        super(UpdateView, self).__init__(*args, **kwargs)

    def get_form(self, form_class):
        form = super(BaseUpdateView, self).get_form(form_class)
        return form

    def post(self, request, *args, **kwargs):
        try:
            obj = super(BaseUpdateView, self).post(request, *args, **kwargs)

        except ValidationError, e:
            messages.error(request, str(e))
            request.method = 'GET'
            return super(BaseUpdateView, self).get(request, *args, **kwargs)

        return obj

    def get(self, request, *args, **kwargs):
        return super(BaseUpdateView, self).get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        """
        Add extra template variables such as form title
        """
        context = super(UpdateView, self).get_context_data(**kwargs)
        context['form_title'] = "Update {0}".format(
            self.form_class.Meta.model.__name__
        )

        # extra_context takes precedence over original values in context
        if self.extra_context:
            context = dict(context.items() + self.extra_context.items())
        return context


class BaseDeleteView(DeleteView):
    template_name = 'confirm_delete.html'
    success_url = '/'

    def get_object(self, queryset=None):
        obj = super(BaseDeleteView, self).get_object()
        return obj

    def delete(self, request, *args, **kwargs):
        # Get the object to delete
        obj = get_object_or_404(self.form_class.Meta.model,
                                pk= kwargs.get('pk', 0))

        try:
            view = super(BaseDeleteView, self).delete(request, *args, **kwargs)
        except ValidationError, e:
            messages.error(request, "Error: {0}".format(' '.join(e.messages)))
            return redirect(obj)

        messages.success(request, "Deletion Successful")
        return view


class Base(DetailView):
    def get(self, request, *args, **kwargs):
        return render(request, "base.html")
