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

    def compile_q(self):
        """Compile a q set:
            The idea here is to use a stack to calcuate the desired query set.
            When you put a term onto the stack, instead of putting the item
            onto the stack
        """
        while True:
            try:
                top = self.stack.pop()
            except IndexError:
                break
            if istype(top, 'term'):
                self.q_stack.append(top.compile_q())
                # TODO ask top to compile it's own q set
            elif istype(top, 'bop'):
                t1 = self.q_stack.pop()
                t2 = self.q_stack.pop()
                if top.value == 'AND':
                    q_result = []
                    for qi, qj in izip(t1, t2):
                        qij = Q()
                        if qi and qj:
                            q_result.append(qi & qj)
                        else:  # Something AND nothing is nothing
                            q_result.append(None)
                if top.value == 'OR':
                    q_result = []
                    for qi, qj in izip(t1, t2):
                        qij = Q()
                        if qi and qj:
                            q_result.append(qi | qj)
                        elif qi:
                            q_result.append(qi)
                        elif qj:
                            q_result.append(qj)
                        else:
                            q_result.append(None)

                self.q_stack.append(q_result)

    def get_managers(self):
        # Alphabetical order
        managers = []
        managers.append(AddressRecord.objects)
        managers.append(CNAME.objects)
        managers.append(Domain.objects)
        managers.append(MX.objects)
        managers.append(Nameserver.objects)
        managers.append(PTR.objects)
        managers.append(SRV.objects)
        managers.append(SSHFP.objects)
        managers.append(StaticInterface.objects)
        managers.append(TXT.objects)
        return managers

    def compile_search(self):
        self.compile_q()
        for manager, mega_filter in izip(self.get_managers(), self.q_stack[0]):
            print manager.filter(mega_filter)

t = Compiler("node106 AND phx")
t.compile_search()
