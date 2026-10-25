(n, m, k, x, y) = map(int, input().split())
if n == 1:
	if k % m == 0:
		ans = k // m
		print(ans, ans, ans)
	else:
		rem = k % m
		ans = k // m
		if y <= rem:
			print(ans + 1, ans, ans + 1)
		else:
			print(ans + 1, ans, ans)
	exit(0)
if k == n * m:
	print('1 1 1')
	exit(0)
if k > n * m:
	f = 1
	l = 1
	o = 1
	k -= n * m
	div = k // ((n - 1) * m)
	k = k % ((n - 1) * m)
	if div & 1:
		f = div // 2 + 2
		l = f - 1
	else:
		f = div // 2 + 1
		l = f
	if n == 2:
		o = 0
	else:
		o = div + 1
	s = o
	if x == 1:
		s = f
	if x == n:
		s = l
	if k > 0 and n != 2:
		o += 1
	if k - (n - 2) * m > 0:
		if div % 2 == 0:
			f += 1
	if div & 1:
		for i in range(1, n):
			for j in range(0, m):
				if k == 0:
					break
				if i == x - 1 and j == y - 1:
					s += 1
				k -= 1
			if k == 0:
				break
	else:
		for i in range(n - 2, -1, -1):
			for j in range(0, m):
				if k == 0:
					break
				if i == x - 1 and j == y - 1:
					s += 1
				k -= 1
			if k == 0:
				break
	print(max(o, f, l), min(f, l), s)
	exit(0)
s = 0
for i in range(0, n):
	for j in range(0, m):
		if k == 0:
			break
		if i == x - 1 and j == y - 1:
			s += 1
		k -= 1
	if k == 0:
		break
if s > 0:
	print(1, 0, 1)
else:
	print(1, 0, 0)
