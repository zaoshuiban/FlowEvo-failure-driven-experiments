N = 100010

def gen_mobius_function():
	mu = [1] * N
	mu[0] = 0
	P = [True] * N
	P[0] = P[1] = False
	for i in range(2, N):
		if P[i]:
			j = i
			while j < N:
				P[j] = False
				mu[j] *= -1
				j += i
			j = i * i
			while j < N:
				mu[j] = 0
				j += i * i
	return mu
m = int(input())
mu = gen_mobius_function()
MOD = 10 ** 9 + 7

def mod_inv(x):
	return pow(x, MOD - 2, MOD)
E = 1
for i in range(2, N):
	p = m // i * mod_inv(m)
	E += -mu[i] * p * mod_inv(1 - p)
print(E % MOD)
