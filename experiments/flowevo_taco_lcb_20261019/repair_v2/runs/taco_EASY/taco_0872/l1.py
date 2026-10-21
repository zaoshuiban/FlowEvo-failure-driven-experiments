def tops(msg):
    result = []
    i = 1
    step = 5
    n = len(msg)

    while i < n:
        result.append(msg[i])
        i += step
        step += 4

    result.reverse()
    return ''.join(result)