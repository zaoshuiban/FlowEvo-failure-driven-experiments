import sys


def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    tc = data[0]
    idx = 1
    answers = []

    for _ in range(tc):
        T1, T2, t1, t2 = data[idx], data[idx + 1], data[idx + 2], data[idx + 3]
        idx += 4

        # Work with doubled areas to keep computations exact.
        total_twice = 2 * T1 * T2
        non_meeting_twice = 0

        # Region where Yurii arrives more than t1 seconds after Chef:
        # y - x > t1
        if t1 < T2:
            L = T2 - t1
            m = min(T1, L)
            non_meeting_twice += 2 * L * m - m * m

        # Region where Chef arrives more than t2 seconds after Yurii:
        # x - y > t2
        if t2 < T1:
            L = T1 - t2
            m = min(T2, L)
            non_meeting_twice += 2 * L * m - m * m

        meeting_twice = total_twice - non_meeting_twice
        if meeting_twice < 0:
            meeting_twice = 0
        elif meeting_twice > total_twice:
            meeting_twice = total_twice

        probability = meeting_twice / total_twice
        answers.append(f"{probability:.10f}")

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()