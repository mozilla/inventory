from django.db.models import Q

import mozdns
import core
from mozdns.address_record.models import AddressRecord
from mozdns.cname.models import CNAME
from mozdns.domain.models import Domain
from mozdns.mx.models import MX
from mozdns.nameserver.models import Nameserver
from mozdns.ptr.models import PTR
from mozdns.srv.models import SRV
from mozdns.sshfp.models import SSHFP
from core.interface.static_intr.models import StaticInterface
from mozdns.txt.models import TXT

from parser import Parser
from utils import *
from itertools import izip
import pdb


class Compiler(object):
    def __init__(self, stmt):
        self.stmt = stmt
        self.p = Parser(self.stmt)
        self.root_node = self.p.parse()
        self.stack = list(reversed(make_stack(self.root_node)))
        self.q_stack = []

    def compile_Q(self):
        """Compile a q set:
            The idea here is to use two stacks to calcuate the desired query
            set.
        """
        def error_out(token=None):
            if token is None:
                problem = len(self.stmt)
            else:
                problem = token.col

            raise SyntaxError("Expecting Term or Directive at col "
                    "{0}\n{1}\n{2}^".format(problem, self.stmt, problem * ' '))
        first = True
        while True:
            try:
                top = self.stack.pop()
            except IndexError:
                if first:
                    error_out()
                else:
                    break
            first = False

            if istype(top, 'term') or istype(top, 'directive'):
                self.q_stack.append(top.compile_Q())
            elif istype(top, 'uop'):
                try:
                    t1 = self.q_stack.pop()
                except IndexError:
                    error_out()

                q_negate = []
                for qset in t1:
                    q_negate.append(~qset)
                self.q_stack.append(q_negate)
                continue
            elif istype(top, 'bop'):
                try:
                    t1 = self.q_stack.pop()
                except IndexError:
                    error_out(top)

                try:
                    t2 = self.q_stack.pop()
                except IndexError:
                    error_out(top)

                if top.value == 'AND':
                    q_result = []
                    for qi, qj in izip(t1, t2):
                        if qi and qj:
                            q_result.append(qi & qj)
                        else:  # Something AND nothing is nothing
                            q_result.append(None)
                if top.value == 'OR':
                    q_result = []
                    for qi, qj in izip(t1, t2):
                        if qi and qj:
                            q_result.append(qi | qj)
                        elif qi:
                            q_result.append(qi)
                        elif qj:
                            q_result.append(qj)
                        else:
                            q_result.append(None)
                self.q_stack.append(q_result)
                continue

    def get_managers(self):
        # Alphabetical order
        managers = []
        managers.append(AddressRecord.objects.all())
        managers.append(CNAME.objects.all())
        managers.append(Domain.objects.all())
        managers.append(MX.objects.all())
        managers.append(Nameserver.objects.all())
        managers.append(PTR.objects.all())
        managers.append(SRV.objects.all())
        managers.append(SSHFP.objects.all())
        managers.append(StaticInterface.objects.all())
        managers.append(TXT.objects.all())
        return managers

    def compile_json(self):
        """Return a JSON result of a search."""
        search_result = []
        self.q_stack = []
        self.compile_Q()
        for manager, mega_filter in izip(self.get_managers(), self.q_stack[0]):
            if not mega_filter:
                search_result.append(None)
            else:
                search_result.append(mega_filter)
        search_result.append(None)
        # TODO We need to write resources for all misc types
        return search_result

    def compile_search(self):
        search_result = []
        self.q_stack = []
        self.compile_Q()
        for manager, mega_filter in izip(self.get_managers(), self.q_stack[0]):
            if not mega_filter:
                search_result.append([])
            else:
                search_result.append(manager.filter(mega_filter))
        search_result.append([]) # This last list is for misc objects
        return search_result

