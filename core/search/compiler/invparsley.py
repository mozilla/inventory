grammar = """
# http://people.mozilla.com/~juber/public/docs/_build/html/flows.html

# DSL for Inventory
# Grammar base classes should implement the following functions:
#   - directive
#   - regexpr
#   - text
#   - AND_op
#   - OR_op
#   - NOT_op
#   - compile

ws = ' '*
wss = ' '+
not_ws = :c ?(c not in (' ', '\t')) -> c
letter = :c ?('a' <= c <= 'z' or 'A' <= c <= 'Z') -> c
special = '_' | '.' | '-' | ':' | ','

# Lexical Operators
NOT = '!'
AND = <letter+>:and_ ?(and_ == 'AND') -> self.AND_op()
OR = <letter+>:or_ ?(or_ == 'OR') -> self.OR_op()

# Directive
EQ = '=:'
d_lhs = letter | '_'
d_rhs = letterOrDigit | special | '/'
DRCT = <d_lhs+>:d EQ <d_rhs+>:v -> self.directive(d, v)

# Regular Expression
RE = '/' <(not_ws)+>:r -> self.regexpr(r)

# Regular text
text = (~OR ~AND ~NOT <(letterOrDigit | special )+>:t) -> t
TEXT = <text+>:t -> self.text(t)


# DSF (Device Specific Filters)
DSF = DRCT | RE | TEXT

# An atmon
atom = DSF | parens

value = NOT ws atom:a -> self.NOT_op()(a)
        | atom

# Parens
parens = '(' ws expr:e ws ')' -> e

# Operators Precidence
# 1) i_and
# 2) 2_and
# 3) e_or

# x AND y  <-- Explicit AND
e_and = AND:op wss value:v -> (op, v)

# x y  <-- Implicit AND
i_and = (' '+ ~OR ~AND) value:v -> (self.AND_op(), v)

# x OR y  <-- Explicit OR
e_or = OR:op wss expr_2:v -> (op, v)


# Compile
expr = expr_2:left ws e_or*:right -> self.compile(left, right)
expr_2 = expr_3:left ws e_and*:right -> self.compile(left, right)
expr_3 = value:left i_and*:right -> self.compile(left, right)
"""
