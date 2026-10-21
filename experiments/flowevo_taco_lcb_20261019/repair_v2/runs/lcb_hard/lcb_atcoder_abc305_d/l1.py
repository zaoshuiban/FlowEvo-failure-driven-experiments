import sys
import bisect

def main():
    data = list(map(int, sys.stdin.buffer.read().split()))
    it = iter(data)

    N = next(it)
    A = [next(it) for _ in range(N)]

    starts = []
    ends = []
    prefix = [0]

    for i in range(1, N, 2):
        s = A[i]
        e = A[i + 1]
        starts.append(s)
        ends.append(e)
        prefix.append(prefix[-1] + (e - s))

    m = len(starts)

    def slept_until(x):
        # Total sleep time in [0, x]
        idx = bisect.bisect_right(ends, x)
        total = prefix[idx]

        if idx < m and starts[idx] < x:
            total += x - starts[idx]

        return total

    Q = next(it)
    answers = []

    for _ in range(Q):
        l = next(it)
        r = next(it)
        answers.append(str(slept_until(r) - slept_until(l)))

    print("\n".join(answers))


if __name__ == "__main__":
    main()