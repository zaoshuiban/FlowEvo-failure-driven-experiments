def gcd(a, b):
	if b == 0:
		return a
	return gcd(b, a % b)

def ext(a, b):
	if b == 0:
		return (1, 0)
	else:
		(y, x) = ext(b, a % b)
		y = y - a // b * x
		return (x, y)
(n, m, k) = map(int, input().split())
a = list(map(int, input().split()))
lcm = 1
for i in a:
	lcm = lcm * i // gcd(lcm, i)
	if lcm > n:
		print('NO')
		exit()
j = 0
m1 = 1
s = True
for i in range(k):
	(x, y) = ext(m1, a[i])
	res = m1 * x + a[i] * y
	if (-i - j) % res != 0:
		s = False
		break
	res = (-i - j) // res
	(x, y) = (x * res, y * res)
	j += m1 * x
	t = m1 * a[i]
	if j > t:
		j -= j // t * t
	if j < 0:
		j += (-j + t - 1) // t * t
	if j == 0:
		j = t
	m1 = m1 * a[i] // gcd(m1, a[i])
if j + k - 1 > m or s == False:
	print('NO')
	exit()
b = [gcd(lcm, j + i) for i in range(k)]
for i in range(k):
	if a[i] != b[i]:
		print('NO')
		exit()
print('YES')
