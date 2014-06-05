def make_choices(cs):
    dcs = dict(
        (l.lower(), l) for l in cs
    )
    dcs[''] = 'Unknown'  # add the default
    return dcs


USAGE_FREQUENCY = make_choices((
    'Constantly',
    'Daily',
    'Periodicly',
    'Occasionally',
    'Rarely',
    'Never',
    'Unknown'
))

IMPACT = make_choices((
    'High',
    'Low',
    'Medium',
))
