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

space = ' '
ws = space*
wss = space+
not_ws = :c ?(c not in (' ', '\t')) -> c
letter = :c ?('a' <= c <= 'z' or 'A' <= c <= 'Z') -> c
special = '_' | '.' | '-' | ':' | ',' | '/'
reg_expr = <(not_ws)+>:r -> r

# Lexical Operators
NOT = '!'
AND = <letter+>:and_ ?(and_ == 'AND') -> self.AND_op()
OR = <letter+>:or_ ?(or_ == 'OR') -> self.OR_op()

# Directive
# =: and = are strictly equal.
# ~ stands for fuzzy
EQ = '=:' | '=' | '~' | '<' | '<=' | '>' | '>='

d_lhs = <letter+>:directive '.' <(letter | '_')+>:attr -> (directive, attr)
        | <letter+>:directive -> (directive, None)

d_rhs_value = letterOrDigit | special | '/'
d_rhs_value_with_ws = d_rhs_value | space
d_rhs = '"' <d_rhs_value_with_ws+>:v '"' -> v
        | "'" <d_rhs_value_with_ws+>:v "'" -> v
        # Match regular exprs. No spaces or quotes allowed
        | '/' reg_expr:v -> '/' + v
        | <d_rhs_value+>:v -> v

DRCT = d_lhs:d EQ:e d_rhs:v -> self.directive(e, d, v)

# Regular Expression
RE = '/' reg_expr:r -> self.regexpr(r)

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
e_and = AND:op wss expr:v -> (op, v)

# x y  <-- Implicit AND
# Only value's are allowed next to implicit ands. You have to be explicit about
# boolean logic if you want to get fancy
i_and = (' '+ ~OR ~AND) value:v -> (self.AND_op(), v)

# x OR y  <-- Explicit OR
e_or = OR:op wss expr_2:v -> (op, v)


# Compile
expr = expr_2:left ws e_or*:right -> self.compile(left, right)
expr_2 = expr_3:left ws e_and*:right -> self.compile(left, right)
expr_3 = value:left i_and*:right -> self.compile(left, right)
"""
