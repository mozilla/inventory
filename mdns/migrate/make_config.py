import sys

"""
Arg 1: zone name
Arg 2: filepath
Arg 3: r or f (reverse of forward)
Arg 4: view
Arg 5: Is the zone namne backwards (for reverse domains
"""

print "\t{"
print "\t\t'path':'{0}',".format(sys.argv[2])
print "\t\t'zone_name': '{0}',".format(sys.argv[1])
print "\t\t'name_reversed': bool('{0}'),".format(sys.argv[5])
print "\t\t'direction': '{0}',".format(sys.argv[3])
print "\t\t'view': '{0}',".format(sys.argv[4])
print "\t\t'relative_path': SYSADMIN_REPO + '{0}',".format("/dnsconfig/")
print "\t},"
