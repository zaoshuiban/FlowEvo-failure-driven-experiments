def solve(parameters):
    if not isinstance(parameters, dict):
        raise ValueError('parameters must be an object')
    if set(parameters.keys()) != {'operands', 'operators'}:
        raise ValueError('unexpected keys')
    operands = parameters['operands']
    operators = parameters['operators']
    if not isinstance(operands, list) or not isinstance(operators, list):
        raise ValueError('operands and operators must be lists')
    n = len(operands)
    if n < 1 or n > 8:
        raise ValueError('operand count out of range')
    if len(operators) != n - 1:
        raise ValueError('operator count must be len(operands)-1')
    for v in operands:
        if isinstance(v, bool) or not isinstance(v, int):
            raise ValueError('operands must be integers')
        if v < -10 or v > 20:
            raise ValueError('operand out of range')
    for op in operators:
        if not isinstance(op, str) or op not in ('+', '-', '*'):
            raise ValueError('invalid operator')
    if n == 1:
        return str(1)
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
                for x in left:
                    for y in right:
                        if op == '+':
                            cur.add(x + y)
                        elif op == '-':
                            cur.add(x - y)
                        else:
                            cur.add(x * y)
    return str(len(dp[0][n - 1]))
