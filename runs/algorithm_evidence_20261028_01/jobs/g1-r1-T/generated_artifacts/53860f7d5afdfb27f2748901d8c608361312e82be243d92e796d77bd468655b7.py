def solve(parameters):
    if not isinstance(parameters, dict):
        raise ValueError('parameters must be a dict')
    if set(parameters.keys()) != {'operands', 'operators'}:
        raise ValueError('unexpected keys')
    operands = parameters['operands']
    operators = parameters['operators']
    if not isinstance(operands, list) or not isinstance(operators, list):
        raise ValueError('operands and operators must be lists')
    n = len(operands)
    if n < 1 or n > 8:
        raise ValueError('operands length out of bounds')
    if len(operators) != n - 1:
        raise ValueError('operators length must be len(operands)-1')
    for x in operands:
        if isinstance(x, bool) or not isinstance(x, int):
            raise ValueError('operands must be integers')
        if x < -10 or x > 20:
            raise ValueError('operand out of bounds')
    for op in operators:
        if not isinstance(op, str) or op not in ('+', '-', '*'):
            raise ValueError('invalid operator')
    dp = [[set() for _ in range(n)] for _ in range(n)]
    for i in range(n):
        dp[i][i].add(operands[i])
    for length in range(2, n + 1):
        for i in range(0, n - length + 1):
            j = i + length - 1
            cur = dp[i][j]
            for k in range(i, j):
                op = operators[k]
                left = dp[i][k]
                right = dp[k + 1][j]
                for a in left:
                    for b in right:
                        if op == '+':
                            cur.add(a + b)
                        elif op == '-':
                            cur.add(a - b)
                        else:
                            cur.add(a * b)
    return str(len(dp[0][n - 1]))