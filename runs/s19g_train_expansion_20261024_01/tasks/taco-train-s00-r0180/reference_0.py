from collections import defaultdict
(n, k) = map(int, input().split())
a = list(map(int, input().split()))
n = int(max(a) ** 0.5)
mark = [True] * (n + 1)
prime = []
for i in range(2, n + 1):
	if mark[i]:
		for j in range(i, n + 1, i):
			mark[j] = False
		prime.append(i)
d = defaultdict(int)
(ans, count) = (0, 0)
for i in a:
	(t, t1) = ((), ())
	for j in prime:
		if i == 1:
			break
		if i % j == 0:
			count = 0
			while i % j == 0:
				i //= j
				count += 1
			z = count % k
			if z:
				t += (j, z)
				t1 += (j, k - z)
	if i > 1:
		t += (i, 1)
		t1 += (i, k - 1)
	ans += d[t1]
	d[t] += 1
print(ans)
