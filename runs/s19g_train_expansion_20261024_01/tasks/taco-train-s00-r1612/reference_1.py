n = int(input())
arr = map(int, input().split())
li = [0] * (n + 1)
for i in arr:
	li[i] = li[i - 1] + 1
print(n - max(li))
