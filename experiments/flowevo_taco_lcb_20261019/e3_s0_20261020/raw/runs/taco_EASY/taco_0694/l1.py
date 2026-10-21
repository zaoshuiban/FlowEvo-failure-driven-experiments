def triangular_sum(n):
    k = 1
    while True:
        a = k * (k + 1) // 2
        b = (k + 1) * (k + 2) // 2
        value = a * a + b * b

        if value == n:
            return True
        if value > n:
            return False

        k += 1