def solve(s, n, k):
	s = sorted(s)
	if s[0] != s[k - 1]:
		return s[k - 1]
	worst = s[0]
	if k < n and s[k] != s[-1]:
		return worst + ''.join(s[k:])
	else:
		return worst + s[-1] * ((n - 1) // k)
T = int(input())
for _ in range(T):
	_nk = input().split()
	n = int(_nk[0])
	k = int(_nk[1])
	s = input().strip()
	print(solve(s, n, k))
