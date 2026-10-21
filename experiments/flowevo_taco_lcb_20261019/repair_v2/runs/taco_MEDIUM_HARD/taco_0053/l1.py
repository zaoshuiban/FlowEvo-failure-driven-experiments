import sys

MOD = 10**9 + 7

data = list(map(int, sys.stdin.buffer.read().split()))
if not data:
    sys.exit()

t = data[0]
answers = []

for i in range(1, t + 1):
    n = data[i]
    ans = (pow(2, n + 1, MOD) + 2) % MOD
    answers.append(str(ans))

sys.stdout.write("\n".join(answers))