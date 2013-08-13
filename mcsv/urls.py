from django.conf.urls.defaults import url, patterns
from mcsv.views import (
    ajax_csv_exporter, csv_importer, csv_format, ajax_csv_importer
)


urlpatterns = patterns(
    '',
    url(r'^$', csv_importer, name='csv-importer'),
    url(r'^format/$', csv_format, name='csv-format'),
    url(r'^ajax_csv_importer/$', ajax_csv_importer, name='ajax-csv-importer'),
    url(r'^ajax_csv_exporter/$', ajax_csv_exporter, name='ajax-csv-exporter'),
)
