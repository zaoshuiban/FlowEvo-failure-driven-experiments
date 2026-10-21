import sys

def solve():
    data = sys.stdin.read().split()
    t = int(data[0])
    idx = 1
    answers = []

    for _ in range(t):
        n = int(data[idx])
        k = int(data[idx + 1])
        s = data[idx + 2]
        idx += 3

        mismatches = 0
        for i in range(n // 2):
            if s[i] != s[n - 1 - i]:
                mismatches += 1

        if k < mismatches:
            answers.append("NO")
        else:
            remaining = k - mismatches
            if remaining % 2 == 0 or n % 2 == 1:
                answers.append("YES")
            else:
                answers.append("NO")

    print("\n".join(answers))

if __name__ == "__main__":
    solve()