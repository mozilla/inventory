from django.test import TransactionTestCase
from tastypie.serializers import Serializer
from tastypie.test import TestApiClient, ResourceTestCase


class ResourceTransactionTestCase(TransactionTestCase):
    """
    A hack to get something that behaves like ResourceTestCase but
    subclasses TransactionTestCase
    """
    def __init__(self, *args, **kwargs):
        super(ResourceTransactionTestCase, self).__init__(*args, **kwargs)
        for attr, value in ResourceTestCase.__dict__.items():
            if (callable(value) and not attr.startswith('_') and
                    attr != 'setUp'):
                setattr(ResourceTransactionTestCase, attr, value)

    def setUp(self):
        super(ResourceTransactionTestCase, self).setUp()
        self.serializer = Serializer()
        self.api_client = TestApiClient()
