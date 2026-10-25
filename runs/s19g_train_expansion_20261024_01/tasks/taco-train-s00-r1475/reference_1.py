def avoiddef(a, b):
	b.reverse()
	x = 0
	i = 0
	n = min(len(a), len(b))
	while i < n and b[i] > a[i]:
		x += b[i] - a[i]
		i += 1
	return x

def killdefs(d, a, b):
	i = 0
	n = len(b)
	b2 = [bb for bb in b]
	for dd in d:
		while i < n and b2[i] <= dd:
			i += 1
		if i == n:
			return -1
		b2[i] = 0
		i += 1
	b2.sort()
	x = 0
	i = 0
	for aa in a:
		while i < n and b2[i] < aa:
			i += 1
		if i == n:
			return -1
		i += 1
	return sum(b2) - sum(a)

def f(a, bl):
	al = [int(c[1]) for c in a if c[0] == 'ATK']
	dl = [int(c[1]) for c in a if c[0] == 'DEF']
	al.sort()
	dl.sort()
	bl.sort()
	return max(killdefs(dl, al, bl), avoiddef(al, bl))
(n, m) = list(map(int, input().split()))
a = [input().split() for _ in range(n)]
b = [int(input()) for _ in range(m)]
print(f(a, b))
