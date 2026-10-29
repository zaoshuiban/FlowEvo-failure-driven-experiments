import math

def solve(parameters):
    if not isinstance(parameters, dict):
        raise ValueError('bad input')
    if set(parameters.keys()) != {'operands', 'operators'}:
        raise ValueError('bad keys')
    operands = parameters['operands']
    operators = parameters['operators']
    if not isinstance(operands, list) or not isinstance(operators, list):
        raise ValueError('bad types')
    n = len(operands)
    if n < 1 or n > 8:
        raise ValueError('bad operand count')
    if len(operators) != n - 1:
        raise ValueError('bad operator count')
    for x in operands:
        if isinstance(x, bool) or not isinstance(x, int):
            raise ValueError('bad operand')
        if x < -10 or x > 20:
            raise ValueError('operand out of range')
    for op in operators:
        if op not in ('+', '-', '*'):
            raise ValueError('bad operator')
    # S[i][j] = set of values for operands[i..j]
    S = [[None] * n for _ in range(n)]
    for i in range(n):
        S[i][i] = {operands[i]}
    for length in range(2, n + 1):
        for i in range(0, n - length + 1):
            j = i + length - 1
            vals = set()
            for k in range(i, j):
                op = operators[k]
                left = S[i][k]
                right = S[k + 1][j]
                for a in left:
                    for b in right:
                        if op == '+':
                            vals.add(a + b)
                        elif op == '-':
                            vals.add(a - b)
                        else:
                            vals.add(a * b)
            S[i][j] = vals
    return str(len(S[0][n - 1]))
