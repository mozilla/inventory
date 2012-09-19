import unittest
from parser import Parser
from utils import *

class TestParser(unittest.TestCase):
    def compare(self, ss, expected_stack_str):
        p = Parser(ss)
        root_node = p.parse()
        stack = make_stack(root_node)
        actual =  ' '.join([token.value for token in stack])
        self.assertEqual(actual, expected_stack_str, msg="Actual: {0} != "
                "Excpected:{1} Parsing: {2}".format(actual, expected_stack_str,
                    ss))
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
        exp = 'a b c OR d AND AND'
        self.compare(ss, exp)

    def test10(self):
        ss = "((a AND (b OR c) AND d))"
        exp = 'a b c OR d AND AND'
        self.compare(ss, exp)

    def test11(self):
        ss = "(a b c)"
        exp = 'a b c AND AND'
        self.compare(ss, exp)

    def test12(self):
        ss = "(a b OR c)"
        exp = 'a b AND c OR'
        self.compare(ss, exp)

    def test13(self):
        ss = "(a (b OR c))"
        exp = 'a b c OR AND'
        self.compare(ss, exp)

    def test14(self):
        ss = "((a OR b) c)"
        exp = 'a b OR c AND'
        self.compare(ss, exp)


if __name__ == "__main__":
    unittest.main()
