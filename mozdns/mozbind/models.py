from django.db import models


class DNSBuildRun(models.Model):
    """
    Everytime the DNS build scripts are ran, one of these objects is
    created to track which zones we have built and which zones we haven't built
    (since nothing has changed in them). :class:`BuildManifest` objects
    relate back to a :class:`DNSBuildRun` instance and represent one zone's
    state.
    """
    log = models.TextField()
    #stats_json = models.JSONField("stats", max_length=max_length)

    def record(self, root_domain, soa, zfiles, zhash):
        bm = BuildManifest(zname=root_domain.name, files=','.join(zfiles),
                           zhash=zhash, build_run=self)
        bm.save()
        return bm

    def stash(self, k, v):
        self.stats_json[k] = v

    def get_manifests(self, **kwargs):
       return BuildManifest.objects.filter(build_run=self, **kwargs)


class BuildManifest(models.Model):
    max_length = 256
    zname = models.CharField(max_length=max_length)
    files = models.CharField(max_length=max_length)
    zhash = models.CharField(max_length=max_length)
    build_run = models.ForeignKey(DNSBuildRun)
    #stats_json = models.JSONField("stats", max_length=max_length)

    def stash(self, k, v):
        self.stats_json[k] = v
