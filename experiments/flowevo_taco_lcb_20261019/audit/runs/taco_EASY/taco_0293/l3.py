import sys

def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    t = data[0]
    idx = 1
    answers = []
    INF = 10**18

    for _ in range(t):
        n = data[idx]
        idx += 1

        even_count = 0
        min_v2 = INF

        for _ in range(n):
            x = data[idx]
            idx += 1

            if x % 2 == 0:
                even_count += 1

                v2 = 0
                while x % 2 == 0:
                    x //= 2
                    v2 += 1

                if v2 < min_v2:
                    min_v2 = v2

        if even_count == 0:
            answers.append("0")
        elif even_count < n:
            answers.append(str(even_count))
        else:
            answers.append(str(min_v2 + n - 1))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()