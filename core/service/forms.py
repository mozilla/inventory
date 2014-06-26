from django import forms

from core.service.models import Service, Dependency

import simplejson as json


class ServiceForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(ServiceForm, self).__init__(*args, **kwargs)

        # Below are a list of fields in the form that will have data
        # autocomplete in them
        autocompletes = [
            'category',
            'business_owner',
            'tech_owner',
            'used_by',
        ]

        # Dynamically load the auto complete data and shove it in a css
        # attribute. Later, javascript will setup JQuery autocomplete.
        for ac in autocompletes:
            data = list(
                Service.objects.all()
                .order_by(ac)
                .distinct()
                .values_list(ac, flat=True)
            )

            try:
                # Don't display the empty value
                data.remove('')
            except ValueError:
                pass

            self.fields[ac].widget.attrs['class'] = 'service-auto-complete'
            self.fields[ac].widget.attrs['data-autocomplete'] = (
                json.dumps(data)
            )

        # Any field that needs to be a chosen-select box should define that
        # here
        self.fields['systems'].widget.attrs['class'] = 'chosen-select'
        self.fields['site'].widget.attrs['class'] = 'chosen-select'
        self.fields['parent_service'].widget.attrs['class'] = 'chosen-select'
        self.fields['depends_on'].widget.attrs['class'] = 'chosen-select'
        self.fields['allocations'].widget.attrs['class'] = (
            'chosen-select service-allocations'
        )

        # exclude thyself from parent service selection
        if self.instance.pk:
            self.fields['parent_service'].queryset = (
                Service.objects.exclude(pk=self.instance.pk)
            )

    class Meta:
        model = Service
        fields = (
            # Plain
            'name',
            'alias',
            'description',

            # Autocompleted fields
            'category',
            'business_owner',
            'tech_owner',
            'used_by',

            # Choice fields
            'usage_frequency',
            'impact',

            # Relational fields
            'allocations',
            'systems',
            'depends_on',
            'parent_service',
            'site',

            # Extra
            'notes',
        )

    # http://stackoverflow.com/a/2264722
    # Need to override how save_m2m works
    def save(self, commit=True):
        super(ServiceForm, self).save(commit=False)

        def save_m2m():
            opts = self.instance._meta
            cleaned_data = self.cleaned_data
            fields = self._meta.fields
            for f in opts.many_to_many:
                if fields and f.name not in fields:
                    continue
                if f.name in cleaned_data:
                    if f.name == 'depends_on':
                        self.instance.depends_on.clear()
                        for service in cleaned_data[f.name]:
                            Dependency.objects.get_or_create(
                                dependant=self.instance, provider=service
                            )
                    else:
                        f.save_form_data(self.instance, cleaned_data[f.name])

        if commit:
            self.instance.save()
            save_m2m()

        return self.instance
