n = int(input())
for i in range(n):
	(n, m, x1, y1, x2, y2) = map(int, input().split())
	if x1 <= x2 and y1 <= y2:
		pass
	elif x1 >= x2 and y1 >= y2:
		(x1, y1, x2, y2) = (x2, y2, x1, y1)
	else:
		(x1, y1, x2, y2) = (x2, y1, x1, y2)
	if x1 <= x2 and y1 <= y2:
		pass
	elif x1 >= x2 and y1 >= y2:
		(x1, y1, x2, y2) = (x2, y2, x1, y1)
	print(n * m - ((n - (x2 - x1)) * (m - (y2 - y1)) * 2 - max(0, (n - (x2 - x1)) * 2 - n) * max(0, (m - (y2 - y1)) * 2 - m)))
