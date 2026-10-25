n = int(input())
ans = 0
visited = {}
f = {}
s = {}
for i in range(n):
	n = [int(x) for x in input().split()]
	if n[0] in f:
		ans += f[n[0]]
		f[n[0]] += 1
	else:
		f[n[0]] = 1
	if n[1] in s:
		ans += s[n[1]]
		s[n[1]] += 1
	else:
		s[n[1]] = 1
	if tuple(n) in visited:
		ans -= visited[tuple(n)]
		visited[tuple(n)] += 1
	else:
		visited[tuple(n)] = 1
print(ans)
