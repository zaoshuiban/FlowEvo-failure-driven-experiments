import sys


def solve() -> None:
    it = iter(map(int, sys.stdin.buffer.read().split()))
    try:
        T = next(it)
    except StopIteration:
        return

    answers = []

    for _ in range(T):
        N = next(it)
        M = next(it)
        K = next(it)

        if K == 0:
            # Consume the matrix.
            for _ in range(N * M):
                next(it)

            # Count all square submatrices.
            # N <= M, so side lengths are 1..N.
            total = (
                (M - N) * N * (N + 1) // 2
                + N * (N + 1) * (2 * N + 1) // 6
            )
            answers.append(str(total))
            continue

        if N == 1:
            total = 0
            for _ in range(M):
                if next(it) >= K:
                    total += 1
            answers.append(str(total))
            continue

        # 2D prefix sums.
        pref = [[0] * (M + 1) for _ in range(N + 1)]

        for i in range(1, N + 1):
            prev = pref[i - 1]
            cur = pref[i]

            for j in range(1, M + 1):
                value = next(it)
                cur[j] = value + prev[j] + cur[j - 1] - prev[j - 1]

        total = 0

        for i in range(1, N + 1):
            top_row = pref[i - 1]
            current_row = pref[i]
            max_down = N - i + 1

            for j in range(1, M + 1):
                jm1 = j - 1
                max_right = M - j + 1
                max_side = max_down if max_down < max_right else max_right

                # Check side length 1.
                if current_row[j] - top_row[j] - current_row[jm1] + top_row[jm1] >= K:
                    total += max_side
                    continue

                if max_side <= 1:
                    continue

                # Find the smallest side length whose average is at least K.
                low = 2
                high = max_side
                first_valid = 0

                while low <= high:
                    mid = (low + high) // 2
                    right = j + mid - 1
                    bottom_row = pref[i + mid - 1]

                    square_sum = (
                        bottom_row[right]
                        - top_row[right]
                        - bottom_row[jm1]
                        + top_row[jm1]
                    )

                    if square_sum >= K * mid * mid:
                        first_valid = mid
                        high = mid - 1
                    else:
                        low = mid + 1

                if first_valid:
                    total += max_side - first_valid + 1

        answers.append(str(total))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()