from django import forms
from django.forms import ModelForm
from django.forms.models import construct_instance
from django.core.exceptions import ValidationError


class BaseForm(ModelForm):
    comment = forms.CharField(widget=forms.HiddenInput, required=False)

    def __init__(self, *args, **kwargs):
        super(BaseForm, self).__init__(*args, **kwargs)

        def ttl_helper(o):
            if not o:
                return 'default (SOA minimum)'
            if hasattr(o, 'domain') and o.domain and o.domain.soa:
                return '{0} (click to override)'.format(o.domain.soa.minimum)
            if (hasattr(o, 'reverse_domain') and o.reverse_domain and
                    o.reverse_domain.soa):
                return '{0} (click to override)'.format(
                    o.reverse_domain.soa.minimum
                )
            return 'default (SOA minimum)'

        self.fields['ttl'].widget = forms.TextInput(
            attrs={'placeholder': ttl_helper(self.instance)}
        )

    def save(self, commit=True):
        """
        Saves this ``form``'s cleaned_data into model instance
        ``self.instance``.

        If commit=True, then the changes to ``instance`` will be saved to the
        database. Returns ``instance``.
        """
        if self.instance.pk is None:
            fail_message = 'created'
        else:
            fail_message = 'changed'
        return self.save_instance(
            self.instance, self._meta.fields, fail_message, commit,
            construct=False
        )

    def delete_instance(self, instance):
        instance.delete(call_prune_tree=False)

    # I coppied this form django.forms.models because it's default behavior
    # wasn't calling any sort of validators for m2m objects
    def save_instance(self, instance, fields=None, fail_message='saved',
                      commit=True, exclude=None, construct=True):
        """
        Saves bound Form ``form``'s cleaned_data into model instance
        ``instance``.

        If commit=True, then the changes to ``instance`` will be saved to the
        database. Returns ``instance``.

        If construct=False, assume ``instance`` has already been constructed
        and just needs to be saved.
        """
        if construct:
            instance = construct_instance(self, instance, fields, exclude)
        opts = instance._meta
        if self.errors:
            raise ValueError("the %s could not be %s because the data didn't"
                             " validate." % (opts.object_name, fail_message))

        # wrap up the saving of m2m data as a function.
        def save_m2m(instance):
            cleaned_data = self.cleaned_data
            for f in opts.many_to_many:
                if fields and f.name not in fields:
                    continue
                if f.name in cleaned_data:
                    for validator in f.validators:
                        validator(instance, cleaned_data[f.name])
                    f.save_form_data(instance, cleaned_data[f.name])
        if commit:
            # TODO XXX, why are we not using transactions?
            # if we are committing, save the instance and the m2m data
            # immediately.
            if not instance.pk:
                rollback = True
            else:
                rollback = False
            instance.save()
            try:
                save_m2m(instance)
                # ^-- pass instance so we can validate it's views
            except ValidationError:
                if rollback:
                    self.delete_instance(instance)
                    # we didn't call ensure_label_domain so it's not our
                    # responsibility to call prune_tree
                raise
        else:
            # we're not committing. add a method to the form to allow deferred
            # saving of m2m data.
            self.save_m2m = save_m2m
        return instance
