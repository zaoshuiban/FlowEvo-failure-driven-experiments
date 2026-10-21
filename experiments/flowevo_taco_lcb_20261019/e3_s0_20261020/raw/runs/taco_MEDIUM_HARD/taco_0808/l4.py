import sys


def solve() -> None:
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    test_cases = data[0]
    idx = 1
    answers = []

    for _ in range(test_cases):
        T1, T2, t1, t2 = data[idx], data[idx + 1], data[idx + 2], data[idx + 3]
        idx += 4

        # Work with twice the areas to keep everything in integers.
        total_twice = 2 * T1 * T2
        non_meeting_twice = 0

        # Region where Yurii arrives more than t1 seconds after Chef:
        # y - x > t1
        if t1 < T2:
            L = T2 - t1
            if L <= T1:
                non_meeting_twice += L * L
            else:
                non_meeting_twice += 2 * L * T1 - T1 * T1

        # Region where Chef arrives more than t2 seconds after Yurii:
        # x - y > t2
        if t2 < T1:
            L = T1 - t2
            if L <= T2:
                non_meeting_twice += L * L
            else:
                non_meeting_twice += 2 * L * T2 - T2 * T2

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