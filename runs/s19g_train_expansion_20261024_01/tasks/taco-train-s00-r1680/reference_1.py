inp = lambda : map(int, input().rstrip().split())
(n, q) = inp()
li = sorted(inp())
a = [0] * (n + 1)
for _ in range(q):
	(x, y) = inp()
	a[x - 1] += 1
	a[y] -= 1
for i in range(n):
	a[i + 1] += a[i]
print(sum(map(lambda x: x[0] * x[1], zip(li, sorted(a[:-1])))))
