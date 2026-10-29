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
    if len(operators) != n - 1:
        raise ValueError('operator count mismatch')
    for x in operands:
        if isinstance(x, bool) or not isinstance(x, int):
            raise ValueError('operands must be integers')
        if x < -10 or x > 20:
            raise ValueError('operand out of range')
    for op in operators:
        if op not in ('+', '-', '*'):
            raise ValueError('invalid operator')
    if n == 1:
        return str(1)
    dp = [[None] * n for _ in range(n)]
    for i in range(n):
        dp[i][i] = {operands[i]}
    for length in range(2, n + 1):
        for i in range(0, n - length + 1):
            j = i + length - 1
            vals = set()
            for k in range(i, j):
                op = operators[k]
                left = dp[i][k]
                right = dp[k + 1][j]
                if op == '+':
                    for a in left:
                        for b in right:
                            vals.add(a + b)
                elif op == '-':
                    for a in left:
                        for b in right:
                            vals.add(a - b)
                else:
                    for a in left:
                        for b in right:
                            vals.add(a * b)
            dp[i][j] = vals
    return str(len(dp[0][n - 1]))