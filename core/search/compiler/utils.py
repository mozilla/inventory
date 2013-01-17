def make_stack(node):
    def _make_stack(stack, node):
        if not node:
            return stack
        if (hasattr(node, 'l_child') and hasattr(node, 'r_child')):
            if hasattr(node, 'l_child'):
                _make_stack(stack, node.l_child)
            if hasattr(node, 'r_child'):
                _make_stack(stack, node.r_child)
            stack.append(node)
        else:
            if hasattr(node, 'child'):
                _make_stack(stack, node.child)
                stack.append(node)
            else:
                stack.append(node)
    stack = []
    _make_stack(stack, node)
    return stack


def print_stack(stack):
    print ' '.join([token.value for token in stack])


def istype(a, b):
    if not a:
        return False
    if a.ntype == b:
        return True
    else:
        return False
