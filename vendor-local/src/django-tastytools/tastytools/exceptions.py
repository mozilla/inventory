class ValidationError(Exception):
    message = "Bad request"
    args = {}

    def __init__(self):
        pass

    def get_dict(self):
        return {
                'name': self.__class__.__name__,
                'message' : self.message,
                'args' : self.args
               }


class MissingField(ValidationError):

    def __init__(self, field_name):
        self.args = {'field_name': field_name}
        self.message = "Bad request, missing field: %s" % field_name
