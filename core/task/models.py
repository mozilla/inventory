from django.db import models


class DNSIncrementalManager(models.Manager):
    def get_query_set(self):
        return super(DNSIncrementalManager, self).get_query_set().filter(ttype='dns-incremental')  # noqa


class DNSFullManager(models.Manager):
    def get_query_set(self):
        return super(DNSFullManager, self).get_query_set().filter(ttype='dns-full')  # noqa


class Task(models.Model):
    task = models.CharField(max_length=255, blank=False)
    ttype = models.CharField(max_length=255, blank=False)

    objects = models.Manager()
    dns_incremental = DNSIncrementalManager()
    dns_full = DNSFullManager()

    @classmethod
    def schedule_zone_rebuild(cls, soa):
        """
        Schedules a rebuild that only changes zone file contents and *not*
        config contents. Operations that can not possibly change the precense
        of a zone statement in the config file should use this rebuild type.
        """
        Task(task=str(soa.pk), ttype='dns-incremental').save()

    @classmethod
    def schedule_all_dns_rebuild(cls, soa):
        """
        Schedules a rebuild for a zone and also regenerates the global zone
        config. This type of rebiuld is reserved for operations  that would
        cause a zone to be removed or added to any config file.
        """
        Task(task=str(soa.pk), ttype='dns-full').save()

    def __repr__(self):
        return "<Task: {0}>".format(self)

    def __str__(self):
        return "{0} {1}".format(self.ttype, self.task)

    def save(self):
        super(Task, self).save()

    class Meta:
        db_table = u'task'
        ordering = ['task']
