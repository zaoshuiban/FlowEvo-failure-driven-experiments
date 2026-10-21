import sys


def main() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n = data[0]
    m = data[1]
    a = data[2:2 + n]

    # Circular gaps between consecutive elements of the first bag.
    gaps = [0] * n
    for i in range(n - 1):
        gaps[i] = a[i + 1] - a[i]
    gaps[n - 1] = a[0] + m - a[-1]

    # Reflection symmetries correspond to matches of gaps in cyclic reversed(gaps).
    rev = gaps[::-1]
    text = rev + rev[:-1]

    # KMP prefix function for gaps.
    pi = [0] * n
    for i in range(1, n):
        j = pi[i - 1]
        while j > 0 and gaps[i] != gaps[j]:
            j = pi[j - 1]
        if gaps[i] == gaps[j]:
            j += 1
        pi[i] = j

    matches = []
    j = 0
    for idx, value in enumerate(text):
        while j > 0 and value != gaps[j]:
            j = pi[j - 1]
        if value == gaps[j]:
            j += 1

        if j == n:
            start = idx - n + 1
            matches.append(start)
            j = pi[j - 1]

    ans = []
    base = a[0]

    for c in matches:
        jidx = (-c) % n
        ans.append((base + a[jidx]) % m)

    ans.sort()

    out = [str(len(ans))]
    if ans:
        out.append(" ".join(map(str, ans)))

    sys.stdout.write("\n".join(out))


if __name__ == "__main__":
    main()