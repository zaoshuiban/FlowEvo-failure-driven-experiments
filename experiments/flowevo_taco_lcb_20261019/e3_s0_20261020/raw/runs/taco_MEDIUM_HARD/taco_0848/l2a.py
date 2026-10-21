import sys

def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    t = data[0]
    idx = 1
    ans = []

    for _ in range(t):
        n = data[idx]
        idx += 1

        first_only = 0
        second_only = 0
        both = 0

        for i in range(n):
            value = data[idx + i]

            good_first = (value == i + 1)
            good_second = (value == n - i)

            if not good_first and not good_second:
                both += 1
            elif not good_first:
                first_only += 1
            elif not good_second:
                second_only += 1

        idx += n

        if first_only + both <= second_only:
            ans.append("First")
        elif second_only + both < first_only:
            ans.append("Second")
        else:
            ans.append("Tie")

    sys.stdout.write("\n".join(ans))


if __name__ == "__main__":
    solve()