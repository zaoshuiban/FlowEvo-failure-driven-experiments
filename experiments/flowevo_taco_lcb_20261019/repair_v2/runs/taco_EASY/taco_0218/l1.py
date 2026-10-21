def reg_sum_hits(n, s):
    if n <= 0:
        return [[0, 1]]
    if s == 1:
        return [[n, 1]]
    if n == 1:
        return [[i, 1] for i in range(1, s + 1)]

    max_k = n * (s - 1)
    result = [[n, 1]]

    total = 1
    residue_sums = [0] * s
    residue_sums[0] = 1

    ns = n * s

    for k in range(1, max_k + 1):
        count = (n * total - ns * residue_sums[k % s]) // k
        result.append([n + k, count])

        total += count
        residue_sums[k % s] += count

    return result