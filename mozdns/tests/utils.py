import random
import string

from mozdns.create_zone.views import create_zone_ajax
from django.test import RequestFactory


# TODO This should be used everywhere

def get_post_data(random_str, suffix):
    """Return a valid set of data"""
    return {
        'root_domain': '{0}{1}'.format(random_str, suffix),
        'soa_primary': 'ns1.mozilla.com',
        'soa_contact': 'noc.mozilla.com',
        'nameserver_1': 'ns1.mozilla.com',
        'ttl_1': '1234'
    }


def create_fake_zone(random_str, suffix=".mozilla.com"):
    factory = RequestFactory()
    post_data = get_post_data(random_str, suffix=suffix)
    request = factory.post("/dont/matter", post_data)
    create_zone_ajax(request)
    from mozdns.domain.models import Domain
    return Domain.objects.get(name=post_data['root_domain'])


def random_label():
    """
    Utility function to generate a random *valid* label.
    """
    label = ''
    for i in range(random.randint(5, 30)):
        label += string.letters[random.randint(0, len(string.letters) - 1)]
    return label


def random_byte():
    """
    Utility function to generate a random byte for random IPs
    """
    return random.randint(1, 255)
