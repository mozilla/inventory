from haystack import indexes
from mozdns.mx.models import MX
from mozdns.mozdns_index import MozdnsIndex


class MXIndex(MozdnsIndex, indexes.Indexable):
    server = indexes.CharField(model_attr='server')

    def get_model(self):
        return MX
