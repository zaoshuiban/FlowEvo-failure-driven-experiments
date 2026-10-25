n = int(input())
start = [1, 2]
for _ in range(31):
	(e1, e2) = (start[-2], start[-1])
	if e1 % 2 == 0:
		start.append(2 * e1 + 1)
	elif e2 % 2 == 0:
		start.append(2 * e2 + 1)
	start.append(e1 + e2 + 1)
	if start[-1] < start[-2]:
		(start[-2], start[-1]) = (start[-1], start[-2])
if n in start:
	print(1)
else:
	print(0)
