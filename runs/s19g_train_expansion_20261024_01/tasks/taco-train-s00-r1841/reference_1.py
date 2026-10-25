import sys
int1 = lambda x: int(x) - 1
p2D = lambda x: print(*x, sep='\n')

def II():
	return int(sys.stdin.readline())

def MI():
	return map(int, sys.stdin.readline().split())

def LI():
	return list(map(int, sys.stdin.readline().split()))

def LLI(rows_number):
	return [LI() for _ in range(rows_number)]

def SI():
	return sys.stdin.readline()[:-1]

def chmax(i, j, val):
	if i > k or j > n:
		return
	if val > dp[i][j]:
		dp[i][j] = val
(n, k) = MI()
s = SI()
t = SI()
if t[0] == t[1]:
	c = min(len(s), s.count(t[0]) + k)
	print(c * (c - 1) // 2)
	exit()
dp = [[-1] * (n + 1) for _ in range(k + 1)]
dp[0][0] = 0
for c in s:
	for i in range(k, -1, -1):
		for j in range(n, -1, -1):
			pre = dp[i][j]
			if pre == -1:
				continue
			if c == t[1]:
				chmax(i, j, pre + j)
			else:
				chmax(i + 1, j, pre + j)
			if c == t[0]:
				chmax(i, j + 1, pre)
			else:
				chmax(i + 1, j + 1, pre)
print(max((dp[i][j] for j in range(n + 1) for i in range(k + 1))))
