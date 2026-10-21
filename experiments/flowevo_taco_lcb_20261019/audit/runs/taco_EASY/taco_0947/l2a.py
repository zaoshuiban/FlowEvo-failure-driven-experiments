def split_odd_and_even(n):
    s = str(n)
    result = []
    current = s[0]

    for digit in s[1:]:
        if int(digit) % 2 == int(current[-1]) % 2:
            current += digit
        else:
            result.append(int(current))
            current = digit

    result.append(int(current))
    return result