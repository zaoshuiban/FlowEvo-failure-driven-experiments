def move(i):
	if lis[i + 1] >= 1:
		lis[i + 1] -= 1
		lis[i] += 2
		return 1
	else:
		ret = move(i + 1)
		lis[i + 1] -= 1
		lis[i] += 2
		return ret + 1
import math
t = int(input())
dic = {}
rdic = {}
for i in range(61):
	dic[2 ** i] = i
	rdic[i] = 2 ** i
for loop in range(t):
	(n, m) = map(int, input().split())
	a = list(map(int, input().split()))
	if sum(a) < n:
		print(-1)
		continue
	lis = [0] * 62
	ans = 0
	for i in a:
		lis[dic[i]] += 1
	nsum = 0
	NN = 0
	for i in range(61):
		nsum += lis[i] * rdic[i]
		NN += n & rdic[i]
		if nsum >= NN:
			continue
		else:
			ans += move(i)
			nsum += rdic[i]
	print(ans)
