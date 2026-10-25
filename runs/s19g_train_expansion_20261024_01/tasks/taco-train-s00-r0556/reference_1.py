(n, m) = map(int, input().split())
f = [[int(1000000000.0) for j in range(m)] for i in range(n)]
for i in range(n):
	s = input()
	if s.find('1') == -1:
		print(-1)
		exit()
	f[i][0] = s[::-1].find('1') + 1
	f[i][m - 1] = s.find('1') + 1
	for j in range(m):
		f[i][j] = 0 if s[j] == '1' else f[i][j]
	for j in range(m):
		f[i][j] = min(f[i][j], f[i][j - 1] + 1)
	for j in range(m - 2, -1, -1):
		f[i][j] = min(f[i][j], f[i][j + 1] + 1)
print(min([sum([f[i][j] for i in range(n)]) for j in range(m)]))
