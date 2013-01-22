from django.test import TestCase
from core.search.compiler.invparse import build_parser
from core.search.compiler.utils import make_stack


class TestParser(TestCase):
    def compare(self, ss, expected_stack_str):
        parse = build_parser()
        root_node = parse(ss)
        stack = make_stack(root_node)
        actual = ' '.join([n.value for n in stack])
        self.assertEqual(actual, expected_stack_str, msg="Actual: {0} "
                         "Excpected: {1} Parsing: {2}".format(actual,
                         expected_stack_str, ss))

    def test1(self):
        ss = "(a AND (b OR (c d)))"
        exp = 'a b c d AND OR AND'
        self.compare(ss, exp)

    def test2(self):
        ss = "(a AND b)"
        exp = 'a b AND'
        self.compare(ss, exp)

    def test3(self):
        ss = "(a b)"
        exp = 'a b AND'
        self.compare(ss, exp)

    def test4(self):
        ss = "((a b))"
        exp = 'a b AND'
        self.compare(ss, exp)

    def test5(self):
        ss = "((a b) c)"
        exp = 'a b AND c AND'
        self.compare(ss, exp)

    def test6(self):
        ss = "(a (b c))"
        exp = 'a b c AND AND'
        self.compare(ss, exp)

    def test7(self):
        ss = "((a AND (b OR (c d))))"
        exp = 'a b c d AND OR AND'
        self.compare(ss, exp)

    def test8(self):
        ss = "(a AND b OR c AND d)"
        exp = 'a b AND c d AND OR'
        self.compare(ss, exp)

    def test9(self):
        ss = "(a AND (b OR c) AND d)"
        exp = 'a b c OR AND d AND'
        self.compare(ss, exp)

    def test10(self):
        ss = "((a AND (b OR c) AND d))"
        exp = 'a b c OR AND d AND'
        self.compare(ss, exp)

    def test11(self):
        ss = "(a b c)"
        exp = 'a b AND c AND'
        self.compare(ss, exp)

    def test12(self):
        ss = "(a b OR c)"
        exp = 'a b AND c OR'
        self.compare(ss, exp)

    def test24(self):
        ss = "(a OR b c)"
        exp = 'a b c AND OR'
        self.compare(ss, exp)

    def test13(self):
        ss = "(a (b OR c))"
        exp = 'a b c OR AND'
        self.compare(ss, exp)

    def test14(self):
        ss = "((a OR b) c)"
        exp = 'a b OR c AND'
        self.compare(ss, exp)

    def test15(self):
        ss = "(-c)"
        exp = 'c NOT'
        self.compare(ss, exp)

    def test16(self):
        ss = "(-a c)"
        exp = 'a NOT c AND'
        self.compare(ss, exp)

    def test17(self):
        ss = "(-(a c))"
        exp = 'a c AND NOT'
        self.compare(ss, exp)

    def test18(self):
        ss = "a -c"
        exp = 'a c NOT AND'
        self.compare(ss, exp)

    def test19(self):
        ss = "a -(c OR b)"
        exp = 'a c b OR NOT AND'
        self.compare(ss, exp)

    def test20(self):
        ss = "a - c"
        exp = 'a c NOT AND'
        self.compare(ss, exp)

    def test21(self):
        ss = "a -(c OR b)"
        exp = 'a c b OR NOT AND'
        self.compare(ss, exp)

    def test22(self):
        ss = "type=:a -(c OR -b)"
        exp = 'type=:a c b NOT OR NOT AND'
        self.compare(ss, exp)

    def test23(self):
        ss = "a b d OR c f g"
        exp = 'a b AND d AND c f AND g AND OR'
        self.compare(ss, exp)

    def test25(self):
        ss = "foo-bar baz"
        exp = 'foo-bar baz AND'
        self.compare(ss, exp)

    def test26(self):
        ss = "type=:foo.bar -type=:baz"
        exp = 'type=:foo.bar type=:baz NOT AND'
        self.compare(ss, exp)
