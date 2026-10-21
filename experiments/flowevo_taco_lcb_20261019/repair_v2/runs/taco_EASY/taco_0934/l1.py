def shortest_time(speed):
    a, b, c, d = sorted(speed)
    return min(
        a + 3 * b + d,
        2 * a + b + c + d
    )