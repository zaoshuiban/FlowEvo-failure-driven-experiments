import sys

def solve():
    data = sys.stdin.buffer.read().split()
    n = int(data[0])
    strings = data[1:1+n]

    countA = {}
    countB = {}

    for s in strings:
        bal = 0
        min_bal = 0
        for ch in s:
            if ch == 40:  # '('
                bal += 1
            else:
                bal -= 1
            if bal < min_bal:
                min_bal = bal

        if min_bal >= 0:
            countA[bal] = countA.get(bal, 0) + 1
        else:
            bal2 = 0
            min_bal2 = 0
            for ch in reversed(s):
                if ch == 41:  # ')'
                    bal2 += 1
                else:
                    bal2 -= 1
                if bal2 < min_bal2:
                    min_bal2 = bal2
            if min_bal2 >= 0:
                orig_bal = -bal2
                countB[orig_bal] = countB.get(orig_bal, 0) + 1

    ans = 0
    for b, cnt in countA.items():
        if -b in countB:
            ans += min(cnt, countB[-b])

    print(ans)

if __name__ == "__main__":
    solve()