MOD = 998244353

def power(a, b):
	res = 1
	while b > 0:
		if b % 2 == 1:
			res = res * a % MOD
		a = a * a % MOD
		b //= 2
	return res

def inverse(n):
	return power(n, MOD - 2)
(h, w) = map(int, input().split())
grid = [input() for _ in range(h)]
prob = [0, 0]
for c in range(2, max(h, w) + 1):
	prob.append(prob[-1] + (-1) ** c * inverse(power(2, c)))
	prob[-1] %= MOD
res = 0
for r in range(h):
	cnt = 0
	for c in range(w):
		if grid[r][c] == 'o':
			cnt += 1
		else:
			cnt = 0
		res += prob[cnt]
		res %= MOD
for c in range(w):
	cnt = 0
	for r in range(h):
		if grid[r][c] == 'o':
			cnt += 1
		else:
			cnt = 0
		res += prob[cnt]
		res %= MOD
for r in range(h):
	for c in range(w):
		if grid[r][c] == 'o':
			res *= 2
			res %= MOD
print(res)
