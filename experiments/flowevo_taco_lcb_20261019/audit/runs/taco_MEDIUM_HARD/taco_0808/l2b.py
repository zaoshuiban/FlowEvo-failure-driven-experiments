import sys


def area_above(T1, T2, t1):
    # Area where y - x > t1: Chef arrives too early for Yurii.
    L = T2 - t1
    if L <= 0:
        return 0.0
    m = min(T1, L)
    return L * m - m * m * 0.5


def area_below(T1, T2, t2):
    # Area where x - y > t2: Yurii arrives too early for Chef.
    L = T1 - t2
    if L <= 0:
        return 0.0
    m = min(T2, L)
    return L * m - m * m * 0.5


def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    cases = data[0]
    idx = 1
    answers = []

    for _ in range(cases):
        T1 = data[idx]
        T2 = data[idx + 1]
        t1 = data[idx + 2]
        t2 = data[idx + 3]
        idx += 4

        total_area = float(T1) * float(T2)

        non_meeting_area = area_above(T1, T2, t1) + area_below(T1, T2, t2)
        probability = 1.0 - non_meeting_area / total_area

        if probability < 0.0:
            probability = 0.0
        elif probability > 1.0:
            probability = 1.0

        answers.append(f"{probability:.10f}")

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()