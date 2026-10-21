import sys


def int_stream():
    data = sys.stdin.buffer.read()
    num = 0
    in_num = False

    for c in data:
        if c > 32:
            num = num * 10 + (c - 48)
            in_num = True
        elif in_num:
            yield num
            num = 0
            in_num = False

    if in_num:
        yield num


def main() -> None:
    it = int_stream()

    try:
        n = next(it)
    except StopIteration:
        return

    m = next(it)
    a = [next(it) for _ in range(n)]
    del it

    gaps = [0] * n
    for i in range(n - 1):
        gaps[i] = a[i + 1] - a[i]
    gaps[n - 1] = a[0] + m - a[-1]

    pi = [0] * n
    for i in range(1, n):
        j = pi[i - 1]
        while j > 0 and gaps[i] != gaps[j]:
            j = pi[j - 1]
        if gaps[i] == gaps[j]:
            j += 1
        pi[i] = j

    ans = []
    j = 0

    # Search for gaps in cyclic reversed gaps without explicitly building it.
    total_len = 2 * n - 1
    for idx in range(total_len):
        value = gaps[n - 1 - (idx % n)]

        while j > 0 and value != gaps[j]:
            j = pi[j - 1]

        if value == gaps[j]:
            j += 1

        if j == n:
            c = idx - n + 1
            k = (-c) % n
            ans.append((a[0] + a[k]) % m)
            j = pi[n - 1]

    ans.sort()

    if ans:
        sys.stdout.write(str(len(ans)) + "\n")
        sys.stdout.write(" ".join(map(str, ans)) + "\n")
    else:
        sys.stdout.write("0\n")


if __name__ == "__main__":
    main()