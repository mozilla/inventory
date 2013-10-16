from django.core.exceptions import ValidationError
import re


is_mac = re.compile('^([0-9a-fA-F]{2}(:|$)){6}$')


def validate_mac(mac):
    """
    Validates a mac address. If the mac is in the form XX-XX-XX-XX-XX-XX this
    function will replace all '-' with ':'.

    :param mac: The mac address
    :type mac: str
    :returns: The valid mac address.
    :raises: ValidationError
    """
    if not is_mac.match(mac):
        raise ValidationError(
            "Mac Address {0} is not in valid format".format(mac)
        )
    return mac


valid_sreg_name_formats = [
    re.compile("^(mgmt|nic)\d+$"),
]

valid_hw_name_formats = [
    re.compile("^hw\d+$"),
]


def validate_hw_name(name):
    validate_name(
        valid_hw_name_formats, name,
        "Not in valid format. Try something like hw0."
    )


def validate_sreg_name(name):
    validate_name(
        valid_sreg_name_formats, name,
        "Not in valid format. Try something like nic0 or mgmt0."
    )


def validate_name(formats, name, error_msg):
    for f in formats:
        if f.match(name):
            return
    raise ValidationError(error_msg)


def validate_site_name(name):
    if not name:
        raise ValidationError("A site name must be non empty.")
    if name.find(' ') > 0:
        raise ValidationError("A site name must not contain spaces.")
    if name.find('.') > 0:
        raise ValidationError("A site name must not contain a period.")
