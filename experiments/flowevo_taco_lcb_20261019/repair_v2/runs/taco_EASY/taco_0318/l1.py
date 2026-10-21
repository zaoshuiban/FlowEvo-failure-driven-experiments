import sys


def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    idx = 0
    t = data[idx]
    idx += 1

    answers = []

    for _ in range(t):
        n = data[idx]
        idx += 1

        cnt = [0] * (n + 1)

        for _ in range(n):
            x = data[idx]
            idx += 1

            while x > n:
                x //= 2

            cnt[x] += 1

        for value in range(n, 0, -1):
            while cnt[value] > 1:
                cnt[value] -= 1
                cnt[value // 2] += 1

        ok = all(cnt[i] == 1 for i in range(1, n + 1))
        answers.append("YES" if ok else "NO")

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()