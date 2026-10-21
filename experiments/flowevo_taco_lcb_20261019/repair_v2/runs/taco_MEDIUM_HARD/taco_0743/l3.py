import sys

def main() -> None:
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    n = int(data[0])
    p = float(data[1])
    t = int(data[2])

    q = 1.0 - p

    # dp[i] = probability that exactly i people have entered, 0 <= i < n
    dp = [0.0] * n
    dp[0] = 1.0

    # Probability that all n people have already entered
    full = 0.0

    for _ in range(t):
        ndp = [0.0] * n
        new_full = full  # once all n have entered, they stay on the escalator

        for i in range(n):
            prob = dp[i]
            if prob == 0.0:
                continue

            # The front person does not enter
            ndp[i] += prob * q

            # The front person enters
            if i + 1 < n:
                ndp[i + 1] += prob * p
            else:
                new_full += prob * p

        dp = ndp
        full = new_full

    answer = full * n
    for i in range(n):
        answer += i * dp[i]

    print(f"{answer:.15f}")


if __name__ == "__main__":
    main()