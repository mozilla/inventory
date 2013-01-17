from core.utils import start_end_filter, two_to_one
from core.interface.static_intr.models import StaticInterface
from mozdns.address_record.models import AddressRecord
from mozdns.ptr.models import PTR


def range_usage(ip_start, ip_end, ip_type, get_objects=True):
    """This is a magical function."""
    istart, iend, ipf_q = start_end_filter(ip_start, ip_end, ip_type)

    def get_ip(rec):
        return two_to_one(rec.ip_upper, rec.ip_lower)

    lists = [sorted(AddressRecord.objects.filter(ipf_q), key=get_ip),
             sorted(PTR.objects.filter(ipf_q), key=get_ip),
             sorted(StaticInterface.objects.filter(ipf_q), key=get_ip)]

    free_ranges = []

    def cmp_ip_upper_lower(a, b):
        if a.ip_upper > b.ip_upper:
            return a
        elif a.ip_upper < b.ip_upper:
            return b
        elif a.ip_lower > b.ip_lower:
            return a
        elif a.ip_lower < b.ip_lower:
            return b
        else:
            return a

    unused = 0
    minimum_i = 0
    rel_start = int(istart)
    end = int(iend)
    while True:
        if rel_start > end:
            break
        lists = [l for l in lists if l]
        if not lists:
            free_ranges.append((rel_start, end))
            unused += end - rel_start + 1
            break

        min_list = min(lists, key=lambda x: two_to_one(x[0].ip_upper,
                                                       x[0].ip_lower))

        minimum = min_list[0]
        minimum_i = two_to_one(minimum.ip_upper, minimum.ip_lower)
        unused += minimum_i - rel_start
        if minimum_i != rel_start:
            free_ranges.append((rel_start, minimum_i - 1))

        for l in lists:
            while (l and
                    l[0].ip_upper == minimum.ip_upper and
                    l[0].ip_lower == minimum.ip_lower):
                l.pop(0)

        rel_start = minimum_i + 1

    range_usage = {
        'unused': unused,
        'used': int(iend) - int(istart) - unused + 1,
        'free_ranges': free_ranges,
    }

    return range_usage
