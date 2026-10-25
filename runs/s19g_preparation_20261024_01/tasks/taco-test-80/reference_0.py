(x, m) = map(int, input().split())
x %= m
arr = [False] * m
while not arr[x]:
	arr[x] = True
	x *= 2
	x %= m
print(['Yes', 'No'][x != 0])
