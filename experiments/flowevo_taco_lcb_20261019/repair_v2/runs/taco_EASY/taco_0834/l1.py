def bears(x, s):
    pairs = []
    i = 0

    while i < len(s) - 1:
        if (s[i] == 'B' and s[i + 1] == '8') or (s[i] == '8' and s[i + 1] == 'B'):
            pairs.append(s[i])
            pairs.append(s[i + 1])
            i += 2
        else:
            i += 1

    pair_string = ''.join(pairs)
    return [pair_string, len(pairs) // 2 >= x]