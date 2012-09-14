def update_soa(record):
    """This function will attempt to find an SOA associated with an object and
    if it finds an SOA will incremente the serial.
    """
    if record and record.domain and record.domain.soa:
        record.domain.soa.serial += 1
        record.domain.soa.dirty = True
        record.domain.soa.save()
