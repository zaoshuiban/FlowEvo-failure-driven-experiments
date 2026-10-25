t = int(input(''))
C = [0] * t
for i in range(t):
	LRX = input('').split(' ')
	n = int(LRX[0])
	m = int(LRX[1])
	n2 = 1
	k = 1
	while n % 10 == 0:
		n //= 10
		n2 *= 10
	while n % 2 == 0:
		if 5 * k <= m:
			k = 5 * k
		n //= 2
		n2 *= 2
	while n % 5 == 0:
		if 2 * k <= m:
			k = 2 * k
		n //= 5
		n2 *= 5
	while 10 * k <= m:
		k *= 10
	k *= m // k
	C[i] = k * n * n2
for j in C:
	print(j)
