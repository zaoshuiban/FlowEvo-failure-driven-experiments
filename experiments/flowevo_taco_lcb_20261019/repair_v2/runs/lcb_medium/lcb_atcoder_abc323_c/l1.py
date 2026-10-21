import sys


def main():
    input = sys.stdin.readline

    N, M = map(int, input().split())
    A = list(map(int, input().split()))
    S = [input().strip() for _ in range(N)]

    scores = []
    for i, s in enumerate(S, start=1):
        total = i
        for j, ch in enumerate(s):
            if ch == 'o':
                total += A[j]
        scores.append(total)

    answers = []

    for i in range(N):
        current = scores[i]

        max_other = 0
        for j in range(N):
            if i != j:
                max_other = max(max_other, scores[j])

        need = max_other + 1 - current

        if need <= 0:
            answers.append("0")
            continue

        unsolved = []
        for j, ch in enumerate(S[i]):
            if ch == 'x':
                unsolved.append(A[j])

        unsolved.sort(reverse=True)

        gained = 0
        count = 0

        for score in unsolved:
            gained += score
            count += 1
            if gained >= need:
                break

        answers.append(str(count))

    print("\n".join(answers))


if __name__ == "__main__":
    main()