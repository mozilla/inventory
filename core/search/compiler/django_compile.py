from itertools import izip

from core.search.compiler.invparse import build_parser
from core.search.compiler.invfilter import BadDirective
from core.search.compiler.utils import make_stack, istype
from core.search.compiler.invfilter import searchables


def compile_to_django(search):
    compiled_qs, error = compile_q_objects(search)
    if error:
        return None, error
    return qs_to_object_map(compiled_qs), ""


def search_type(search, rdtype):
    """A simple wrapper for returning an rdtypes queryset"""
    obj_map, error = compile_to_django(search)
    if error:
        return None, error
    return obj_map[rdtype], None


def compile_q_objects(search):
    """
    This function returns a tuple where the first element is a list of
    unevaluated querysets. If there were errors processing the search string,
    the first element in the tuble is None and the second is a string
    describing the error.
    """
    parse = build_parser()
    try:
        root_node = parse(search)
        exec_stack = list(reversed(make_stack(root_node)))
        qs = compile_Q(exec_stack)[0]  # The first element on the stack is the
                                       # result list
        return qs, None
    except (SyntaxError, BadDirective) as why:
        return None, str(why)


def _compile_q_objects(search):
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


def qs_to_object_map(qs):
    obj_map = {}
    for q, (type_, Klass) in izip(qs, searchables):
        if not q:
            obj_map[type_] = []
        else:
            obj_map[type_] = Klass.objects.filter(q)
    obj_map['misc'] = []
    return obj_map
