def split_odd_and_even(n):
    digits = str(n)
    result = []
    current = digits[0]

    for digit in digits[1:]:
        if int(digit) % 2 == int(current[-1]) % 2:
            current += digit
        else:
            result.append(int(current))
            current = digit

    result.append(int(current))
    return result