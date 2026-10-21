def split_odd_and_even(n):
    s = str(n)
    if not s:
        return []

    result = []
    start = 0
    prev_parity = ord(s[0]) & 1

    for i in range(1, len(s)):
        parity = ord(s[i]) & 1
        if parity != prev_parity:
            result.append(int(s[start:i]))
            start = i
            prev_parity = parity

    result.append(int(s[start:]))
    return result


splitOddAndEven = split_odd_and_even