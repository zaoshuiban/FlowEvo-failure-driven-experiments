import sys


def min_seconds(s: bytes) -> int:
    freq = [0, 0, 0]
    cnt = [[0, 0, 0] for _ in range(3)]

    for ch in s:
        if ch == ord('r'):
            c = 0
        elif ch == ord('g'):
            c = 1
        else:
            c = 2

        cnt[0][c] += freq[0]
        cnt[1][c] += freq[1]
        cnt[2][c] += freq[2]
        freq[c] += 1

    permutations = (
        (0, 1, 2),
        (0, 2, 1),
        (1, 0, 2),
        (1, 2, 0),
        (2, 0, 1),
        (2, 1, 0),
    )

    answer = 10**18

    for p in permutations:
        cost = 0
        for i in range(3):
            for j in range(i + 1, 3):
                cost += cnt[p[j]][p[i]]
        if cost < answer:
            answer = cost

    return answer


def main() -> None:
    data = sys.stdin.buffer.read().split()
    if not data:
        return

    t = int(data[0])
    answers = []

    for i in range(1, t + 1):
        answers.append(str(min_seconds(data[i])))

    sys.stdout.write("\n".join(answers))


if __name__ == "__main__":
    main()