def solve(parameters):
    if not isinstance(parameters, dict):
        raise ValueError('parameters must be a dict')
    required = ['num_problems', 'base_score', 'correct_weight', 'wrong_weight', 'lower_bound_exclusive', 'max_score']
    for key in required:
        if key not in parameters:
            raise ValueError('missing parameter: ' + key)
        val = parameters[key]
        if isinstance(val, bool) or not isinstance(val, int):
            raise ValueError('parameter must be an integer: ' + key)
    n = parameters['num_problems']
    b = parameters['base_score']
    a = parameters['correct_weight']
    d = parameters['wrong_weight']
    lo = parameters['lower_bound_exclusive']
    hi = parameters['max_score']
    if n < 0 or n > 10000:
        raise ValueError('num_problems out of supported range')
    if a == d:
        raise ValueError('correct_weight and wrong_weight must differ')
    if hi < lo:
        raise ValueError('max_score must be at least lower_bound_exclusive')
    if hi - lo > 2000000:
        raise ValueError('score range too large')
    def feasible_count(s):
        count = 0
        for c in range(0, n + 1):
            rem = s - b - a * c
            if rem % d != 0:
                continue
            w = rem // d
            if w < 0 or w > n - c:
                continue
            count += 1
            if count > 1:
                return count
        return count
    start = lo + 1
    for s in range(start, hi + 1):
        if feasible_count(s) == 1:
            return str(s)
    raise ValueError('no uniquely decodable score found in range')
