import sys

def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    test_cases = data[0]
    idx = 1
    answers = []

    for _ in range(test_cases):
        T1, T2, t1, t2 = data[idx], data[idx + 1], data[idx + 2], data[idx + 3]
        idx += 4

        a = T1 - t2
        if a <= 0:
            area1_twice = 0
        elif a <= T2:
            area1_twice = a * a
        else:
            area1_twice = 2 * a * T2 - T2 * T2

        b = T2 - t1
        if b <= 0:
            area2_twice = 0
        elif b <= T1:
            area2_twice = b * b
        else:
            area2_twice = 2 * b * T1 - T1 * T1

        total_twice = 2 * T1 * T2
        valid_twice = total_twice - area1_twice - area2_twice

        probability = valid_twice / total_twice
        answers.append(f"{probability:.10f}")

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    solve()