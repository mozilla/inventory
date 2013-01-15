
def validate(obj):
    """
    This function exists so we can do all the highlevel logic of validating
    records in one place. Every DNS record type (except for SOA) should call
    this function. The record's property 'rdtype' will be used to decide which
    validation functions will be called.
    """
