def count_pal(n):
    if n <= 0:
        return [0, 0]

    exact = 9 * 10 ** ((n - 1) // 2)

    if n % 2 == 0:
        total = 2 * (10 ** (n // 2) - 1)
    else:
        total = 11 * 10 ** (n // 2) - 2

    return [exact, total]