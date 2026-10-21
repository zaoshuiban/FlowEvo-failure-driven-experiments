import sys

def solve():
    data = iter(map(int, sys.stdin.buffer.read().split()))
    try:
        test_cases = next(data)
    except StopIteration:
        return

    answers = []

    for _ in range(test_cases):
        T1 = next(data)
        T2 = next(data)
        t1 = next(data)
        t2 = next(data)

        a = T1
        b = T2

        # Twice the area where Yurii arrives too late:
        # y > x + t1
        H = b - t1
        if H <= 0:
            above2 = 0
        elif H <= a:
            above2 = H * H
        else:
            above2 = 2 * a * H - a * a

        # Twice the area where Yurii arrives too early:
        # y < x - t2
        L = a - t2
        if L <= 0:
            below2 = 0
        else:
            K = min(b, L)
            below2 = 2 * L * K - K * K

        total2 = 2 * a * b
        meet2 = total2 - above2 - below2

        probability = meet2 / total2
        answers.append(f"{probability:.12f}")

    sys.stdout.write("\n".join(answers))

if __name__ == "__main__":
    solve()