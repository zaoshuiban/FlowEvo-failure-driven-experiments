def triangular_sum(n):
    i = 1
    while True:
        t1 = i * (i + 1) // 2
        t2 = (i + 1) * (i + 2) // 2
        total = t1 * t1 + t2 * t2

        if total == n:
            return True
        if total > n:
            return False

        i += 1