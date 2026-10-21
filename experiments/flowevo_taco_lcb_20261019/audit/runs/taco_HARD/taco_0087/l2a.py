import sys

def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    t = data[0]
    idx = 1
    answers = []

    for _ in range(t):
        n = data[idx]
        k = data[idx + 1]
        b = data[idx + 2]
        idx += 3

        a = data[idx:idx + n]
        idx += n

        if k == 0:
            ge_b = sum(1 for x in a if x >= b)
            ans = ge_b
            if ge_b < n:
                ans += 1
            answers.append(str(ans))
        else:
            a.sort()
            ans = 1
            last = a[0]

            for x in a[1:]:
                if x >= k * last + b:
                    ans += 1
                    last = x

            answers.append(str(ans))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()