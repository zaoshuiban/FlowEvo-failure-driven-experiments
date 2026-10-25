for _ in range(int(input())):
	n = int(input())
	arr = list(map(int, input().split()))
	tot = 0
	for i in range(1, n):
		tot += abs(arr[i] - arr[i - 1])
	ans = min(tot - abs(arr[0] - arr[1]), tot - abs(arr[n - 1] - arr[n - 2]))
	for i in range(1, n - 1):
		ans = min(ans, tot - abs(arr[i] - arr[i - 1]) - abs(arr[i] - arr[i + 1]) + abs(arr[i - 1] - arr[i + 1]))
	print(ans)
