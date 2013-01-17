from itertools import izip

from core.search.compiler.invparse import build_parser
from core.search.compiler.invfilter import BadDirective
from core.search.compiler.utils import make_stack, istype
from core.search.compiler.invfilter import get_managers, searchables


def compile_to_django(search):
    compiled_qs, error = compile_q_objects(search)
    if error:
        return None, error
    return filter_objects(compiled_qs), ""


def search_type(search, rtype):
    """A simple wrapper for returning an objects Q object."""
    qs, error = compile_q_objects(search)
    if error:
        return None, error
    for t, q in izip(searchables, qs):
        if rtype == t[0]:
            return q, None
    return None, None


def compile_q_objects(search):
    parse = build_parser()
    try:
        root_node = parse(search)
    except (SyntaxError, BadDirective), e:
        return None, str(e)
    exec_stack = list(reversed(make_stack(root_node)))
    qs = compile_Q(exec_stack)[0]
    qs.append([])  # This last list is for misc objects
    return qs, None


def compile_Q(stack):
    q_stack = []
    while True:
        try:
            top = stack.pop()
        except IndexError:
            return q_stack
        if istype(top, 'FILTER'):
            q_stack.append(top.Q)
        elif istype(top, 'NOT'):
            term = q_stack.pop()
            q_stack.append(map(lambda Q: ~Q, term))
            continue
        elif istype(top, 'AND') or istype(top, 'OR'):
            t1 = q_stack.pop()
            t2 = q_stack.pop()
            q_result = []
            for qi, qj in izip(t1, t2):
                if istype(top, 'AND'):
                    if qi and qj:
                        q_result.append(qi & qj)
                    else:  # Something AND nothing is nothing
                        q_result.append(None)
                elif istype(top, 'OR'):
                    if qi and qj:
                        q_result.append(qi | qj)
                    elif qi:
                        q_result.append(qi)
                    elif qj:
                        q_result.append(qj)
                    else:
                        q_result.append(None)
            q_stack.append(q_result)


def filter_objects(qs):
    search_result = []
    for manager, q in izip(get_managers(), qs):
        if not q:
            search_result.append([])
        else:
            search_result.append(manager.filter(q))
    search_result.append([])  # This last list is for misc objects
    return search_result
