import sys

def main():
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    n = int(data[0])
    q = int(data[1])

    operations = {}
    idx = 2
    for _ in range(q):
        pair = data[idx]
        result = data[idx + 1]
        idx += 2
        operations[(pair[0], pair[1])] = result[0]

    # dp[c] = number of strings of the current length that reduce to character c
    dp = [1] * 6  # For length 1, each of 'a'...'f' has exactly one string

    for _ in range(2, n + 1):
        ndp = [0] * 6

        for (left, right), result in operations.items():
            left_idx = left - ord('a')
            result_idx = result - ord('a')
            ndp[result_idx] += dp[left_idx]

        dp = ndp

    print(dp[ord('a') - ord('a')])

if __name__ == "__main__":
    main()