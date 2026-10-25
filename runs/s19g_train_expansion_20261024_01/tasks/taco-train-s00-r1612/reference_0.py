def LIS(s):
	n = len(s)
	L = [0] * n
	appear = [False] * n
	L[0] = 1
	find = [-1] * n
	appear[s[0]] = True
	find[s[0]] = 0
	for i in range(1, len(s)):
		if s[i] > 0 and appear[s[i] - 1]:
			L[i] = L[find[s[i] - 1]] + 1
		else:
			L[i] = 1
		appear[s[i]] = True
		find[s[i]] = i
	return max(L)

def BIS(s):
	n = len(s)
	L = [0] * n
	appear = [False] * n
	L[n - 1] = 1
	find = [-1] * n
	appear[s[n - 1]] = True
	find[s[n - 1]] = n - 1
	for i in range(n - 2, -1, -1):
		if s[i] + 1 < n and appear[s[i] + 1]:
			L[i] = L[find[s[i] - 1]] + 1
		else:
			L[i] = 1
		appear[s[i]] = True
		find[s[i]] = i
	return max(L)
n = int(input())
L = list(map(int, input().split()))
L = [x - 1 for x in L]
print(n - max(LIS(L), BIS(L)))
