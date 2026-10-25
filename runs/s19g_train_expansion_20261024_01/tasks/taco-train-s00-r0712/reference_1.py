import heapq
n = int(input())
V = list(map(int, input().split()))
T = list(map(int, input().split()))
a = []
ans = []
tmp = 0
for i in range(0, n):
	heapq.heappush(a, tmp + V[i])
	tmpAns = 0
	while len(a) and a[0] <= tmp + T[i]:
		tmpAns += heapq.heappop(a) - tmp
	tmpAns += len(a) * T[i]
	ans.append(tmpAns)
	tmp += T[i]
print(' '.join(map(str, ans)))
