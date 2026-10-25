import sys
(n, m) = map(int, input().split())
mp = ['' for i in range(n)]
f = [[0 for j in range(m)] for i in range(n)]
for i in range(n):
	mp[i] = input()
	if mp[i].find('1') == -1:
		print(-1)
		sys.exit()
	tmp = mp[i][::-1].find('1') + 1
	for j in range(m):
		if mp[i][j] == '1':
			f[i][j] = 0
		else:
			f[i][j] = f[i][j - 1] + 1 if j > 0 else tmp
	tmp = mp[i].find('1') + 1
	for j in range(m - 1, -1, -1):
		f[i][j] = min(f[i][j], f[i][j + 1] + 1 if j + 1 < m else tmp)
ans = int(1000000000.0)
for j in range(m):
	sm = 0
	for i in range(n):
		sm += f[i][j]
	ans = min(ans, sm)
print(ans)
