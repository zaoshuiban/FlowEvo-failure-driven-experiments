def triangular_sum(n):
    k = 1
    while True:
        a = k * (k + 1) // 2
        b = (k + 1) * (k + 2) // 2
        total = a * a + b * b

        if total == n:
            return True
        if total > n:
            return False

        k += 1