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

# fixture version bd9230b7b2d9bdd725cc6968f36d5504fb6f029b7c7f5fbf286c707862a64e2c
