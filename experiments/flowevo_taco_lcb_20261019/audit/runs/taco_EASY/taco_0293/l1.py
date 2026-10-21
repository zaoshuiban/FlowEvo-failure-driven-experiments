import sys

def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    it = iter(data)

    t = next(it)
    answers = []

    for _ in range(t):
        n = next(it)
        a = [next(it) for _ in range(n)]

        even_count = 0
        has_odd = False

        for x in a:
            if x & 1:
                has_odd = True
            else:
                even_count += 1

        if has_odd:
            answers.append(str(even_count))
        else:
            best = 10**18

            for x in a:
                cnt = 0
                while x % 2 == 0:
                    cnt += 1
                    x //= 2
                best = min(best, cnt)

            answers.append(str(n - 1 + best))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()