from math import gcd
from functools import reduce
(n, k) = [int(aa) for aa in input().split()]
a = [int(aa) for aa in input().split()]
g = reduce(gcd, a) % k
answ = [0] * k
pos = g
count = 0
while answ[pos] == 0:
	answ[pos] = 1
	pos = (pos + g) % k
	count += 1
print(count)
for i in range(len(answ)):
	if answ[i] == 1:
		print(i, end=' ')
