from haystack import indexes
from mozdns.nameserver.models import Nameserver


class NameserverIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    server = indexes.CharField(model_attr='server')

    def index_queryset(self):
        return self.get_model().objects.all()

    def get_model(self):
        return Nameserver
