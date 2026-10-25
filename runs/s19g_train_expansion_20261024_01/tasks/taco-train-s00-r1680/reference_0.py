from sys import stdin, stdout
(n, m) = map(int, stdin.readline().split())
l = list(map(int, stdin.readline().split()))
l1 = [0] * n
for i in range(m):
	(p, q) = map(int, stdin.readline().split())
	l1[p - 1] += 1
	if q != n:
		l1[q] -= 1
c = 0
for i in range(n):
	c += l1[i]
	l1[i] = c
l1.sort()
l.sort()
a = 0
for i in range(n):
	a += l[i] * l1[i]
stdout.write(str(a) + '\n')
