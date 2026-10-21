import sys

def solve():
    data = list(map(int, sys.stdin.buffer.read().split()))
    if not data:
        return

    t = data[0]
    idx = 1
    answers = []

    for _ in range(t):
        n = data[idx]
        k = data[idx + 1]
        idx += 2

        a = data[idx:idx + n]
        idx += n

        votes = [0] * (n + 1)
        for voted in a:
            votes[voted] += 1

        answer = 0
        for person in range(1, n + 1):
            if votes[person] >= k and a[person - 1] != person:
                answer += 1

        answers.append(str(answer))

    sys.stdout.write("\n".join(answers))

if __name__ == "__main__":
    solve()