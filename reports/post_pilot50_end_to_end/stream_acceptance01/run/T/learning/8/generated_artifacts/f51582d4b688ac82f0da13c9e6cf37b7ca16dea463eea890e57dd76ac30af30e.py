def solve(parameters):
    n = parameters['n']
    if type(n) is not int or n < 0 or n > 10000:
        raise ValueError('unsupported n')
    return str(n * (n + 1) // 2)
import re
def match(problem):
    m = re.fullmatch(r'Compute the sum of integers from 1 through ([0-9]+), inclusive\.', problem)
    if not m:
        return {'status':'DECLINE','parameters':{},'reason':'outside explicit fixture grammar','assumption_quotes':[],'requested_quantity':'integer sum'}
    n = int(m.group(1))
    if n > 10000:
        return {'status':'DECLINE','parameters':{},'reason':'resource bound','assumption_quotes':[],'requested_quantity':'integer sum'}
    return {'status':'MATCH','parameters':{'n':n},'reason':'explicit finite sum','assumption_quotes':[problem],'requested_quantity':'integer sum'}

# fixture version 54e0d85eeabeef824710f1a31d95ec5e086c48c5e70a47e4781c1fa512c2ab95

def unused():
    x=0
    def inner():
        nonlocal x
        x+=1
        return x
    return inner()
