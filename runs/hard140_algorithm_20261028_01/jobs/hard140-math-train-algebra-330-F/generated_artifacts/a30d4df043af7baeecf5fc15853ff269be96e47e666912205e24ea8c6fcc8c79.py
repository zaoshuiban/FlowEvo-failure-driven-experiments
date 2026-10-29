import math

def solve(parameters):
    if not isinstance(parameters, dict):
        raise ValueError('parameters must be a dict')
    required = ['outer_coefficient', 'inner_constant', 'inner_coefficient', 'depth']
    for key in required:
        if key not in parameters:
            raise ValueError('missing parameter: ' + key)
    outer_coefficient = parameters['outer_coefficient']
    inner_constant = parameters['inner_constant']
    inner_coefficient = parameters['inner_coefficient']
    depth = parameters['depth']
    for name, val in [('outer_coefficient', outer_coefficient), ('inner_constant', inner_constant), ('inner_coefficient', inner_coefficient), ('depth', depth)]:
        if isinstance(val, bool) or not isinstance(val, int):
            raise ValueError(name + ' must be an integer')
    if depth < 0:
        raise ValueError('depth must be nonnegative')
    if depth > 100000:
        raise ValueError('depth too large')
    value = inner_constant
    for _ in range(depth):
        value = inner_constant + inner_coefficient * value
    result = outer_coefficient * value
    return str(result)

def description():
    return 'Evaluate nested expression outer_coefficient*(inner_constant+inner_coefficient*(...)) with depth nested layers. Start with innermost constant, iterate recurrence value=inner_constant+inner_coefficient*value depth times, multiply by outer_coefficient. Returns integer string. Uncertainty: assumes uniform nesting pattern and exact depth as given.'

def applicability():
    return 'Applies to integer parameters with depth>=0 and depth<=100000. Rejects non-integer or boolean inputs and negative depth. Does not handle non-uniform nesting or non-integer coefficients.'
