from tastytools.resources import ModelResource
from tastypie import fields
from ..models import Test

class Test_1_1_Resource(ModelResource):
    class Meta:
        resource_name = "test_1_1"
        queryset = Test.objects.all()
        
class Test_1_2_Resource(ModelResource):
    class Meta:
        resource_name = "test_1_2"
        queryset = Test.objects.all()
    
class Test_1_3_Resource(ModelResource):
    class Meta:
        resource_name = "test_1_3"
        queryset = Test.objects.all()