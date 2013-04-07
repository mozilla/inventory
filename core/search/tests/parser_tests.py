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
        t = 'aND'
        self.assertTrue(callable(self.parse(t)))


class ORTest(T):
    rule = 'OR'

    def test1(self):
        t = 'OR'
        self.assertTrue(callable(self.parse(t)))

    def test2(self):
        t = 'oR'
        self.assertTrue(callable(self.parse(t)))


class BoolEXPRTest(T):
    rule = 'expr'

    def test1(self):
        t = '8 AND 8'
        out = '(' + t + ')'
        self.assertEqual(out, self.parse(t))

    def test2(self):
        t = '8 8'
        out = '(8 AND 8)'
        self.assertEqual(out, self.parse(t))

    def test3(self):
        t = '8 8 8'
        out = '((8 AND 8) AND 8)'
        self.assertEqual(out, self.parse(t))

    def test4(self):
        t = '8 OR 8 OR 8'
        out = '((8 OR 8) OR 8)'
        self.assertEqual(out, self.parse(t))

    def test5(self):
        t = '8 8 OR 8'
        out = '((8 AND 8) OR 8)'
        self.assertEqual(out, self.parse(t))

    def test6(self):
        t = '8 OR 8 8'
        out = '(8 OR (8 AND 8))'
        self.assertEqual(out, self.parse(t))


class BareNOTTests(T):
    rule = 'value'

    def test1(self):
        t = '!a'
        out = '(NOT a)'
        self.assertEqual(out, self.parse(t))

    def test2(self):
        t = 'a'
        out = 'a'
        self.assertEqual(out, self.parse(t))


class EXPRTests(T):
    rule = 'expr'

    def test1(self):
        t = '!(a b)'
        out = '(NOT (a AND b))'
        self.assertEqual(out, self.parse(t))

    def test2(self):
        t = 'a'
        out = 'a'
        self.assertEqual(out, self.parse(t))

    def test15(self):
        t = "(!c)"
        out = '(NOT c)'
        self.assertEqual(out, self.parse(t))

    def test16(self):
        t = "(!a c)"
        out = '((NOT a) AND c)'
        self.assertEqual(out, self.parse(t))

    def test17(self):
        t = "(!(a c))"
        out = '(NOT (a AND c))'
        self.assertEqual(out, self.parse(t))

    def test18(self):
        t = "a !c"
        out = '(a AND (NOT c))'
        self.assertEqual(out, self.parse(t))

    def test19(self):
        t = "a !(c OR b)"
        out = '(a AND (NOT (c OR b)))'
        self.assertEqual(out, self.parse(t))

    def test20(self):
        t = "a ! c"
        out = '(a AND (NOT c))'
        self.assertEqual(out, self.parse(t))

    def test22(self):
        t = "type=:a !(c OR !b)"
        out = "(('type', 'a') AND (NOT (c OR (NOT b))))"
        self.assertEqual(out, self.parse(t))

    def test23(self):
        t = "a b d OR c f g"
        out = '(((a AND b) AND d) OR ((c AND f) AND g))'
        self.assertEqual(out, self.parse(t))

    def test25(self):
        t = "foo-bar baz"
        out = '(foo-bar AND baz)'
        self.assertEqual(out, self.parse(t))

    def test26(self):
        t = "type=:foo.bar !type=:baz"
        out = "(('type', 'foo.bar') AND (NOT ('type', 'baz')))"
        self.assertEqual(out, self.parse(t))
