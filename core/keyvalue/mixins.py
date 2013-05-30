class KVUrlMixin(object):
    def get_kv_url(self):
        return '/en-US/core/keyvalue/{0}/{1}/'.format(
            self.keyvalue_set.model.__name__.lower(), self.pk
        )
