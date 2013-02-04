from tastypie.resources import ModelResource
from ..models import Test

class Test_3_1_Resource(ModelResource):
    class Meta:
        resource_name = "test_3_1"
        queryset = Test.objects.all()
        
class Test_3_2_Resource(ModelResource):
    class Meta:
        resource_name = "test_3_2"
        queryset = Test.objects.all()
    
class Test_3_3_Resource(ModelResource):
    class Meta:
        resource_name = "test_3_3"
        queryset = Test.objects.all()