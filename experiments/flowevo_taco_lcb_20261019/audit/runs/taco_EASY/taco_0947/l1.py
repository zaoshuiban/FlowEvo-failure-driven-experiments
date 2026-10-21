def split_odd_and_even(n):
    s = str(n)
    result = []
    current = s[0]

    for i in range(1, len(s)):
        if int(s[i]) % 2 == int(s[i - 1]) % 2:
            current += s[i]
        else:
            result.append(int(current))
            current = s[i]

    result.append(int(current))
    return result