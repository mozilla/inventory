from django.test import TestCase
from ometa.runtime import ParseError

from core.search.compiler.invdsl import make_debug_compiler


class T(TestCase):
    def setUp(self):
        self.test_g = make_debug_compiler()

    def parse(self, input_):
        return getattr(self.test_g(input_), self.rule)()

    def fail(self, input_):
        self.assertRaises(ParseError, self.parse, input_)


class DRCTTest(T):
    rule = 'DRCT'

    def test1(self):
        self.assertEqual(('foo', 'bar'), self.parse('foo=:bar'))

    def test2(self):
        lhs = 'foo'
        rhs = '-df:,832kjda_'
        self.assertEqual((lhs, rhs), self.parse('{0}=:{1}'.format(lhs, rhs)))

    def test3(self):
        lhs = 'foo'
        rhs = '-=df:,832kjda_'
        self.fail('{0}=:{1}'.format(lhs, rhs))

    def test4(self):
        self.fail('foo')


class TextTest(T):
    rule = 'TEXT'

    def test1(self):
        t = 'foo'
        self.assertEqual(t, self.parse(t))

    def test11(self):
        t = '11:22::'
        self.assertEqual(t, self.parse(t))

    def test2(self):
        t = '!foo'
        self.fail(t)

    def test3(self):
        t = 'foo=:bar'
        self.fail(t)

    def test4(self):
        t = '!foo'
        self.fail(t)

    def test5(self):
        t = 'foo bar'
        self.fail(t)


class RETest(T):
    rule = 'RE'

    def test1(self):
        t = '/foo'
        self.assertEqual(t[1:], self.parse(t))

    def test2(self):
        t = '/f.[d]{}^oo'
        self.assertEqual(t[1:], self.parse(t))

    def test3(self):
        t = '/foo /bar'
        self.fail(t)


class ANDTest(T):
    rule = 'AND'

    def test1(self):
        t = 'AND'
        self.assertTrue(callable(self.parse(t)))

    def test2(self):
        t = 'AND'
        self.assertTrue(callable(self.parse(t)))


class ORTest(T):
    rule = 'OR'

    def test1(self):
        t = 'OR'
        self.assertTrue(callable(self.parse(t)))

    def test2(self):
        t = 'OR'
        self.assertTrue(callable(self.parse(t)))


class BoolEXPRTest(T):
    rule = 'expr'

    def test1(self):
        t = '8 AND 8'
        out = ('AND', '8', '8')
        self.assertEqual(out, self.parse(t))

    def test2(self):
        t = '8 8'
        out = ('AND', '8', '8')
        self.assertEqual(out, self.parse(t))

    def test3(self):
        t = '8 8 8'
        out = ('AND', ('AND', '8', '8'), '8')
        self.assertEqual(out, self.parse(t))

    def test4(self):
        t = '8 OR 8 OR 8'
        out = ('OR', ('OR', '8', '8'), '8')
        self.assertEqual(out, self.parse(t))

    def test5(self):
        t = '8 8 OR 8'
        out = ('OR', ('AND', '8', '8'), '8')
        self.assertEqual(out, self.parse(t))

    def test6(self):
        t = '8 OR 8 8'
        out = ('OR', '8', ('AND', '8', '8'))
        self.assertEqual(out, self.parse(t))


class BareNOTTests(T):
    rule = 'value'

    def test1(self):
        t = '!a'
        out = ('NOT', 'a')
        self.assertEqual(out, self.parse(t))

    def test2(self):
        t = 'a'
        out = 'a'
        self.assertEqual(out, self.parse(t))


