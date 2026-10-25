import sys
(n, m, d) = map(int, input().split())
L = []
for i in range(n):
	L.extend(list(map(int, input().split())))
L.sort()
(moves, middle) = (0, n * m // 2)
for i in range(n * m):
	if abs(L[middle] - L[i]) % d != 0:
		print('-1')
		sys.exit(0)
		break
	else:
		moves += abs(L[middle] - L[i]) // d
print(moves)
sys.exit(0)
