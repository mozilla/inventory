import futures
import requests
import simplejson as json
import time

from slurpee.models import ExternalData
from systems.models import System
from django.db import transaction

from slurpee.constants import P_EXTRA, P_MANAGED

MAX_RETRY = 10


class NoDataReturned(Exception):
    pass


class ForemanFactSlurp(object):
    def __init__(self, session, source, url, fact, ssl_verify,
                 extra_get_params={}):
        self.session = session
        self.ssl_verify = ssl_verify
        self.source = source
        self.fact = fact
        self.fact_name = fact['fact_name']
        self.fact_url = url.format(fact_name=self.fact_name)
        self.params = {
            # MySQL on the pd side can't handle bigger than uint32
            "per_page": (1 << 32) - 1,
            "search": 'name~{0}'.format(self.fact_name)
        }
        self.params.update(extra_get_params)
        self.name = fact['fact_name']  # Default
        if 'policy' in fact:
            # The user has specified an explicit policy to use:
            #   - Build a list containing all full policy names
            #   - See if this fact's policy is in the list of policies
            if fact['policy'] not in [p[0] for p in ExternalData.POLICY_TYPE]:
                raise Exception(
                    "Unkown policy type '{0}'".format(fact['policy'])
                )

            self.policy = fact['policy']

            # Non P_EXTRA and P_MANAGED policy facts must specify an explicit
            # name to use in the UI
            if fact['policy'] not in (P_EXTRA, P_MANAGED):
                try:
                    self.name = fact['name']
                except KeyError:
                    raise Exception(
                        "Non default policy fact '{0}' requires a 'name' in "
                        "its config block".format(self.fact_name)
                    )
        else:
            self.policy = P_EXTRA

    def slurp(self):
        """Reach out to the external source and ask about the fact."""

        print "Asking for fact {0} from {1}".format(
            self.fact['fact_name'], self.fact_url
        )

        retry = 0
        success = False
        # We have tried retry times
        while retry < MAX_RETRY:
            self.resp = self.session.get(
                self.fact_url, params=self.params, verify=self.ssl_verify
            )
            if self.resp.status_code == 200:
                self.data = json.loads(self.resp.content)
                success = True
                break
            retry += 1
            print "Failed to fetch fact. Retrying...."
            time.sleep(1)

        if not success:
            raise Exception(
                "Issues connecting to {0}. Retry is {1}.".format(
                    self.fact_url, MAX_RETRY
                )
            )

        print "[{0} {1}] {2} hosts covered".format(
            self.fact['fact_name'], self.fact_url, len(self.data)
        )
        print "Waiting to be processed..."

    def detect_ambiguous_fact(self, data):
        """Look at the data and make sure our fact_name is occuring in the json
        blobs"""
        if not data:
            return

        if self.fact_name not in data.items()[0][1]:
            raise Exception("Did not find fact '{0}' in {1}".format(
                self.fact_name, data.items()[0]
            ))

    def process(self):
        # Can't do this function in parallel because of Mr. GIL
        self.detect_ambiguous_fact(self.data)
        orm_data = []

        for hostname, value in self.data.iteritems():
            if not hostname:
                continue

            if self.fact_name not in value:
                continue

            try:
                orm_data.append(ExternalData(
                    system=System.objects.get(hostname=hostname),
                    name=self.name,
                    source_name=self.fact_name,
                    data=value[self.fact_name],
                    source=self.source,
                    policy=self.policy
                ))
            except System.DoesNotExist:
                print "Couldn't find system {0}".format(hostname)

        if not orm_data:
            # If no data was returned raise an exception. This should cause the
            # transaction to rollback.
            raise NoDataReturned(
                "No data returned from {0} {1}".format(self.source, self.url)
            )
        ExternalData.objects.bulk_create(orm_data)

        print "Created {0} new datum".format(len(orm_data))
        print "Done!"


def get_future_facts(source, source_url, auth, facts, ssl_verify):
    infra_session = requests.Session()
    infra_session.auth = auth
    return [
        ForemanFactSlurp(infra_session, source, source_url, fact, ssl_verify)
        for fact in facts
    ]


@transaction.commit_on_success
def slurp_puppet_facts(source=None, source_url=None, auth=None, facts=None,
                       ssl_verify=None):
    """
    Spawn N threads for every fact being fetched. Tell N ForemanFactSlurp
    instances to fetch their data, process that data, and then insert the data
    into the ExteriorData table.
    """
    future_facts = get_future_facts(
        source, source_url, auth, facts, ssl_verify
    )

    # Clear everything we saw last time
    ExternalData.objects.filter(source=source).delete()

    with futures.ThreadPoolExecutor(max_workers=len(future_facts)) as executor:
        facts = dict(
            (executor.submit(ff.slurp), ff) for ff in future_facts
        )

        for fact in futures.as_completed(facts):
            # This will can an exception and rollback our delete()
            fact.result()

            facts[fact].process()
