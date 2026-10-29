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
        raise ValueError('operand count out of range')
    for v in operands:
        if isinstance(v, bool) or not isinstance(v, int):
            raise ValueError('operands must be integers')
        if v < -10 or v > 20:
            raise ValueError('operand out of range')
    if len(operators) != n - 1:
        raise ValueError('operator count mismatch')
    for o in operators:
        if not isinstance(o, str) or o not in ('+', '-', '*'):
            raise ValueError('invalid operator')
    if n == 1:
        return str(1)
    dp = [[None] * n for _ in range(n)]
    for i in range(n):
        dp[i][i] = {operands[i]}
    for length in range(2, n + 1):
        for i in range(0, n - length + 1):
            j = i + length - 1
            cur = set()
            for k in range(i, j):
                left = dp[i][k]
                right = dp[k + 1][j]
                op = operators[k]
                for x in left:
                    for y in right:
                        if op == '+':
                            cur.add(x + y)
                        elif op == '-':
                            cur.add(x - y)
                        else:
                            cur.add(x * y)
            dp[i][j] = cur
    return str(len(dp[0][n - 1]))