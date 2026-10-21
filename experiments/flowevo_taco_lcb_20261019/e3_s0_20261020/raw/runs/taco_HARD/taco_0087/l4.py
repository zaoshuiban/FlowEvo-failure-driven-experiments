import sys
from bisect import bisect_right


def main() -> None:
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
            high = 0
            for x in a:
                if x >= b:
                    high += 1

            low = n - high
            ans = high + (1 if low > 0 else 0)
            answers.append(str(ans))
            continue

        a.sort()

        values = []
        for x in a:
            if not values or values[-1] != x:
                values.append(x)

        m = len(values)
        tree = [0] * (m + 1)

        ans = 0
        pos = 0
        last = None

        for x in a:
            if x != last:
                pos += 1
                last = x

            threshold = (x - b) // k
            query_pos = bisect_right(values, threshold)

            best = 0
            i = query_pos
            while i > 0:
                if tree[i] > best:
                    best = tree[i]
                i -= i & -i

            dp = best + 1
            if dp > ans:
                ans = dp

            i = pos
            while i <= m:
                if tree[i] < dp:
                    tree[i] = dp
                i += i & -i

        answers.append(str(ans))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    main()