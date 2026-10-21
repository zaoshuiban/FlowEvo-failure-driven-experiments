import sys


def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    n, m = data[0], data[1]
    a = data[2:2 + n]

    gaps = [0] * n
    for i in range(n - 1):
        gaps[i] = a[i + 1] - a[i]
    gaps[n - 1] = a[0] + m - a[n - 1]

    # Prefix function for the cyclic gap sequence
    pi = [0] * n
    for i in range(1, n):
        j = pi[i - 1]
        while j > 0 and gaps[i] != gaps[j]:
            j = pi[j - 1]
        if gaps[i] == gaps[j]:
            j += 1
        pi[i] = j

    # Find all reflection symmetries of the cyclic gap sequence.
    # Search gaps in reverse(gaps) + reverse(gaps).
    rev = gaps[::-1]
    text = rev + rev

    axes = []
    matched = 0

    for idx, value in enumerate(text):
        while matched > 0 and value != gaps[matched]:
            matched = pi[matched - 1]

        if value == gaps[matched]:
            matched += 1

        if matched == n:
            start = idx - n + 1
            if start < n:
                axis_index = (-start) % n
                axes.append(axis_index)
            matched = pi[matched - 1]

    base = a[0]
    answer = [(base + a[j]) % m for j in axes]
    answer.sort()

    k = len(answer)
    if k == 0:
        sys.stdout.write("0\n")
    else:
        sys.stdout.write(str(k) + "\n")
        sys.stdout.write(" ".join(map(str, answer)) + "\n")


if __name__ == "__main__":
    main()