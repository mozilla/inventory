from system_api import SystemResource
from systems.models import System
from tastypie.test import ResourceTestCase
class TastySystemTest(ResourceTestCase):

    def setUp(self):
        super(TastySystemTest, self).setUp()

    def create_system(self, host_dict):
        System(**host_dict).save()

    def test1_system_not_exist(self):
        resp = self.api_client.get('/api/v3/system/1/', format='json')
        self.assertEqual(resp.status_code, 404)
 
    def test2_create_system(self):
        data = {'hostname': 'foobar.vlan.dc'}
        resp = self.api_client.post('/en-US/tasty/v3/system/', format='json', data=data)
        self.assertEqual(resp.status_code, 201)

    def test3_get_system_by_id(self):
        self.create_system({'hostname':'foobar.vlan.dc'})
        resp = self.api_client.get('/en-US/tasty/v3/system/2/', format='json')
        self.assertEqual(resp.status_code, 200)


    def test4_get_system_by_hostname(self):
        self.create_system({'hostname':'foobar.vlan.dc'})
        resp = self.api_client.get('/en-US/tasty/v3/system/foobar.vlan.dc/', format='json')
        self.assertEqual(resp.status_code, 200)


    def test5_delete_system_by_id(self):
        self.create_system({'hostname':'foobar.vlan.dc'})
        self.assertEqual(len(System.objects.all()), 1)
        resp = self.api_client.get('/en-US/tasty/v3/system/foobar.vlan.dc/', format='json')
        system_id = self.deserialize(resp)['id']
        resp = self.api_client.delete('/en-US/tasty/v3/system/%i/' % system_id, format='json')
        self.assertEqual(resp.status_code, 204)
        self.assertEqual(len(System.objects.all()), 0)


    def test6_delete_system_by_hostname(self):
        self.create_system({'hostname':'foobar.vlan.dc'})
        self.assertEqual(len(System.objects.all()), 1)
        resp = self.api_client.delete('/en-US/tasty/v3/system/%s/' % 'foobar.vlan.dc', format='json')
        self.assertEqual(resp.status_code, 204)
        self.assertEqual(len(System.objects.all()), 0)
