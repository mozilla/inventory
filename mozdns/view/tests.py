from django.test import TestCase

from mozdns.view.models import View
from mozdns.domain.models import Domain
from mozdns.ptr.models import PTR
from mozdns.address_record.models import AddressRecord
from systems.tests.utils import create_fake_host
from core.registration.static.models import StaticReg


class ViewTests(TestCase):
    """
    Cases we need to cover.
    1) Give an A/PTR/StaticReg private IP and the private view.
        * clean, save, *no* ValidationError raised

    2) Give an A/PTR/StaticReg private IP and the public view.
        * clean, save, ValidationError raised

    3) Give an A/PTR/StaticReg private IP and the public and private
    view.
        * clean, save, ValidationError raised
    """
    def setUp(self):
        self.o = Domain(name="org")
        self.o.save()
        self.f_o = Domain(name="foo.org")
        self.f_o.save()
        self.s = create_fake_host(hostname="foo.mozilla.com")

        Domain.objects.get_or_create(name="arpa")
        Domain.objects.get_or_create(name="in-addr.arpa")
        Domain.objects.get_or_create(name="10.in-addr.arpa")
        Domain.objects.get_or_create(name="172.in-addr.arpa")
        Domain.objects.get_or_create(name="192.in-addr.arpa")

        self.public, _ = View.objects.get_or_create(name="public")
        self.private, _ = View.objects.get_or_create(name="private")

    def test_private_view_case_1_addr(self):
        a = AddressRecord.objects.create(
            label="asf", domain=self.f_o, ip_str="10.0.0.1", ip_type="4"
        )
        # Object has to exist before views can be assigned.
        a.views.add(self.private)
        a.save()

    def test_private_view_case_1_ptr(self):
        ptr = PTR.objects.create(name="asf", ip_str="10.0.0.1", ip_type="4")
        # Object has to exist before views can be assigned.
        ptr.views.add(self.private)
        ptr.save()

    def test_private_view_case_1_sreg(self):
        sreg = StaticReg.objects.create(
            label="asf", domain=self.f_o, ip_str="10.0.0.1", ip_type="4",
            system=self.s
        )
        # Object has to exist before views can be assigned.
        sreg.views.add(self.private)
        sreg.save()

    def test_private_view_case_2_addr(self):
        a = AddressRecord.objects.create(
            label="asf1", domain=self.f_o, ip_str="10.0.0.1", ip_type="4"
        )
        # Object has to exist before views can be assigned.
        a.views.add(self.public)
        self.assertFalse(a.views.filter(name="public"))

        a = AddressRecord.objects.create(
            label="asf1", domain=self.f_o, ip_str="172.30.0.1", ip_type="4"
        )
        # Object has to exist before views can be assigned.
        a.views.add(self.public)
        self.assertFalse(a.views.filter(name="public"))

        a = AddressRecord.objects.create(
            label="asf1", domain=self.f_o, ip_str="192.168.0.1", ip_type="4"
        )
        # Object has to exist before views can be assigned.
        a.views.add(self.public)
        self.assertFalse(a.views.filter(name="public"))

    def test_private_view_case_2_ptr(self):
        ptr = PTR.objects.create(name="asf", ip_str="10.0.0.2", ip_type="4")
        # Object has to exist before views can be assigned.
        ptr.views.add(self.public)
        self.assertFalse(ptr.views.filter(name="public"))

        ptr = PTR.objects.create(name="asf", ip_str="172.16.0.1", ip_type="4")
        # Object has to exist before views can be assigned.
        ptr.views.add(self.public)
        self.assertFalse(ptr.views.filter(name="public"))

        ptr = PTR.objects.create(name="asf", ip_str="192.168.2.3", ip_type="4")
        # Object has to exist before views can be assigned.
        ptr.views.add(self.public)
        self.assertFalse(ptr.views.filter(name="public"))

    def test_private_view_case_2_sreg(self):
        sreg = StaticReg.objects.create(
            label="asf", domain=self.f_o, ip_str="10.0.0.1", ip_type="4",
            system=self.s
        )
        # Object has to exist before views can be assigned.
        sreg.views.add(self.public)
        self.assertFalse(sreg.views.filter(name="public"))

        sreg = StaticReg.objects.create(
            label="asf", domain=self.f_o, ip_str="172.31.255.254",
            ip_type="4", system=self.s
        )
        # Object has to exist before views can be assigned.
        sreg.views.add(self.public)
        self.assertFalse(sreg.views.filter(name="public"))

        sreg = StaticReg.objects.create(
            label="asf", domain=self.f_o, ip_str="192.168.255.254",
            ip_type="4", system=self.s
        )
        # Object has to exist before views can be assigned.
        sreg.views.add(self.public)
        self.assertFalse(sreg.views.filter(name="public"))

    def test_private_view_case_3_addr(self):
        a = AddressRecord.objects.create(
            label="asf3", domain=self.f_o, ip_str="10.0.0.1", ip_type="4"
        )
        a.views.add(self.private)
        a.save()
        # Object has to exist before views can be assigned.
        a.views.add(self.public)
        self.assertFalse(a.views.filter(name="public"))

        a = AddressRecord.objects.create(
            label="asf3", domain=self.f_o, ip_str="172.30.0.1", ip_type="4"
        )
        a.views.add(self.private)
        a.save()
        # Object has to exist before views can be assigned.
        a.views.add(self.public)
        self.assertFalse(a.views.filter(name="public"))

        a = AddressRecord.objects.create(
            label="asf3", domain=self.f_o, ip_str="192.168.0.1", ip_type="4"
        )
        a.views.add(self.private)
        a.save()
        # Object has to exist before views can be assigned.
        a.views.add(self.public)
        self.assertFalse(a.views.filter(name="public"))

    def test_private_view_case_3_ptr(self):
        ptr = PTR.objects.create(name="asf3", ip_str="10.0.0.2", ip_type="4")
        ptr.views.add(self.private)
        ptr.save()
        # Object has to exist before views can be assigned.
        ptr.views.add(self.public)
        self.assertFalse(ptr.views.filter(name="public"))

        ptr = PTR.objects.create(name="asf3", ip_str="172.16.0.1", ip_type="4")
        ptr.views.add(self.private)
        ptr.save()
        # Object has to exist before views can be assigned.
        ptr.views.add(self.public)
        self.assertFalse(ptr.views.filter(name="public"))

        ptr = PTR.objects.create(name="asf3", ip_str="192.168.2.3",
                                 ip_type="4")
        ptr.views.add(self.private)
        ptr.save()
        # Object has to exist before views can be assigned.
        ptr.views.add(self.public)
        self.assertFalse(ptr.views.filter(name="public"))

    def test_private_view_case_3_sreg(self):
        sreg = StaticReg.objects.create(
            label="asf3", domain=self.f_o, ip_str="10.0.0.1",
            ip_type="4", system=self.s
        )
        sreg.views.add(self.private)
        sreg.save()
        # Object has to exist before views can be assigned.
        sreg.views.add(self.public)
        self.assertFalse(sreg.views.filter(name="public"))

        sreg = StaticReg.objects.create(
            label="asf3", domain=self.f_o, ip_str="172.31.255.254",
            ip_type="4", system=self.s)
        sreg.views.add(self.private)
        sreg.save()
        # Object has to exist before views can be assigned.
        sreg.views.add(self.public)
        self.assertFalse(sreg.views.filter(name="public"))

        sreg = StaticReg.objects.create(
            label="asf3", domain=self.f_o, ip_str="192.168.255.254",
            ip_type="4", system=self.s
        )
        sreg.views.add(self.private)
        sreg.save()
        # Object has to exist before views can be assigned.
        sreg.views.add(self.public)
        self.assertFalse(sreg.views.filter(name="public"))
