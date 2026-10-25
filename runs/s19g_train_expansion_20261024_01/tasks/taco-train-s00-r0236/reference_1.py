n = int(input())
a = list(map(int, input().split()))
t = [0] * (max(a) + 1)
for (i, v) in enumerate(a):
	t[v] += v
for i in range(3, len(t)):
	t[i] += max(t[i - 2], t[i - 3])
print(max(t))
