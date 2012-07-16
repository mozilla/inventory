def get_interfaces_range(start, stop):
    intrs = StaticInterface.objects.filter(ip_upper=0, ip_lower__gte=start,
            ip_lower__lte=end)
