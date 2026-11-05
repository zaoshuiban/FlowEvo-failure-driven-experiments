def solve(parameters):
    n = parameters['n']
    if type(n) is not int or n < 0 or n > 10000:
        raise ValueError('unsupported n')
    return '0'
import re
def match(problem):
    m = re.fullmatch(r'Compute the sum of integers from 1 through ([0-9]+), inclusive\.', problem)
    if not m:
        return {'status':'DECLINE','parameters':{},'reason':'outside explicit fixture grammar','assumption_quotes':[],'requested_quantity':'integer sum'}
    n = int(m.group(1))
    if n > 10000:
        return {'status':'DECLINE','parameters':{},'reason':'resource bound','assumption_quotes':[],'requested_quantity':'integer sum'}
    return {'status':'MATCH','parameters':{'n':n},'reason':'explicit finite sum','assumption_quotes':[problem],'requested_quantity':'integer sum'}

# fixture version 4bca58b677dbcbdbe161e9352289367ad9d86d4efd277cfa26e91786fc715e2c
