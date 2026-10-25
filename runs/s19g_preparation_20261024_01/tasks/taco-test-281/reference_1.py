def comb(n, k, MOD):
	if k > n // 2:
		k = n - k
	answer = 1
	for i in range(k):
		answer *= n - i
		answer //= i + 1
	return answer % MOD

def putin():
	return map(int, input().split())

def sol():
	n = int(input())
	A = list(input())
	num_zeros = 0
	num_pairs = 0
	first = 0
	for i in range(n):
		if A[i] == '0':
			first = 0
			num_zeros += 1
		elif first == 0:
			first = 1
		else:
			num_pairs += 1
			first = 0
	print(comb(num_zeros + num_pairs, num_zeros, 998244353))
for itr in range(int(input())):
	sol()
