import sys
from itertools import permutations

def solve():
    data = sys.stdin.read().split()
    if not data:
        return

    t = int(data[0])
    colors = {'r': 0, 'g': 1, 'b': 2}
    perms = list(permutations(range(3)))

    answers = []

    for case in range(1, t + 1):
        s = data[case]

        # cnt[a][b] = number of pairs (i, j) such that i < j, s[i] = a, s[j] = b
        cnt = [[0] * 3 for _ in range(3)]
        seen = [0, 0, 0]

        for ch in s:
            cur = colors[ch]
            for prev in range(3):
                cnt[prev][cur] += seen[prev]
            seen[cur] += 1

        ans = 10**30

        for perm in perms:
            cost = 0
            for i in range(3):
                for j in range(i + 1, 3):
                    earlier = perm[i]
                    later = perm[j]
                    # Pairs where 'later' appears before 'earlier' are inversions.
                    cost += cnt[later][earlier]
            if cost < ans:
                ans = cost

        answers.append(str(ans))

    sys.stdout.write("\n".join(answers))

if __name__ == "__main__":
    solve()