import sys

MOD = 998244353
MAXN = 300000

pow2 = [1] * (MAXN + 5)
for i in range(1, MAXN + 5):
    pow2[i] = (pow2[i - 1] * 2) % MOD

data = sys.stdin.buffer.read()
idx = 0
length = len(data)

def next_int():
    global idx
    while idx < length and data[idx] <= 32:
        idx += 1
    num = 0
    while idx < length and data[idx] > 32:
        num = num * 10 + (data[idx] - 48)
        idx += 1
    return num

t = next_int()
answers = []

for _ in range(t):
    n = next_int()
    m = next_int()

    adj = [[] for _ in range(n)]

    for _ in range(m):
        u = next_int() - 1
        v = next_int() - 1
        adj[u].append(v)
        adj[v].append(u)

    color = [-1] * n
    answer = 1
    valid = True

    for start in range(n):
        if color[start] != -1:
            continue

        color[start] = 0
        stack = [start]
        count0 = 1
        count1 = 0

        while stack and valid:
            u = stack.pop()
            current_color = color[u]

            for v in adj[u]:
                if color[v] == -1:
                    color[v] = current_color ^ 1
                    if color[v] == 0:
                        count0 += 1
                    else:
                        count1 += 1
                    stack.append(v)
                elif color[v] == current_color:
                    valid = False
                    break

        if not valid:
            break

        ways_component = (pow2[count0] + pow2[count1]) % MOD
        answer = (answer * ways_component) % MOD

    if valid:
        answers.append(str(answer))
    else:
        answers.append("0")

sys.stdout.write("\n".join(answers))