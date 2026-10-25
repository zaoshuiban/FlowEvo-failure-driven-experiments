def readGen(transform):
	while True:
		n = 0
		tmp = input().split()
		m = len(tmp)
		while n < m:
			yield transform(tmp[n])
			n += 1
readint = readGen(int)

def work():
	(n, m) = (next(readint), next(readint))
	(x1, y1) = (next(readint), next(readint))
	(x2, y2) = (next(readint), next(readint))
	l = min(x1 - 1, x2 - 1)
	r = min(n - x1, n - x2)
	u = min(y1 - 1, y2 - 1)
	d = min(m - y1, m - y2)
	w = l + r - abs(x1 - x2) + 1
	h = u + d - abs(y1 - y2) + 1
	if w <= 0 or h <= 0:
		a = 0
	else:
		a = h * w
	cover = 2 * (l + r + 1) * (u + d + 1) - a
	print(m * n - cover)
n = next(readint)
for i in range(n):
	work()
