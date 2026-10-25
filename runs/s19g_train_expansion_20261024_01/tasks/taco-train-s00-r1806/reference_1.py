p = int(1000000000.0 + 9)

def f2(l):
	(n, m, k) = l
	w = n - m
	cc = n - w * k
	if cc < k:
		return m
	nkp1 = cc // k + 1
	f = w * (k - 1) + cc % k - (k << 1)
	return f + (k << nkp1) % p

def f(l):
	(n, m, k) = l
	w = n - m
	cc = n - w * k
	if cc < k:
		return m
	g = ((2 << cc // k) - 2) % p
	fcc = k * g + cc % k
	return fcc + w * (k - 1)
l = list(map(int, input().split()))
print(f2(l) % p)
