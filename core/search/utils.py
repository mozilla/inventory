from django.db.models import Q


def objects_to_Q(query_set):
    """
    Given a sequence (can be empty) containing django ORM objects, calculate a
    Q expression what will return those objects.
    """
    def combine(q, n):
        return q | Q(pk=n.pk)
    return reduce(combine, query_set, Q(pk__lt=-1))
