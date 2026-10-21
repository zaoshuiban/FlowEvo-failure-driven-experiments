import sys
import bisect


def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    it = iter(data)

    T = next(it)
    output = []

    for _ in range(T):
        N = next(it)
        Q = next(it)

        A = [next(it) for _ in range(N)]

        starts = []
        ends = []
        lengths = []

        i = 0
        while i < N:
            j = i + 1
            while j < N and A[j] == A[i]:
                j += 1

            starts.append(i)
            ends.append(j - 1)
            lengths.append(j - i)

            i = j

        M = len(lengths)
        answers = [0] * Q
        requests = []

        for qi in range(Q):
            L = next(it)
            R = next(it)
            K = next(it)

            l = L - 1
            r = R - 1

            p = bisect.bisect_right(starts, l) - 1
            q = bisect.bisect_right(starts, r) - 1

            if p == q:
                if r - l + 1 >= K:
                    answers[qi] = 1
            else:
                cnt = 0

                if ends[p] - l + 1 >= K:
                    cnt += 1

                if r - starts[q] + 1 >= K:
                    cnt += 1

                answers[qi] = cnt

                if p + 1 <= q - 1:
                    requests.append((K, p + 1, q - 1, qi))

        if requests:
            order = sorted(range(M), key=lambda x: lengths[x], reverse=True)
            requests.sort(key=lambda x: x[0], reverse=True)

            bit = [0] * (M + 2)

            def add(pos):
                pos += 1
                while pos <= M:
                    bit[pos] += 1
                    pos += pos & -pos

            def prefix_sum(pos):
                result = 0
                while pos > 0:
                    result += bit[pos]
                    pos -= pos & -pos
                return result

            ptr = 0

            for K, left_run, right_run, qi in requests:
                while ptr < M and lengths[order[ptr]] >= K:
                    add(order[ptr])
                    ptr += 1

                full_runs = (
                    prefix_sum(right_run + 1) - prefix_sum(left_run)
                )
                answers[qi] += full_runs

        output.extend(map(str, answers))

    sys.stdout.write("\n".join(output))


if __name__ == "__main__":
    solve()