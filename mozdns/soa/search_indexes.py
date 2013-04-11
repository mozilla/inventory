from haystack import indexes
from mozdns.soa.models import SOA


class DomainIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    description = indexes.CharField(model_attr='description')

    def index_queryset(self):
        return self.get_model().objects.all()

    def get_model(self):
        return SOA
