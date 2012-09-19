def make_stack(node):
    def _make_stack(stack, node):
        if not (node.l_child or node.r_child):
            if node.token.value:
                stack.append(node.token)
        else:
            if node.l_child:
                _make_stack(stack, node.l_child)
            if node.r_child:
                _make_stack(stack, node.r_child)
            if node.token.value:
                stack.append(node.token)
    stack = []
    _make_stack(stack, node)
    return stack

def print_stack(stack):
    print ' '.join([token.value for token in stack])

def istype(a, b):
    if not a:
        return False
    if a.type_ == b.title():
        return True
    else:
        return False
