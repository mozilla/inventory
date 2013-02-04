from tastypie.validation import Validation
from tastytools.exceptions import ValidationError, MissingField


class FieldsValidation(Validation):

    def __init__(self, required=None, validated=None, **kwargs):
        if required is None:
            required = []

        if validated is None:
            validated = []

        all_methods = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']

        self.required_fields = {}
        self.validated_fields = {}

        dicts = {'required': self.required_fields,
                 'validated': self.validated_fields}

        self.map_method_validations(self.required_fields,
            required, all_methods)
        self.map_method_validations(self.validated_fields,
            validated, all_methods)

        for key, value in kwargs.items():
            for arr_name in ['required', 'validated']:
                if key[:len(arr_name)] == arr_name:
                    methods = self.parse_methods_key(key, arr_name)
                    self.map_method_validations(dicts[arr_name],
                        value, methods)

        Validation.__init__(self)

    def parse_methods_key(self, key, prefix):
        prefix_len = len(prefix) + 1  # prefix + underscore
        methods = key[prefix_len:].split('_')
        return [method.upper() for method in methods]

    def map_method_validations(self, target_dict, fields_to_add, methods):
        for method in methods:
            res_fields = target_dict.setdefault(method, [])
            for field in fields_to_add:
                res_fields.append(field)

    def is_valid(self, bundle, request):
        if not bundle.data:
            return {'__all__': 'Missing data.'}

        required_errors = self.validate_required(bundle, request)
        validation_errors = self.validate_fields(bundle, request)

        errors = required_errors + validation_errors

        if errors:
            return {'errors' : errors}
        return {}

    def validate_fields(self, bundle, request=None):
        errors = []
        for field in self.validated_fields[request.method]:
            validation_func = getattr(self, '%s_is_valid' % field)
            try:
                validation_func(bundle.data.get(field, None), bundle, request)
            except ValidationError, error:
                errors.append(error.get_dict())
        return errors

    def validate_required(self, bundle, request=None):
        errors = []
        for required_field in self.required_fields[request.method]:
            if required_field not in bundle.data:
                error = MissingField(field_name=required_field)
                errors.append(error.get_dict())
        return errors

    @staticmethod
    def uri_to_pk(uri):
        if uri is None:
            return None

        # convert everything to lists
        multiple = not isinstance(uri, basestring)
        uris = uri if multiple else [uri]

        # handle all passed URIs
        converted = []
        for one_uri in uris:
            try:
                # hopefully /api/v1/<resource_name>/<pk>/
                converted.append(int(one_uri.split('/')[-2]))
            except (IndexError, ValueError):
                raise ValueError("URI %s could not be converted to PK integer." % one_uri)
            # convert back to original format
        return converted if multiple else converted[0]
