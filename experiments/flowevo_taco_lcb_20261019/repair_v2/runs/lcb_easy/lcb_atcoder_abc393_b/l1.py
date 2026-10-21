import sys

S = sys.stdin.readline().strip()
n = len(S)
answer = 0

for j in range(n):
    if S[j] != 'B':
        continue

    d = 1
    while j - d >= 0 and j + d < n:
        if S[j - d] == 'A' and S[j + d] == 'C':
            answer += 1
        d += 1

print(answer)