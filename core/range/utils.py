from core.utils import start_end_filter, two_to_one
from core.interface.static_intr.models import StaticInterface
from mozdns.address_record.models import AddressRecord
from mozdns.ptr.models import PTR


def range_usage(ip_start, ip_end, ip_type, get_objects=False):
    """
    :param ip_start: Start ip
    :type ip_start: str
    :param ip_end: End ip
    :type ip_end: str
    :param ip_type: ip type
    :type ip_end: str ('4' or '6')

    Returns ip usage statistics about the range starting at ip_start and
    ending at ip_end.

    Given an inclusive contiguous range of positive integers (IP addresses)
    between `a` and `b` and a list of lists where each sublist contains
    integers (IP addresses) that are within the range, how many integers
    between `a` and `b` do not exist in any of the lists; this is what this
    function calculates.

    For example:

    ```
    Start = 0
    End = 9
    Lists = [[1,2,3], [2,3,4]]
    ```

    The integers that do not occur in `Lists` are `0`, `5`, `6`, `7`, `8`, and
    `9`, so there are 6 integers that do not exist in Lists that satisfy `Start
    <= n <= End`.

    Start can be small and End can be very large (the range may be
    larger than you would want to itterate over). Due to the size of IPv6
    ranges, we should not use recursion.

    There are three types of objects (that we care about) that have IP's
    associated with them: AddressRecord, PTR, StaticInterface. Because we get
    objects back as Queryset's that are hard to merge, we have to do this
    algorithm while retaining all three lists. The gist of the algoritm is as
    follows::

        # Assume the lists are sorted
        while lists:
            note the start number (ip)
            lowest =: of the things in list (PTR, A, INTR), find the lowest
            difference =: start - lowest.ip
            total_free +=: difference
            start =: lowest.ip + 1

            if any PTR, A, or INTR has the same IP as lowest:
                remove those items from their lists
    """

    istart, iend, ipf_q = start_end_filter(ip_start, ip_end, ip_type)

    def get_ip(rec):
        return two_to_one(rec.ip_upper, rec.ip_lower)

    # This should be done in the db
    lists = [sorted(AddressRecord.objects.filter(ipf_q), key=get_ip),
             sorted(PTR.objects.filter(ipf_q), key=get_ip),
             sorted(StaticInterface.objects.filter(ipf_q), key=get_ip)]
    # This should be done in the db
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

        if get_objects:
            objects = ['objects']
        for l in lists:
            while (l and
                    l[0].ip_upper == minimum.ip_upper and
                    l[0].ip_lower == minimum.ip_lower):
                if get_objects:
                    objects.append(l.pop(0))
                else:
                    l.pop(0)
        if get_objects:
            free_ranges.append(objects)

        rel_start = minimum_i + 1

    range_usage = {
        'unused': unused,
        'used': int(iend) - int(istart) - unused + 1,
        'free_ranges': free_ranges,
    }

    return range_usage
