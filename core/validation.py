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


valid_name_formats = [
    re.compile("^(nic\d+(\.\d+)?)$"),
    re.compile("^(eth\d+(\.\d+)?)$"),
    re.compile("^(bond\d+(\.\d+)?)$"),
    re.compile("^(mgmt\d+(\.\d+)?)$"),
]


def validate_intrerface_name(name):
    # TODO ^ fix that regex, he was drunk.
    for f in valid_name_formats:
        if f.match(name):
            return
    raise ValidationError(
        "Not in valid format. Try something like eth0 or eth1."
    )


def validate_site_name(name):
    if not name:
        raise ValidationError("A site name must be non empty.")
    if name.find(' ') > 0:
        raise ValidationError("A site name must not contain spaces.")
    if name.find('.') > 0:
        raise ValidationError("A site name must not contain a period.")
