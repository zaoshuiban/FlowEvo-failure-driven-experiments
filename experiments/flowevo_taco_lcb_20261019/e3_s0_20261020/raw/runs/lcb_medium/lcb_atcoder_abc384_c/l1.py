import sys

def main():
    a, b, c, d, e = map(int, sys.stdin.readline().split())
    scores = [a, b, c, d, e]
    problems = "ABCDE"

    participants = []

    for mask in range(1, 1 << 5):
        name = []
        score = 0

        for i in range(5):
            if mask & (1 << i):
                name.append(problems[i])
                score += scores[i]

        participants.append((score, "".join(name)))

    participants.sort(key=lambda x: (-x[0], x[1]))

    print("\n".join(name for _, name in participants))


if __name__ == "__main__":
    main()