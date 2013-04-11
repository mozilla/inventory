from django.core.exceptions import ValidationError
import re


mac_match = "^[0-9a-f][0-9a-f]:[0-9a-f][0-9a-f]:[0-9a-f][0-9a-f]:"\
    "[0-9a-f][0-9a-f]:[0-9a-f][0-9a-f]:[0-9a-f][0-9a-f]$"
is_mac = re.compile(mac_match)


def validate_mac(mac):
    mac = mac.lower()
    if not isinstance(mac, basestring):
        raise ValidationError("Mac Address not of valid type.")

    # TODO, I'm drunk. Write a better regex
    if not is_mac.match(mac):
        raise ValidationError("Mac Address not in valid format.")
