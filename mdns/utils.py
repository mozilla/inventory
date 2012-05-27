INV_URL = "https://inventory.mozilla.org/en-US/"

def print_system(system):
    return "{0} ({1}/systems/edit/{2}/)".format(system, INV_URL, system.pk)
