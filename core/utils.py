from django.db.models import Q

import ipaddr
import pdb

def get_interfaces_range(start, stop):
    intrs = StaticInterface.objects.filter(ip_upper=0, ip_lower__gte=start,
            ip_lower__lte=end)

class IPFilterSet(object):
    ipfs = set()

    def add(self, ipf):
        self.ipfs.add(ipf)

    def pprint(self):
        for ipf in self.ipfs:
            print ipf

    def pprint_intersect(self):
        for intersect in self.calc_intersect():
            print intersect

    def calc_intersect(self):
        """
        This is where the magic comes from. Given a list of IPFilter objects,
        figure the ranges that are common to all the IPFilters, and create a
        new list of IPFilter objects that represent this range.
        """

    def compile_OR(self):
        mega_filter = Q()
        for ipf in self.ipfs:
            mega_filter = mega_filter | ipf.compile_q()

    def compile_AND(self):
        """Returns a Q object containing the intersections of all ipfs."""
        if not self.ipfs:
            return Q()
        rx = trim(self.ipfs[0], self.ipfs[1:])
        return rx.compile_q()

    def trim(r, rs, ip_type):
        if not (rs and r):
            return r
        r1 = rs[0]
        rx = intersect(r, r1, ip_type)
        return trim(rx, rs[1:], ip_type)

    def intersect(r1, r2, ip_type):
        """Cases:
            * Subset or equal
            * Left intersect
            * Right intersect
            * No intersect
        """
        if r1.start > r2.end:
            return None
        # We have intersection somewhere.
        if r1.end == r2.end and r1.start == r1.end:
            # r1 is subset of r2
            # Low                   High
            # r1    |---------|
            # r2    |---------|
            # rx    |---------|
            return r1
        if r1.start > r2.start and r1.end < r2.end:
            # r1 is subset of r2
            # Low                   High
            # r1     |-------|
            # r2    |---------|
            # rx    |---------|
            return r1
        if r1.start > r2.start and r1.end > r2.start:
            # Low                   High
            # r1    |---------|
            # r2 |---------|
            # rx    |------|
            return IPFilter(None, ip_type, r1.start_upper, r1.start_lower,
                    r2.end_upper, r2.end_lower)
        if r1.start < r2.start and r1.end < r2.end:
            # Low                   High
            # r1 |---------|
            # r2    |---------|
            # rx    |------|
            return IPFilter(None, ip_type, r2.start_upper, r2.start_lower,
                    r1.end_upper, r1.end_lower)


class IPFilter(object):
    def __init__(self, object_, ip_type, start_upper, start_lower, end_upper, end_lower):
        self.object_ = object_  # The composite object
        self.ip_type = ip_type
        if ip_type == '6':
            self.IPKlass = ipaddr.IPv6Address
        elif ip_type == '4':
            self.IPKlass = ipaddr.IPv4Address
        self.start = self.IPKlass(two_to_one(start_upper, start_lower))
        self.end = self.IPKlass(two_to_one(end_upper, end_lower))
        self.start_upper = start_upper
        self.start_lower = start_lower
        self.end_upper = end_upper
        self.end_lower = end_lower

    def __str__(self):
        return "{0} -- {1}".format(self.start, self.end)

    def __repr__(self):
        return str(self)

    def compile_Q(self):
        q_filter = Q(ip_upper=start_upper, ip_lower__gte=start_lower,
                ip_lower__lte=end_lower)
        return q_filter


def two_to_four(start, end):
    start_upper = start >> 64
    start_lower = start & (1 << 64) - 1
    end_upper = end >> 64
    end_lower = end & (1 << 64) - 1
    return start_upper, start_lower, end_upper, end_lower

def two_to_one(upper, lower):
    return long(upper << 64) + long(lower)

def four_to_two(start_upper, start_lower, end_upper, end_lower):
    start = start_upper << 64 + start_lower
    end = end_upper << 64 + end_lower
    return start, end
