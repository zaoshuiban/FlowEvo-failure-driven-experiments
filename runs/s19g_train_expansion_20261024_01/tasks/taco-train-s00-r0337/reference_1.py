n = int(input())
a = list(map(int, input().split()))
if n == 1:
	print(a[0])
else:
	(p, e) = (0, 0)
	for i in range(n):
		if a[i] >= 0:
			p = p + 1
		else:
			e = e + 1
	if p > 0 and e > 0:
		ans = 0
		for i in range(n):
			ans = ans + abs(a[i])
		print(ans)
	else:
		d = -2 * 10 ** 9
		ans = abs(a[0])
		for i in range(1, n):
			ans = ans + abs(a[i])
			if d < abs(a[i] - a[i - 1]) - (abs(a[i]) + abs(a[i - 1])):
				d = abs(a[i] - a[i - 1]) - (abs(a[i]) + abs(a[i - 1]))
		ans = ans + d
		print(ans)
