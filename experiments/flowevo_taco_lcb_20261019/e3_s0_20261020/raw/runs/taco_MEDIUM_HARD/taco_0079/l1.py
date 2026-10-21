def mix(s1, s2):
    from collections import Counter

    def lowercase_counts(s):
        return Counter(ch for ch in s if 'a' <= ch <= 'z')

    c1 = lowercase_counts(s1)
    c2 = lowercase_counts(s2)

    parts = []

    for ch in 'abcdefghijklmnopqrstuvwxyz':
        n1 = c1.get(ch, 0)
        n2 = c2.get(ch, 0)
        maximum = max(n1, n2)

        if maximum <= 1:
            continue

        if n1 > n2:
            prefix = '1'
        elif n2 > n1:
            prefix = '2'
        else:
            prefix = '='

        parts.append(f"{prefix}:{ch * maximum}")

    parts.sort(key=lambda part: (-len(part), part))
    return '/'.join(parts)