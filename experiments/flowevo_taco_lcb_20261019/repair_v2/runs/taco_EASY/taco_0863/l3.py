import sys

def main():
    data = sys.stdin.read().split()
    if not data:
        return

    n = int(data[0])
    q = int(data[1])

    operations = []
    idx = 2
    for _ in range(q):
        pair = data[idx]
        result = data[idx + 1]
        idx += 2
        operations.append((pair[0], pair[1], result))

    letters = "abcdef"

    # dp[c] = number of strings of the current length that reduce to c
    # For length 1, there is exactly one string for each character.
    dp = {c: 1 for c in letters}

    for _ in range(2, n + 1):
        ndp = {c: 0 for c in letters}

        for first, _, result in operations:
            ndp[result] += dp[first]

        dp = ndp

    print(dp['a'])


if __name__ == "__main__":
    main()