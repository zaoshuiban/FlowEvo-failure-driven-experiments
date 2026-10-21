import sys


def solve() -> None:
    it = iter(map(int, sys.stdin.buffer.read().split()))
    t = next(it)
    answers = []

    for _ in range(t):
        n = next(it)
        m = next(it)

        prev_min = [0] * m
        prev_max = [0] * m

        for i in range(n):
            curr_min = [0] * m
            curr_max = [0] * m

            for j in range(m):
                val = next(it)

                if i == 0:
                    if j == 0:
                        curr_min[j] = curr_max[j] = val
                    else:
                        curr_min[j] = curr_min[j - 1] + val
                        curr_max[j] = curr_max[j - 1] + val
                else:
                    if j == 0:
                        curr_min[j] = prev_min[j] + val
                        curr_max[j] = prev_max[j] + val
                    else:
                        curr_min[j] = min(prev_min[j], curr_min[j - 1]) + val
                        curr_max[j] = max(prev_max[j], curr_max[j - 1]) + val

            prev_min, prev_max = curr_min, curr_max

        # Number of cells on any path is n + m - 1.
        # For the sum to be 0, this number must be even.
        if (n + m) % 2 == 0:
            answers.append("NO")
        elif prev_min[m - 1] <= 0 <= prev_max[m - 1]:
            answers.append("YES")
        else:
            answers.append("NO")

    sys.stdout.write("\n".join(answers) + "\n")


if __name__ == "__main__":
    solve()