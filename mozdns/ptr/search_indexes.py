from haystack import indexes
from mozdns.ptr.models import PTR


class PTRIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    name = indexes.CharField(model_attr='name')
    ip_str = indexes.CharField(model_attr='ip_str')

    def index_queryset(self):
        return self.get_model().objects.all()

    def get_model(self):
        return PTR
