from collections import deque
for _ in range(int(input())):
	(n, m, k1, k2) = list(map(int, input().split()))
	arr = []
	for i in range(n):
		arr.append(list(map(int, input().split())))
	robo1 = [[-1] * m for i in range(n)]
	robo2 = [[-1] * m for i in range(n)]
	robo1[0][0] = 0
	robo2[0][m - 1] = 0
	Q = deque([(0, 0)])
	while Q:
		(i, j) = Q.popleft()
		for x in range(max(i - k1, 0), min(i + k1 + 1, n)):
			t = abs(i - x)
			for y in range(max(0, j - k1 + t), min(j + k1 - t + 1, m)):
				if arr[x][y] == 0 and robo1[x][y] == -1:
					robo1[x][y] = robo1[i][j] + 1
					Q.append((x, y))
	Q = deque([(0, m - 1)])
	while Q:
		(i, j) = Q.popleft()
		for x in range(max(i - k2, 0), min(i + k2 + 1, n)):
			t = abs(i - x)
			for y in range(max(0, j - k2 + t), min(j + k2 - t + 1, m)):
				if arr[x][y] == 0 and robo2[x][y] == -1:
					robo2[x][y] = robo2[i][j] + 1
					Q.append((x, y))
	ans = float('inf')
	for i in range(n):
		for j in range(m):
			if robo1[i][j] != -1 and robo2[i][j] != -1:
				ans = min(ans, max(robo1[i][j], robo2[i][j]))
	print(-1 if ans == float('inf') else ans)
