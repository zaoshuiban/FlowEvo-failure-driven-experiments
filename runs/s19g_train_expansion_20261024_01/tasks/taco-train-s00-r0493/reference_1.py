from collections import deque
(N, M) = map(int, input().split())
D = sorted(list(set([int(a) for a in input().split()] + [-1 << 10, N])))
M = len(D)
DD = [D[i + 1] - D[i] for i in range(M - 1)]
(g, r) = map(int, input().split())
X = [[0] * (g + 1) for _ in range(M)]
a = D[1]
Q = deque([(1, g - a, 0)] if a < g else [(1, g, 1)] if g == a else [])
ma = -1
gt = 1 << 30
goal = M - 1
while Q:
	(i, a, t) = deque.popleft(Q)
	if t > gt:
		continue
	if X[i][a]:
		continue
	X[i][a] = 1
	if i == goal:
		ma = max(ma, a)
		gt = t
		continue
	(dl, dr) = (DD[i - 1], DD[i])
	if dl < a:
		Q.appendleft((i - 1, a - dl, t))
	elif dl == a:
		Q.append((i - 1, g, t + 1))
	if dr < a:
		Q.appendleft((i + 1, a - dr, t))
	elif dr == a:
		Q.append((i + 1, g, t + 1))
print(gt * (g + r) + (g - ma if ma < g else -r) if ma >= 0 else -1)
