from math import gcd

def LCM(a, b):
	if min(a, b) == 0:
		return max(a, b)
	return a // gcd(a, b) * b

class Eqn:

	def __init__(self, r, mod):
		self.r = r
		self.mod = mod

def bye():
	print('NO')
	exit(0)

def exgcd(a, b):
	if b == 0:
		return (1, 0)
	(xp, yp) = exgcd(b, a % b)
	x = yp
	y = xp - a // b * yp
	return (x, y)

def merge(a, b):
	newmode = LCM(a.mod, b.mod)
	if (a.r - b.r) % gcd(a.mod, b.mod) != 0:
		bye()
	newr = exgcd(a.mod, b.mod)[0] * (b.r - a.r) // gcd(a.mod, b.mod) * a.mod + a.r
	newr %= newmode
	return Eqn(newr, newmode)
(x, y) = (0, 0)
(n, m, k) = [int(i) for i in input().split()]
a = [int(i) for i in input().split()]
for i in a:
	x = LCM(x, i)
	if x > n:
		bye()
cur = Eqn(0, 1)
for i in range(0, len(a)):
	cur = merge(cur, Eqn(-i % a[i], a[i]))
y = cur.r
if y == 0:
	y += x
for i in range(0, len(a)):
	if gcd(x, y + i) != a[i]:
		bye()
if x > n or y + k - 1 > m:
	bye()
print('YES')
