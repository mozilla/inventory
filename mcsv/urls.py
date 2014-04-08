from django.conf.urls.defaults import url, patterns
from mcsv.views import (
    ajax_csv_exporter, csv_importer, csv_format, ajax_csv_importer,
    ajax_csv_export_classes, ajax_full_csv_exporter, full_csv_exporter
)


urlpatterns = patterns(
    '',
    url(r'^$', csv_importer, name='csv-importer'),
    url(r'^format/$', csv_format, name='csv-format'),
    url(r'^ajax_csv_importer/$', ajax_csv_importer, name='ajax-csv-importer'),
    url(r'^ajax_csv_exporter/$', ajax_csv_exporter, name='ajax-csv-exporter'),
    url(r'^full_exporter/$', full_csv_exporter, name='csv-full-exporter'),  # noqa
    url(r'^ajax_csv_full_exporter/$', ajax_full_csv_exporter, name='ajax-csv-full-exporter'),  # noqa
    url(r'^ajax_csv_full_exporter_classes/$', ajax_csv_export_classes, name='ajax-csv-full-exporter-classes'),  # noqa
)
