def find_lowest_int(k):
    n = 9
    step = 9 * k
    a = step  # a = k * n

    while True:
        if sorted(str(a)) == sorted(str(a + n)):
            return n
        n += 9
        a += step