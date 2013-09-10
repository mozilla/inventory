__import__('inventory_context')

from user_systems.models import UnmanagedSystemType

new_types = (
    'Office Equipment',
    'Linux Desktop',
    'Linux Laptop',
    'Monitor',
    'AV Equipment',
    'Other Hardware',
)
for new_type in new_types:
    UnmanagedSystemType.objects.create(name=new_type)
