from cyder.cybind.build import *
from django.shortcuts import render_to_response

def sample_build(request):
    DEBUG_BUILD_STRING = ''
    DEBUG_BUILD_STRING += build_forward_zone_files()
    DEBUG_BUILD_STRING += build_reverse_zone_files()
    return render_to_response('sample_build.html', {'data':DEBUG_BUILD_STRING})
