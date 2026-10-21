import sys

MOD = 998244353
INV2 = (MOD + 1) // 2  # modular inverse of 2


def main() -> None:
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    N = int(data[0])
    P = int(data[1])

    invP = pow(P, MOD - 2, MOD)

    ans = []
    expected = 0       # E[S_{i-1}]
    expected_sq = 0    # E[S_{i-1}^2]
    add_value = 1      # 1 / P^(i-1)

    for _ in range(N):
        add_sq = add_value * add_value % MOD

        # E[(S + X * add_value)^2]
        # = E[S^2] + add_value * E[S] + add_value^2 / 2
        expected_sq = (
            expected_sq
            + add_value * expected
            + add_sq * INV2
        ) % MOD

        # E[S + X * add_value] = E[S] + add_value / 2
        expected = (expected + add_value * INV2) % MOD

        ans.append(str(expected_sq))
        add_value = add_value * invP % MOD

    sys.stdout.write(" ".join(ans) + "\n")


if __name__ == "__main__":
    main()