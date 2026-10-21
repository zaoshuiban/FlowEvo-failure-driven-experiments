import sys


def main() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    it = iter(data)

    n = next(it)
    m = next(it)
    l = next(it)

    a = [0] * (n + 1)
    over = [False] * (n + 1)

    runs = 0
    for i in range(1, n + 1):
        a[i] = next(it)
        if a[i] > l:
            over[i] = True
            if i == 1 or not over[i - 1]:
                runs += 1

    answers = []

    for _ in range(m):
        t = next(it)

        if t == 0:
            answers.append(str(runs))
        else:
            p = next(it)
            d = next(it)

            if not over[p]:
                a[p] += d

                if a[p] > l:
                    left = p > 1 and over[p - 1]
                    right = p < n and over[p + 1]

                    runs += 1
                    if left:
                        runs -= 1
                    if right:
                        runs -= 1

                    over[p] = True

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    main()