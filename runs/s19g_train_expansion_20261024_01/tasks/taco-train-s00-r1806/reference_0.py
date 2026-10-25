from collections import defaultdict
mod = int(1000000009)

def is_good(n, a, b):
	while n:
		digit = n % 10
		if digit != a and digit != b:
			return False
		n = n // 10
	return True
(n, m, k) = map(int, input().split())
m -= n % k
score = n % k
n -= n % k
sets = n // k
used = sets * (k - 1)
if used >= m:
	print(m + score)
	exit()
else:
	filled = m - used
	score += 2 * k * (2 ** filled % mod - 1) % mod
	score += int(sets - filled) * (k - 1) % mod
print(score % mod)
