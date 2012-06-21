from haystack import indexes
from mozdns.soa.models import SOA


class DomainIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    comment = indexes.CharField(model_attr='comment')

    def index_queryset(self):
        return self.get_model().objects.all()

    def get_model(self):
        return SOA
