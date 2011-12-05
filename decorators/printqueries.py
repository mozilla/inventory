""" 
    Print SQL Decorator found at http://pushingkarma.com/notebookdjango-decorator-print-sql-queries/
    Usage:
    @print_queries('metric')
    Where 'metric' is a search filter in the query itself
"""
import os, time

COLORS = {'blue':34, 'cyan':36, 'green':32, 'grey':30, 'magenta':35, 'red':31, 'white':37, 'yellow':33}
RESET = '\033[0m'

def print_queries(filter=None):
    """ Print all queries executed in this funnction. """
    def wrapper1(func):
        def wrapper2(*args, **kwargs):
            from django.db import connection
            sqltime, longest, numshown = 0.0, 0.0, 0
            initqueries = len(connection.queries)
            starttime = time.time()
            result = func(*args, **kwargs)
            for query in connection.queries[initqueries:]:
                sqltime += float(query['time'].strip('[]s'))
                longest = max(longest, float(query['time'].strip('[]s')))
                if not filter or filter in query['sql']:
                    numshown += 1
                    querystr = colored('\n[%ss] ' % query['time'], 'yellow')
                    querystr += colored(query['sql'], 'blue')
                    print querystr
            numqueries = len(connection.queries) - initqueries
            numhidden = numqueries - numshown
            runtime = round(time.time() - starttime, 3)
            proctime = round(runtime - sqltime, 3)
            print colored("------", 'blue')
            print colored('Total Time:  %ss' % runtime, 'yellow')
            print colored('Proc Time:   %ss' % proctime, 'yellow')
            print colored('Query Time:  %ss (longest: %ss)' % (sqltime, longest), 'yellow')
            print colored('Num Queries: %s (%s hidden)\n' % (numqueries, numhidden), 'yellow')
            return result
        return wrapper2
    return wrapper1

def colored(text, color=None):
    """ Colorize text {red, green, yellow, blue, magenta, cyan, white}. """
    if os.getenv('ANSI_COLORS_DISABLED') is None and 1 == 2:
        fmt_str = '\033[%dm%s'
        if color is not None:
            text = fmt_str % (COLORS[color], text)
        text += RESET
    return text