class EXPRTests(T):
    rule = 'expr'

    def test1(self):
        t = '!(a b)'
        out = ('NOT', ('AND', 'a', 'b'))
        self.assertEqual(out, self.parse(t))

    def test2(self):
        t = 'a'
        out = 'a'
        self.assertEqual(out, self.parse(t))

    def test15(self):
        t = "(!c)"
        out = ('NOT', 'c')
        self.assertEqual(out, self.parse(t))

    def test16(self):
        t = "(!a c)"
        out = ('AND', ('NOT', 'a'), 'c')
        self.assertEqual(out, self.parse(t))

    def test17(self):
        t = "(!(a c))"
        out = ('NOT', ('AND', 'a', 'c'))
        self.assertEqual(out, self.parse(t))

    def test18(self):
        t = "a !c"
        out = ('AND', 'a', ('NOT', 'c'))
        self.assertEqual(out, self.parse(t))

    def test19(self):
        t = "a !(c OR b)"
        out = ('AND', 'a', ('NOT', ('OR', 'c', 'b')))
        self.assertEqual(out, self.parse(t))

    def test20(self):
        t = "a ! c"
        out = ('AND', 'a', ('NOT', 'c'))
        self.assertEqual(out, self.parse(t))

    def test22(self):
        t = "type=:a !(c OR !b)"
        out = ('AND', ('type', 'a'), ('NOT', ('OR', 'c', ('NOT', 'b'))))
        self.assertEqual(out, self.parse(t))

    def test23(self):
        t = "a b d OR c f g"
        out = ('OR', ('AND', ('AND', 'a', 'b'), 'd'), ('AND', ('AND', 'c', 'f'), 'g'))  # noqa
        self.assertEqual(out, self.parse(t))

    def test25(self):
        t = "foo-bar baz"
        out = ('AND', 'foo-bar', 'baz')
        self.assertEqual(out, self.parse(t))

    def test26(self):
        t = "type=:foo.bar !type=:baz"
        out = ('AND', ('type', 'foo.bar'), ('NOT', ('=', ('type', 'baz'))))
        self.assertEqual(out, self.parse(t))

    def test26_no_colons(self):
        # like 26 but without the colons
        t = "type=foo.bar !type=baz"
        out = ('AND', ((('=', 'type', None)), 'foo.bar'), ('NOT', (('=', ('type', None)), 'baz')))  # noqa
        self.assertEqual(out, self.parse(t))

    def test27(self):
        t = "mozillaecuador.org OR mozillaecuador.org"
        out = ('OR', 'mozillaecuador.org', 'mozillaecuador.org')
        self.assertEqual(out, self.parse(t))

    def test28(self):
        t = "mozillaecuadOR.org"
        out = "mozillaecuadOR.org"
        self.assertEqual(out, self.parse(t))

    def test29(self):
        t = 'a AND b AND c AND d AND e'
        out = ('AND', 'a', ('AND', 'b', ('AND', 'c', ('AND', 'd', 'e'))))
        self.assertEqual(out, self.parse(t))

    def test30(self):
        t = 'a OR b OR c OR d OR e'
        out = ('OR', ('OR', ('OR', ('OR', 'a', 'b'), 'c'), 'd'), 'e')
        self.assertEqual(out, self.parse(t))

    def test31(self):
        t = 'systems.serial=1234'
        out = (('=', ('systems', 'serial')), '1234')
        self.assertEqual(out, self.parse(t))

    def test32(self):
        t = 'systems.serial~1234'
        out = (('~', ('systems', 'serial')), '1234')
        self.assertEqual(out, self.parse(t))

    def test33(self):
        t = 'systems.serial~"1234 567"'
        out = (('~', ('systems', 'serial')), '1234 567')
        self.assertEqual(out, self.parse(t))

    def test34(self):
        t = 'systems.serial="/1234 567"'
        out = (('~', ('systems', 'serial')), '1234 567')
        self.assertEqual(out, self.parse(t))

    def test34_single_quotes(self):
        t = "systems.serial='/1234 567'"
        out = (('~', ('systems', 'serial')), '1234 567')
        self.assertEqual(out, self.parse(t))

    def test35(self):
        t = 'sys.oob_ip=10.9.3.68'
        out = (('=', ('sys', 'oob_ip')), '10.9.3.68')
        self.assertEqual(out, self.parse(t))

    def test36(self):
        t = 'sys.oob_ip=/^asdf'
        out = (('=', ('sys', 'oob_ip')), '/^asdf')
        self.assertEqual(out, self.parse(t))
