from haystack import indexes
from mozdns.domain.models import Domain


class DomainIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    name = indexes.CharField(model_attr='name')

    def index_queryset(self):
        return self.get_model().objects.all()

    def get_model(self):
        return Domain
