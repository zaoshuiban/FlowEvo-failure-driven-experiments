import sys


def main() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n, m = data[0], data[1]
    a = data[2:2 + n]

    gaps = [0] * n
    for i in range(n - 1):
        gaps[i] = a[i + 1] - a[i]
    gaps[n - 1] = a[0] + m - a[-1]

    pattern = gaps[::-1]

    # Prefix function for KMP
    pi = [0] * n
    for i in range(1, n):
        j = pi[i - 1]
        while j > 0 and pattern[i] != pattern[j]:
            j = pi[j - 1]
        if pattern[i] == pattern[j]:
            j += 1
        pi[i] = j

    answers = []
    j = 0

    # Search reverse(gaps) in gaps + gaps
    for idx in range(2 * n):
        value = gaps[idx] if idx < n else gaps[idx - n]

        while j > 0 and value != pattern[j]:
            j = pi[j - 1]

        if value == pattern[j]:
            j += 1

        if j == n:
            start = idx - n + 1
            if start < n:
                answers.append((a[0] + a[start]) % m)
            j = pi[j - 1]

    answers.sort()
    k = len(answers)

    if k == 0:
        sys.stdout.write("0\n")
    else:
        sys.stdout.write(str(k) + "\n")
        sys.stdout.write(" ".join(map(str, answers)) + "\n")


if __name__ == "__main__":
    main()