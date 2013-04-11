from haystack import indexes


class MozdnsIndex(indexes.SearchIndex):
    text = indexes.CharField(document=True, use_template=True)
    fqdn = indexes.CharField(model_attr='fqdn')
    label = indexes.CharField(model_attr='label')

    def index_queryset(self):
        return self.get_model().objects.all()
