class DisableCSRF(object):
    def process_request(self, request):
        print "ASDF!!!!!!!!!!"
        setattr(request, '_dont_enforce_csrf_checks', True)
