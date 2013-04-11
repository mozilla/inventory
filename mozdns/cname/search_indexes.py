from haystack import indexes
from mozdns.cname.models import CNAME
from mozdns.mozdns_index import MozdnsIndex


class CNAMEIndex(MozdnsIndex, indexes.Indexable):
    data = indexes.CharField(model_attr='data')

    def get_model(self):
        return CNAME
