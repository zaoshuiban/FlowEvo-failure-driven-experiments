import sys

MOD = 1_000_000_007

def main() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    idx = 0
    n = data[idx]
    idx += 1
    b = data[idx]
    idx += 1

    trust = [0] * (n + 1)
    for i in range(1, n + 1):
        trust[i] = data[idx]
        idx += 1

    q = data[idx]
    idx += 1
    queries = data[idx:idx + q]

    answer = [0] * (n + 1)

    if 1 <= b <= n:
        answer[b] = 1

        # suffix[i] = sum(answer[j] for j from i to b) modulo MOD
        suffix = [0] * (b + 2)
        suffix[b] = 1

        for i in range(b - 1, 0, -1):
            right = i + trust[i]
            if right > b:
                right = b

            if right > i:
                dp = suffix[i + 1] - suffix[right + 1]
                if dp < 0:
                    dp += MOD
            else:
                dp = 0

            answer[i] = dp
            suffix[i] = dp + suffix[i + 1]
            if suffix[i] >= MOD:
                suffix[i] -= MOD

    output = []
    for s in queries:
        if 0 <= s <= n:
            output.append(str(answer[s]))
        else:
            output.append("0")

    sys.stdout.write("\n".join(output))


if __name__ == "__main__":
    main()